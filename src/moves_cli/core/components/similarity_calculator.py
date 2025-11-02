from moves_cli.core.components.similarity_units.phonetic import Phonetic
from moves_cli.core.components.similarity_units.semantic import Semantic

from moves_cli.data.models import Chunk, SimilarityResult


class SimilarityCalculator:
    def __init__(
        self,
        all_chunks: list[Chunk],
        semantic_weight: float = 0.6,
        phonetic_weight: float = 0.4,
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

            max_p = max(phonetic_scores.values())
            max_s = max(semantic_scores.values())

            batch_quality = (self.phonetic_weight * max_p) + (
                self.semantic_weight * max_s
            )

            final_results = []
            for candidate in candidates:
                cid = id(candidate)
                norm_p = phonetic_scores[cid] / max_p
                norm_s = semantic_scores[cid] / max_s
                relative = (self.phonetic_weight * norm_p) + (
                    self.semantic_weight * norm_s
                )
                weighted_score = relative * batch_quality

                final_results.append(
                    SimilarityResult(chunk=candidate, score=weighted_score)
                )

            final_results.sort(key=lambda x: x.score, reverse=True)

            return final_results

        except Exception as e:
            raise RuntimeError(f"Similarity comparison failed: {e}") from e
