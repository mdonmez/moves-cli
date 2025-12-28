from collections import defaultdict
from collections.abc import Callable

from moves_cli.config import CANDIDATE_RANGE_MAX_OFFSET, CANDIDATE_RANGE_MIN_OFFSET
from moves_cli.models import Chunk, NormalizationMode, Section
from moves_cli.utils import text_normalizer
from moves_cli.utils.id_generator import generate_chunk_id


def generate_chunks(
    sections: list[Section],
    window_size: int,
    chunk_id_generator: Callable[[], str] = generate_chunk_id,
) -> list[Chunk]:
    if window_size < 1:
        return []

    # map one by one
    words_with_sources = [
        (word, section) for section in sections for word in section.content.split()
    ]

    n_words = len(words_with_sources)
    if n_words < window_size:
        return []

    chunks = []

    range_limit = n_words - window_size + 1

    # create chunks with window size of words with window sliding
    for i in range(range_limit):
        window = words_with_sources[i : i + window_size]

        words = [w for w, _ in window]

        sections_dict = {s.section_index: s for _, s in window}

        joined_text = " ".join(words)

        chunks.append(
            Chunk(
                partial_content=text_normalizer.normalize_text(
                    joined_text, mode=NormalizationMode.PREPROCESS
                ),
                source_sections=tuple(
                    sorted(sections_dict.values(), key=lambda s: s.section_index)
                ),
                # give it id to access it easily
                chunk_id=chunk_id_generator(),
            )
        )

    return chunks


class CandidateChunkGenerator:
    def __init__(self, all_chunks: list[Chunk]):
        self._index: dict[int, list[Chunk]] = defaultdict(list)

        # create index for candidate chunks at init for performance
        for chunk in all_chunks:
            if not chunk.source_sections:
                continue

            min_sec_idx = chunk.source_sections[0].section_index
            max_sec_idx = chunk.source_sections[-1].section_index

            start_candidate_range = max_sec_idx + CANDIDATE_RANGE_MIN_OFFSET
            end_candidate_range = min_sec_idx + CANDIDATE_RANGE_MAX_OFFSET

            is_single_section = len(chunk.source_sections) == 1
            single_source_idx = min_sec_idx if is_single_section else -1

            # selects the chunks that are in the candidate range with not selecting the exact sides
            for idx in range(start_candidate_range, end_candidate_range + 1):
                if is_single_section:
                    if (
                        single_source_idx == idx - CANDIDATE_RANGE_MAX_OFFSET
                        or single_source_idx == idx - CANDIDATE_RANGE_MIN_OFFSET
                    ):
                        continue

                self._index[idx].append(chunk)

    def get_candidate_chunks(self, current_section: Section) -> list[Chunk]:
        return self._index.get(current_section.section_index, [])
