import re
import secrets

from fastnanoid import generate
from unidecode import unidecode

from moves_cli.config import SPEAKER_ID_SUFFIX_LENGTH


def generate_chunk_id() -> str:
    return generate()


def generate_speaker_id(name: str) -> str:
    ascii_name = unidecode(name)

    # slugify
    slug = (
        re.sub(
            r"\s+",
            "-",
            re.sub(r"[^\w\s-]", "", ascii_name),
        )
        .strip("-")
        .lower()
    )

    alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    suffix = "".join(secrets.choice(alphabet) for _ in range(SPEAKER_ID_SUFFIX_LENGTH))
    speaker_id = f"{slug}-{suffix}"
    return speaker_id
