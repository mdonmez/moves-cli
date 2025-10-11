from functools import lru_cache
from rapidfuzz import fuzz
from jellyfish import metaphone

from moves_cli.data.models import SimilarityResult, Chunk


class Phonetic:
    @staticmethod
    @lru_cache(maxsize=350)
    def _get_phonetic_code(text: str) -> str:
        return metaphone(text).replace(" ", "")

    @staticmethod
    @lru_cache(maxsize=350)
    def _calculate_fuzz_ratio(code1: str, code2: str) -> float:
        return fuzz.ratio(code1, code2) / 100.0

    def compare(
        self, input_str: str, candidates: list[Chunk]
    ) -> list[SimilarityResult]:
        try:
            input_code = self._get_phonetic_code(input_str)
            results = []
            for candidate in candidates:
                candidate_code = self._get_phonetic_code(candidate.partial_content)
                score = self._calculate_fuzz_ratio(input_code, candidate_code)
                results.append(SimilarityResult(chunk=candidate, score=score))

            results.sort(key=lambda x: x.score, reverse=True)
            return results

        except Exception as e:
            raise RuntimeError(f"Phonetic similarity comparison failed: {e}") from e
