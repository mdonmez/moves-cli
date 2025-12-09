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
        self, input_str: str, candidates: list[Chunk]
    ) -> list[SimilarityResult]:
        if not candidates:
            return []

        try:
            semantic_results = self.semantic.compare(input_str, candidates)
            phonetic_results = self.phonetic.compare(input_str, candidates)

            phonetic_scores = {id(res.chunk): res.score for res in phonetic_results}
            semantic_scores = {id(res.chunk): res.score for res in semantic_results}

            max_p = max(phonetic_scores.values()) if phonetic_scores else 1.0
            max_s = max(semantic_scores.values()) if semantic_scores else 1.0

            if max_p == 0:
                max_p = 1.0
            if max_s == 0:
                max_s = 1.0

            batch_quality = (self.phonetic_weight * max_p) + (
                self.semantic_weight * max_s
            )

            factor_p = (self.phonetic_weight * batch_quality) / max_p
            factor_s = (self.semantic_weight * batch_quality) / max_s

            final_results = [
                SimilarityResult(
                    chunk=candidate,
                    score=(
                        phonetic_scores.get(id(candidate), 0.0) * factor_p
                        + semantic_scores.get(id(candidate), 0.0) * factor_s
                    ),
                )
                for candidate in candidates
            ]

            final_results.sort(key=lambda x: x.score, reverse=True)

            return final_results

        except Exception as e:
            raise RuntimeError(f"Similarity comparison failed: {e}") from e
