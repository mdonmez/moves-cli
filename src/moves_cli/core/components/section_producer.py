import instructor
from importlib.resources import files
from litellm import completion
import pymupdf
from pathlib import Path
from pydantic import BaseModel, Field
from typing import Literal, cast

from moves_cli.data.models import Section


def _extract_pdf(
    pdf_path: Path, extraction_type: Literal["transcript", "presentation"]
) -> str:
    try:
        with pymupdf.open(pdf_path) as doc:
            match extraction_type:
                case "transcript":
                    full_text = "".join(page.get_text("text") for page in doc)  # type: ignore
                    result = " ".join(full_text.split())

                    return result
                case "presentation":
                    markdown_sections = []
                    slide_count = 0
                    for i, page in enumerate(doc):  # type: ignore
                        page_text = page.get_text("text")
                        cleaned_text = " ".join(page_text.split())
                        markdown_sections.append(f"# Slide Page {i}\n{cleaned_text}")
                        slide_count += 1

                    return "\n\n".join(markdown_sections)
    except Exception as e:
        raise RuntimeError(
            f"PDF extraction failed for {pdf_path} ({extraction_type}): {e}"
        ) from e


def _call_llm(
    presentation_data: str, transcript_data: str, llm_model: str, llm_api_key: str
) -> list[str]:
    class SectionsOutputModel(BaseModel):
        class SectionItem(BaseModel):
            section_index: int = Field(..., ge=0, description="Index starting from 0")
            content: str = Field(..., description="Content of the section")

        sections: list[SectionItem] = Field(  # type: ignore
            ...,
            description="List of section items, one for each slide",
            min_items=len(presentation_data.split("\n\n")),
            max_items=len(presentation_data.split("\n\n")),
        )

    try:
        system_prompt = (
            files("moves_cli.data").joinpath("llm_instruction.md").read_text()
        )
        client = instructor.from_litellm(completion, mode=instructor.Mode.JSON)

        response = client.chat.completions.create(
            model=llm_model,
            api_key=llm_api_key,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"Presentation: {presentation_data}\nTranscript: {transcript_data}",
                },
            ],
            response_model=SectionsOutputModel,
            temperature=0.2,
        )
        result = [item.content for item in response.sections]
        return result
    except Exception as e:
        raise RuntimeError(f"LLM call failed: {e}") from e


def convert_to_list(section_objects: list[Section]) -> list[dict[str, str | int]]:
    return [
        {"content": s.content, "section_index": s.section_index}
        for s in section_objects
    ]


def convert_to_objects(section_list: list[dict[str, str | int]]) -> list[Section]:
    return [
        Section(
            content=cast(str, s_dict["content"]),
            section_index=cast(int, s_dict["section_index"]),
        )
        for s_dict in section_list
    ]


def generate_sections(
    presentation_path: Path, transcript_path: Path, llm_model: str, llm_api_key: str
) -> list[Section]:
    presentation_data = _extract_pdf(presentation_path, "presentation")
    transcript_data = _extract_pdf(transcript_path, "transcript")

    section_contents = _call_llm(
        presentation_data=presentation_data,
        transcript_data=transcript_data,
        llm_model=llm_model,
        llm_api_key=llm_api_key,
    )

    generated_sections: list[Section] = []

    for idx, content in enumerate(section_contents):
        section = Section(
            content=content,
            section_index=idx,
        )
        generated_sections.append(section)

    return generated_sections
