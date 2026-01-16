from pathlib import Path

# General configuration constants
DATA_FOLDER: Path = Path.home() / ".moves"
SECTIONS_FILENAME: str = "sections.md"
SPEAKER_FILENAME: str = "speaker.yaml"

# ID generation
SPEAKER_ID_SUFFIX_LENGTH: int = 5
SPEAKER_ID_GENERATION_MAX_RETRIES: int = 3
ID_BATCH_SIZE: int = 1000
CHUNK_ID_LENGTH: int = 16

# Similarity calculator configuration
SEMANTIC_WEIGHT: float = 0.6
PHONETIC_WEIGHT: float = 0.4
SIMILARITY_THRESHOLD: float = 0.7

# Engine configuration
WINDOW_SIZE: int = 12
CANDIDATE_RANGE_MIN_OFFSET: int = -3
CANDIDATE_RANGE_MAX_OFFSET: int = 5

# Default settings (used by SettingsEditor)
DEFAULT_LLM_MODEL: str = "gemini/gemini-2.5-flash-lite"  # gemini, nearly everyone have google account and gemini api is free
DEFAULT_API_KEY: str = ""
