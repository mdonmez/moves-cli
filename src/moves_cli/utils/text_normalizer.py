import re
import unicodedata

from num2words import num2words

RE_DIACRITICS = re.compile(r"[\u0300-\u036f]")

RE_EMOJI = re.compile(
    r"[\U0001f600-\U0001f64f\U0001f300-\U0001f5ff\U0001f680-\U0001f6ff"
    r"\U0001f1e0-\U0001f1ff\U00002702-\U000027b0\U000024c2-\U0001f251]+",
    flags=re.UNICODE,
)

RE_DIGITS = re.compile(r"\d+")

RE_SPECIAL_CHARS = re.compile(r"[^\w\s'\"`]", flags=re.UNICODE)

RE_WHITESPACE = re.compile(r"\s+")

QUOTE_TRANS_TABLE = str.maketrans(
    {
        "‘": "'",
        "’": "'",
        "‚": "'",
        "‛": "'",
        "“": " ",
        "”": " ",
        "„": " ",
        "‟": " ",
        '"': " ",
    }
)


def normalize_text(text: str) -> str:
    if not text:
        return ""

    text = unicodedata.normalize("NFD", text.lower())

    text = RE_DIACRITICS.sub("", text)

    text = RE_EMOJI.sub("", text)

    text = text.translate(QUOTE_TRANS_TABLE)

    if RE_DIGITS.search(text):
        text = RE_DIGITS.sub(lambda m: num2words(m.group(0)).replace("-", " "), text)

    text = RE_SPECIAL_CHARS.sub(" ", text)

    return RE_WHITESPACE.sub(" ", text).strip()
