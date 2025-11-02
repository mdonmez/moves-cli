from moves_cli.utils import text_normalizer
from moves_cli.data.models import Section, Chunk


def generate_chunks(sections: list[Section], window_size: int) -> list[Chunk]:
    if window_size < 1:
        return []

    words_with_sources = [
        (word, section) for section in sections for word in section.content.split()
    ]
    if len(words_with_sources) < window_size:
        return []

    chunks = []
    for i in range(len(words_with_sources) - window_size + 1):
        window = words_with_sources[i : i + window_size]
        words = [w for w, _ in window]
        sections_dict = {s.section_index: s for _, s in window}
        chunks.append(
            Chunk(
                partial_content=text_normalizer.normalize_text(" ".join(words)),
                source_sections=list(sections_dict.values()),
            )
        )

    return chunks


def get_candidate_chunks(
    current_section: Section, all_chunks: list[Chunk]
) -> list[Chunk]:
    idx = current_section.section_index
    start, end = idx - 2, idx + 3

    return [
        chunk
        for chunk in all_chunks
        if len(chunk.source_sections) != 1
        or chunk.source_sections[0].section_index not in (start, end)
        if all(start <= s.section_index <= end for s in chunk.source_sections)
    ]
