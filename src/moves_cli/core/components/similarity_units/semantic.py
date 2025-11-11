import numpy as np

from moves_cli.data.models import Chunk, EmbeddingModel, SimilarityResult


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


if __name__ == "__main__":
    semantic = Semantic([])
    results = semantic.compare(
        "What is the capital of France?",
        [
            Chunk(
                partial_content="Paris is the capital of France.", source_sections=[]
            ),
            Chunk(
                partial_content="Berlin is the capital of Germany.", source_sections=[]
            ),
            Chunk(
                partial_content="Madrid is the capital of Spain.", source_sections=[]
            ),
        ],
    )
    for result in results:
        print(f"Score: {result.score:.4f}, Content: {result.chunk.partial_content}")
