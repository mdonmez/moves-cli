from collections import defaultdict

from moves_cli.models import Chunk, Section
from moves_cli.utils import text_normalizer


def generate_chunks(sections: list[Section], window_size: int) -> list[Chunk]:
    if window_size < 1:
        return []

    words_with_sources = [
        (word, section) for section in sections for word in section.content.split()
    ]

    n_words = len(words_with_sources)
    if n_words < window_size:
        return []

    chunks = []

    range_limit = n_words - window_size + 1

    for i in range(range_limit):
        window = words_with_sources[i : i + window_size]

        # Unpack separated lists
        words = [w for w, _ in window]

        sections_dict = {s.section_index: s for _, s in window}

        joined_text = " ".join(words)

        chunks.append(
            Chunk(
                partial_content=text_normalizer.normalize_text(joined_text),
                source_sections=list(sections_dict.values()),
            )
        )

    return chunks


class CandidateChunkGenerator:
    def __init__(self, all_chunks: list[Chunk]):
        self._index: dict[int, list[Chunk]] = defaultdict(list)

        for chunk in all_chunks:
            if not chunk.source_sections:
                continue

            min_sec_idx = chunk.source_sections[0].section_index
            max_sec_idx = chunk.source_sections[-1].section_index

            start_candidate_range = max_sec_idx - 3
            end_candidate_range = min_sec_idx + 2

            is_single_section = len(chunk.source_sections) == 1
            single_source_idx = min_sec_idx if is_single_section else -1

            for idx in range(start_candidate_range, end_candidate_range + 1):
                if is_single_section:
                    if single_source_idx == idx - 2 or single_source_idx == idx + 3:
                        continue

                self._index[idx].append(chunk)

    def get_candidate_chunks(self, current_section: Section) -> list[Chunk]:
        return self._index.get(current_section.section_index, [])
