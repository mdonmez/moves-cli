import re
import secrets
from unidecode import unidecode

from moves_cli.data.models import SpeakerId


def generate_speaker_id(name: str) -> SpeakerId:
    ascii_name = unidecode(name)

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
    suffix = "".join(secrets.choice(alphabet) for _ in range(5))
    speaker_id = f"{slug}-{suffix}"
    return speaker_id
