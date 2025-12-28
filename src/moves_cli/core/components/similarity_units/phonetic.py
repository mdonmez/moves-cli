from jellyfish import metaphone
from rapidfuzz import fuzz, process

from moves_cli.models import Chunk, SimilarityResult


class Phonetic:
    def __init__(self, all_chunks: list[Chunk]) -> None:
        # we're using this calculation at init to make o(1) lookups possible with dictionary instead of
        # doing it every time, that's huge performance boost
        self._phonetic_codes: dict[str, str] = {
            chunk.chunk_id: metaphone(chunk.partial_content).replace(" ", "")
            for chunk in all_chunks
        }

    def compare(
        self, input_str: str, candidates: list[Chunk]
    ) -> list[SimilarityResult]:
        if not candidates:
            return []

        try:
            input_code = metaphone(input_str).replace(" ", "")

            choices = [self._phonetic_codes.get(c.chunk_id, "") for c in candidates]

            raw_results = process.extract(
                query=input_code,
                choices=choices,
                scorer=fuzz.ratio,
                limit=None,
                processor=None,
            )

            # return with x.y format instead of 0-100
            return [
                SimilarityResult(chunk=candidates[index], score=score / 100.0)
                for _, score, index in raw_results
            ]

        except Exception as e:
            raise RuntimeError(f"Phonetic similarity comparison failed: {e}") from e
