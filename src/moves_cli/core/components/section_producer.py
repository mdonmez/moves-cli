from importlib.resources import files
from pathlib import Path
from typing import Callable, Literal

import instructor
import pymupdf
from litellm import completion
from pydantic import BaseModel, Field

from moves_cli.models import Section


class SectionProducer:
    def _extract_pdf(
        self, pdf_path: Path, extraction_type: Literal["transcript", "presentation"]
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
                            markdown_sections.append(
                                f"# Slide Page {i + 1}\n{cleaned_text}"
                            )
                            slide_count += 1

                        return "\n\n".join(markdown_sections)
        except Exception as e:
            raise RuntimeError(
                f"PDF extraction failed for {pdf_path} ({extraction_type}): {e}"
            ) from e

    def _call_llm(
        self,
        presentation_data: str,
        transcript_data: str,
        llm_model: str,
        llm_api_key: str,
    ) -> list[str]:
        slide_count = len(presentation_data.split("\n\n"))

        class SectionsOutputModel(BaseModel):
            class SectionItem(BaseModel):
                section_index: int = Field(
                    ..., ge=1, description="Index starting from 1"
                )
                content: str = Field(..., description="Content of the section")

            sections: list[SectionItem] = Field(  # type: ignore
                ...,
                description="List of section items, one for each slide",
                min_items=slide_count,
                max_items=slide_count,
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

    def convert_to_yaml(self, sections: list[Section]) -> str:
        """Section listesini YAML formatına dönüştür (folded block scalar)."""
        from io import StringIO

        from ruamel.yaml import YAML
        from ruamel.yaml.comments import CommentedSeq
        from ruamel.yaml.scalarstring import FoldedScalarString

        def to_folded(content: str) -> str | FoldedScalarString:
            """Boş değilse FoldedScalarString, boşsa düz string döner."""
            if not content or not content.strip():
                return ""
            text = content if content.endswith("\n") else content + "\n"
            return FoldedScalarString(text)

        yaml_data = CommentedSeq()
        for idx, section in enumerate(sections):
            yaml_data.append(
                {
                    "section_index": section.section_index,
                    "content": to_folded(section.content),
                }
            )
            if idx > 0:
                yaml_data.yaml_set_comment_before_after_key(idx, before="\n")

        yaml = YAML()
        yaml.default_flow_style = False
        yaml.width = 80

        output = StringIO()
        yaml.dump(yaml_data, output)
        return output.getvalue()

    def load_from_yaml(self, yaml_content: str) -> list[Section]:
        """YAML içeriğinden Section listesi oluştur."""
        from io import StringIO

        from ruamel.yaml import YAML

        yaml = YAML()
        data = yaml.load(StringIO(yaml_content))

        return [
            Section(
                content=str(item["content"]),
                section_index=int(item["section_index"]),
            )
            for item in data
        ]

    def generate_sections(
        self,
        presentation_path: Path,
        transcript_path: Path,
        llm_model: str,
        llm_api_key: str,
        callback: Callable[[str], None] | None = None,
    ) -> list[Section]:
        if callback:
            callback("Extracting presentation data...")
        presentation_data = self._extract_pdf(presentation_path, "presentation")

        if callback:
            callback("Extracting transcript data...")
        transcript_data = self._extract_pdf(transcript_path, "transcript")

        if callback:
            callback("Calling LLM...")
        section_contents = self._call_llm(
            presentation_data=presentation_data,
            transcript_data=transcript_data,
            llm_model=llm_model,
            llm_api_key=llm_api_key,
        )

        generated_sections: list[Section] = []

        for idx, content in enumerate(section_contents):
            section = Section(
                content=content,
                section_index=idx + 1,
            )
            generated_sections.append(section)

        return generated_sections
