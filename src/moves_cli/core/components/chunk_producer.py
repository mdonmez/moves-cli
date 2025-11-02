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


class CandidateChunkGenerator:
    def __init__(self, all_chunks: list[Chunk]):
        self._index: dict[int, list[Chunk]] = {}

        for chunk in all_chunks:
            if not chunk.source_sections:
                continue

            min_sec_idx = min(s.section_index for s in chunk.source_sections)
            max_sec_idx = max(s.section_index for s in chunk.source_sections)

            start_candidate_range = max_sec_idx - 3
            end_candidate_range = min_sec_idx + 2

            for idx in range(start_candidate_range, end_candidate_range + 1):
                if len(chunk.source_sections) == 1:
                    source_idx = chunk.source_sections[0].section_index
                    if source_idx == idx - 2 or source_idx == idx + 3:
                        continue

                if idx not in self._index:
                    self._index[idx] = []
                self._index[idx].append(chunk)

    def get_candidate_chunks(self, current_section: Section) -> list[Chunk]:
        return self._index.get(current_section.section_index, [])
