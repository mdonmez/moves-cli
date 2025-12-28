import numpy as np

from moves_cli.models import Chunk, EmbeddingModel, SimilarityResult


class Semantic:
    def __init__(self, all_chunks: list[Chunk]) -> None:
        from fastembed import TextEmbedding

        self._embeddings: dict[str, np.ndarray] = {}

        self._model = TextEmbedding(
            model_name=EmbeddingModel.name,
            # the specific model path, for using the model at the ml models dir to avoid
            # auto-download with bad ui. also with this way i can use int8 faster model
            specific_model_path=EmbeddingModel.model_dir,
        )

        # do all chunk embeddings at once for performance
        if all_chunks:
            chunk_contents = [chunk.partial_content for chunk in all_chunks]

            chunk_embeddings = list(self._model.embed(chunk_contents))

            for chunk, embedding in zip(all_chunks, chunk_embeddings):
                norm = np.linalg.norm(embedding) or 1.0
                self._embeddings[chunk.chunk_id] = embedding / norm

    def compare(
        self, input_str: str, candidates: list[Chunk]
    ) -> list[SimilarityResult]:
        if not candidates:
            return []

        try:
            input_embedding = next(iter(self._model.embed([input_str])))
            input_embedding = input_embedding / (np.linalg.norm(input_embedding) or 1.0)

            candidate_matrix = np.array(
                [self._embeddings[c.chunk_id] for c in candidates], dtype=np.float32
            )

            scores = candidate_matrix @ input_embedding

            sorted_indices = np.argsort(scores)[::-1]

            return [
                SimilarityResult(chunk=candidates[i], score=float(scores[i]))
                for i in sorted_indices
            ]

        except Exception as e:
            raise RuntimeError(f"Semantic similarity comparison failed: {e}") from e
