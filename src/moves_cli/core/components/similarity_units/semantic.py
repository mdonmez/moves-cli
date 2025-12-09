import numpy as np

from moves_cli.models import Chunk, EmbeddingModel, SimilarityResult


class Semantic:
    def __init__(self, all_chunks: list[Chunk]) -> None:
        from fastembed import TextEmbedding

        self._embeddings: dict[int, np.ndarray] = {}

        self._model = TextEmbedding(
            model_name=EmbeddingModel.name,
            specific_model_path=EmbeddingModel.model_dir,
        )

        if all_chunks:
            chunk_contents = [chunk.partial_content for chunk in all_chunks]

            chunk_embeddings = list(self._model.embed(chunk_contents))

            for chunk, embedding in zip(all_chunks, chunk_embeddings):
                self._embeddings[id(chunk)] = embedding

    def compare(
        self, input_str: str, candidates: list[Chunk]
    ) -> list[SimilarityResult]:
        if not candidates:
            return []

        try:
            input_embedding = next(iter(self._model.embed([input_str])))

            candidate_matrix = np.array(
                [self._embeddings[id(c)] for c in candidates], dtype=np.float32
            )

            scores = candidate_matrix @ input_embedding

            sorted_indices = np.argsort(scores)[::-1]

            return [
                SimilarityResult(chunk=candidates[i], score=float(scores[i]))
                for i in sorted_indices
            ]

        except Exception as e:
            raise RuntimeError(f"Semantic similarity comparison failed: {e}") from e
