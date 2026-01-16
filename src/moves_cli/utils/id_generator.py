import re
from unidecode import unidecode

from moves_cli.config import CHUNK_ID_LENGTH, ID_BATCH_SIZE, SPEAKER_ID_SUFFIX_LENGTH
import os


class IDEngine:
    _buffer = []
    _batch_size = ID_BATCH_SIZE

    @classmethod
    def _refill(cls):
        raw = os.urandom(cls._batch_size * (CHUNK_ID_LENGTH // 2)).hex()
        cls._buffer = [
            raw[i : i + CHUNK_ID_LENGTH] for i in range(0, len(raw), CHUNK_ID_LENGTH)
        ]

    @classmethod
    def get_id(cls, length=CHUNK_ID_LENGTH):
        if not cls._buffer:
            cls._refill()
        return cls._buffer.pop()[:length]


SLUG_CLEANER = re.compile(r"[^\w\s-]")
SLUG_SPACES = re.compile(r"\s+")


def generate_chunk_id() -> str:
    return IDEngine.get_id(CHUNK_ID_LENGTH)


def generate_speaker_id(name: str) -> str:
    ascii_name = unidecode(name).lower()

    slug = SLUG_CLEANER.sub("", ascii_name)
    slug = SLUG_SPACES.sub("-", slug).strip("-")

    suffix = IDEngine.get_id(SPEAKER_ID_SUFFIX_LENGTH)

    return f"{slug}-{suffix}"
