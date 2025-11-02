import numpy as np
from pathlib import Path

from moves_cli.utils import data_handler
from moves_cli.data.models import SimilarityResult, Chunk


class Semantic:
    def __init__(self, all_chunks: list[Chunk]) -> None:
        from fastembed import TextEmbedding

        self._embeddings: dict[int, np.ndarray] = {}

        self._model_path = (
            Path(data_handler.DATA_FOLDER)
            / "ml_models"
            / "all-MiniLM-L6-v2_quint8_avx2"
        )

        self._model = TextEmbedding(
            model_name="sentence-transformers/all-MiniLM-l6-v2",
            specific_model_path=self._model_path,
        )

        if all_chunks:
            chunk_contents = [chunk.partial_content for chunk in all_chunks]
            chunk_embeddings = list(self._model.embed(chunk_contents))

            for chunk, embedding in zip(all_chunks, chunk_embeddings):
                self._embeddings[id(chunk)] = embedding

    def compare(
        self, input_str: str, candidates: list[Chunk]
    ) -> list[SimilarityResult]:
        try:
            input_embedding = list(self._model.embed([input_str]))[0]

            candidate_embeddings = [
                self._embeddings[id(candidate)] for candidate in candidates
            ]

            cosine_scores = np.dot(candidate_embeddings, input_embedding)

            results = [
                SimilarityResult(chunk=candidate, score=float(score))
                for candidate, score in zip(candidates, cosine_scores)
            ]
            results.sort(key=lambda x: x.score, reverse=True)
            return results

        except Exception as e:
            raise RuntimeError(f"Semantic similarity comparison failed: {e}") from e
