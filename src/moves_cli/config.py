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

# VAD configuration (tuned for office/home environments, adjust for large venues)
VAD_THRESHOLD: float = 0.35  # Lower = more sensitive to speech (0.1-0.9)
VAD_MIN_SILENCE: float = 0.5  # Seconds of silence to end speech segment
VAD_MIN_SPEECH: float = 0.1  # Minimum speech duration to detect
VAD_WINDOW_SIZE: int = 512  # ~32ms analysis window at 16kHz
VAD_BUFFER_SIZE: float = 30.0  # Circular buffer size in seconds
