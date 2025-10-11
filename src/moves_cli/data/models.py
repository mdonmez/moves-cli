from dataclasses import dataclass
from typing import Literal
from pathlib import Path


SpeakerId = str
HistoryId = str


@dataclass(frozen=True)
class Section:
    content: str
    section_index: int


@dataclass(frozen=True)
class Chunk:
    partial_content: str
    source_sections: list["Section"]


@dataclass
class Speaker:
    name: str
    speaker_id: SpeakerId
    source_presentation: Path
    source_transcript: Path


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
    transcript_from: Literal["SOURCE", "LOCAL"]
    presentation_from: Literal["SOURCE", "LOCAL"]
