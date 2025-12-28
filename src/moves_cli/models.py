from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from moves_cli.config import DATA_FOLDER, SECTIONS_FILENAME, SPEAKER_FILENAME


class NormalizationMode(StrEnum):
    """Text normalization mode for different use cases."""

    LIVE = "live"  # Fast path: skip num2words (STT outputs words)
    PREPROCESS = "preprocess"  # Full normalization with num2words


@dataclass(frozen=True)
class Section:
    content: str
    section_index: int


@dataclass(frozen=True)
class Chunk:
    partial_content: str
    source_sections: tuple[
        Section, ...
    ]  # Tuple ensures true immutability (frozen=True only prevents reassignment), this is why we use tuple instead of list
    chunk_id: str


@dataclass
class Speaker:
    name: str
    speaker_id: str
    source_presentation: Path
    source_transcript: Path
    last_processed: str | None = None

    @property
    def label(self) -> str:
        return f"{self.name} ({self.speaker_id})"

    @property
    def data_dir(self) -> Path:
        """Speaker veri dizini."""
        return DATA_FOLDER / "speakers" / self.speaker_id

    @property
    def sections_file(self) -> Path:
        """Sections dosyası yolu."""
        return self.data_dir / SECTIONS_FILENAME

    @property
    def speaker_file(self) -> Path:
        """Speaker metadata dosyası yolu."""
        return self.data_dir / SPEAKER_FILENAME


@dataclass(frozen=True)
class SimilarityResult:
    chunk: Chunk
    score: float


@dataclass
class Settings:
    model: str
    key: str


@dataclass(frozen=True)
class ProcessResult:
    section_count: int
    speaker_id: str
    processing_time_seconds: float


@dataclass(frozen=True)
class MlModel:
    name: str
    base_url: str
    files: dict[str, str]  # filename -> checksum
    model_dir: Path


EmbeddingModel = MlModel(
    name="sentence-transformers/all-MiniLM-l6-v2",
    base_url="https://github.com/mdonmez/moves-cli/raw/refs/heads/master/src/moves_cli/data/ml_models/all-MiniLM-L6-v2_quint8_avx2",
    files={
        "model.onnx": "e0def985059c9db8",
        "config.json": "ef5a8e793fd9b2f9",
        "special_tokens_map.json": "93a083cd86fe86e1",
        "tokenizer.json": "9a86f184b2242391",
        "tokenizer_config.json": "829f09aa4433a19d",
    },
    model_dir=DATA_FOLDER / "ml_models" / "all-MiniLM-L6-v2_quint8_avx2",
)

SttModel = MlModel(
    name="sherpa-onnx-nemo-streaming-fast-conformer-transducer-en-480ms",
    base_url="https://github.com/mdonmez/moves-cli/raw/refs/heads/master/src/moves_cli/data/ml_models/nemo-streaming-stt-480ms-int8",
    files={
        "decoder.int8.onnx": "f2751a7feca481bc",
        "encoder.int8.onnx": "bebeb28d3df4dfae",
        "joiner.int8.onnx": "84a3ae887bf7b986",
        "tokens.txt": "14f59574d9b3e62f",
    },
    model_dir=DATA_FOLDER / "ml_models" / "nemo-streaming-stt-480ms-int8",
)
