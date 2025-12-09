from jellyfish import metaphone
from rapidfuzz import fuzz, process

from moves_cli.models import Chunk, SimilarityResult


class Phonetic:
    def __init__(self, all_chunks: list[Chunk]) -> None:
        self._phonetic_codes: dict[int, str] = {
            id(chunk): metaphone(chunk.partial_content).replace(" ", "")
            for chunk in all_chunks
        }

    def compare(
        self, input_str: str, candidates: list[Chunk]
    ) -> list[SimilarityResult]:
        if not candidates:
            return []

        try:
            input_code = metaphone(input_str).replace(" ", "")

            choices = [self._phonetic_codes.get(id(c), "") for c in candidates]

            raw_results = process.extract(
                query=input_code,
                choices=choices,
                scorer=fuzz.ratio,
                limit=None,
                processor=None,
            )

            return [
                SimilarityResult(chunk=candidates[index], score=score / 100.0)
                for _, score, index in raw_results
            ]

        except Exception as e:
            raise RuntimeError(f"Phonetic similarity comparison failed: {e}") from e
