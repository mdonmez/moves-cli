import numpy as np
from pathlib import Path

from moves_cli.utils import data_handler
from moves_cli.data.models import SimilarityResult, Chunk


class Semantic:
    def __init__(self) -> None:
        self._model = None

        self._model_path = (
            Path(data_handler.DATA_FOLDER)
            / "ml_models"
            / "all-MiniLM-L6-v2_quint8_avx2"
        )

    @property
    def model(self):
        """Lazy load the TextEmbedding model only when first accessed."""
        if self._model is None:
            from fastembed import TextEmbedding

            self._model = TextEmbedding(
                model_name="sentence-transformers/all-MiniLM-l6-v2",
                specific_model_path=self._model_path,
            )
        return self._model

    def compare(
        self, input_str: str, candidates: list[Chunk]
    ) -> list[SimilarityResult]:
        try:
            embedding_input = [input_str] + [
                candidate.partial_content for candidate in candidates
            ]

            embeddings = list(self.model.embed(embedding_input))

            input_embedding = embeddings[0]
            candidate_embeddings = embeddings[1:]

            cosine_scores = np.dot(candidate_embeddings, input_embedding)

            results = [
                SimilarityResult(chunk=candidate, score=float(score))
                for candidate, score in zip(candidates, cosine_scores)
            ]
            results.sort(key=lambda x: x.score, reverse=True)
            return results

        except Exception as e:
            raise RuntimeError(f"Semantic similarity comparison failed: {e}") from e
