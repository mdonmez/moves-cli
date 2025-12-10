from pathlib import Path

# General configuration constants
DATA_FOLDER: Path = Path.home() / ".moves"

# Similarity calculator configuration
SEMANTIC_WEIGHT: float = 0.6
PHONETIC_WEIGHT: float = 0.4
SIMILARITY_THRESHOLD: float = 0.7

# Engine configuration
WINDOW_SIZE: int = 12
CANDIDATE_RANGE_MIN_OFFSET: int = -3
CANDIDATE_RANGE_MAX_OFFSET: int = 2

# Default settings (used by SettingsEditor)
DEFAULT_LLM_MODEL: str = "gemini/gemini-2.5-flash-lite"
DEFAULT_API_KEY: str | None = None
