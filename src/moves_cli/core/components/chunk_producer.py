from moves_cli.utils import text_normalizer
from moves_cli.data.models import Section, Chunk


def generate_chunks(sections: list[Section], window_size: int = 12) -> list[Chunk]:
    words_with_sources = [
        (word, section) for section in sections for word in section.content.split()
    ]
    if len(words_with_sources) < window_size:
        return []

    return [
        Chunk(
            partial_content=text_normalizer.normalize_text(
                " ".join(word for word, _ in words_with_sources[i : i + window_size])
            ),
            source_sections=sorted(
                {section for _, section in words_with_sources[i : i + window_size]},
                key=lambda s: s.section_index,
            ),
        )
        for i in range(len(words_with_sources) - window_size + 1)
    ]


def get_candidate_chunks(
    current_section: Section, all_chunks: list[Chunk]
) -> list[Chunk]:
    idx = int(current_section.section_index)
    start, end = idx - 2, idx + 3

    return [
        chunk
        for chunk in all_chunks
        if all(start <= int(s.section_index) <= end for s in chunk.source_sections)
        and not (
            len(chunk.source_sections) == 1
            and int(chunk.source_sections[0].section_index) in (start, end)
        )
    ]
