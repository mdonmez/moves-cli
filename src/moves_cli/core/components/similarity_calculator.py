from moves_cli.config import PHONETIC_WEIGHT, SEMANTIC_WEIGHT
from moves_cli.core.components.similarity_units.phonetic import Phonetic
from moves_cli.core.components.similarity_units.semantic import Semantic
from moves_cli.models import Chunk, SimilarityResult


class SimilarityCalculator:
    def __init__(
        self,
        all_chunks: list[Chunk],
        semantic_weight: float = SEMANTIC_WEIGHT,
        phonetic_weight: float = PHONETIC_WEIGHT,
    ):
        self.semantic_weight = semantic_weight
        self.phonetic_weight = phonetic_weight
        self.semantic = Semantic(all_chunks)
        self.phonetic = Phonetic(all_chunks)

    def compare(
        self,
        input_str: str,
        candidates: list[Chunk],
        current_section_index: int = 0,  # we're getting index for tie breaking
    ) -> list[SimilarityResult]:
        if not candidates:
            return []

        try:
            # the score merging logic, it is a bit complex but it works well.
            # really balances the unfairness of phonetic and semantic scores
            semantic_results = self.semantic.compare(input_str, candidates)
            phonetic_results = self.phonetic.compare(input_str, candidates)

            phonetic_scores = {
                res.chunk.chunk_id: res.score for res in phonetic_results
            }
            semantic_scores = {
                res.chunk.chunk_id: res.score for res in semantic_results
            }

            max_p = max(phonetic_scores.values(), default=0.0) or 1.0
            max_s = max(semantic_scores.values(), default=0.0) or 1.0

            batch_quality = (self.phonetic_weight * max_p) + (
                self.semantic_weight * max_s
            )

            factor_p = (self.phonetic_weight * batch_quality) / max_p
            factor_s = (self.semantic_weight * batch_quality) / max_s

            final_results = []
            for candidate in candidates:
                raw_score = (
                    phonetic_scores.get(candidate.chunk_id, 0.0) * factor_p
                    + semantic_scores.get(candidate.chunk_id, 0.0) * factor_s
                )

                final_score = min(1.0, raw_score)

                final_results.append(
                    SimilarityResult(chunk=candidate, score=final_score)
                )

            # for tie breaking, prefer closest slide on right (forward direction)
            final_results.sort(
                key=lambda x: (
                    -x.score,
                    (0, d)
                    if (
                        d := max(s.section_index for s in x.chunk.source_sections)
                        - current_section_index
                    )
                    >= 0
                    else (1, -d),
                )
            )

            return final_results

        except Exception as e:
            raise RuntimeError(f"Similarity comparison failed: {e}") from e
