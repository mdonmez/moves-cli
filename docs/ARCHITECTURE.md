# Architecture Overview

This document explains how `moves` is structured and how its core components work together.

## High-Level Flow

```
User Input (Speaker Profile)
        ↓
    [Preparation Phase]
        ├─ Document Extraction → Identify slide boundaries (PDF, DOCX, PPTX, TXT, etc.)
        ├─ Transcript Analysis → Segment by sections
        ├─ LLM Processing → Generate speech labels (optional)
        └─ Output: sections.md
        ↓
    [Presentation Phase]
        ├─ Audio Input → Microphone stream
        ├─ VAD → Voice Activity Detection (filter silence)
        ├─ STT → Speech-to-Text (offline ONNX model)
        ├─ Similarity Matching → Find matching section
        └─ Output: Auto-navigation + UI feedback
```

## Core Components

### 1. Speaker Manager (`speaker_manager.py`)

**Responsibility**: Manage speaker profiles and their lifecycle.

**Key Methods**:
- `add()` – Create a new speaker profile from presentation and transcript files
- `edit()` – Update speaker's source files (re-hash if changed)
- `list()` – Get all registered speakers
- `resolve()` – Find speaker by name or ID
- `process()` – Main preparation pipeline (called by `speaker prepare`)
- `delete()` – Remove a speaker and their data

**File Hashing**:
Uses XXH3-64 hashing to detect file changes:
- `presentation_hash` – Hash of source presentation file at last processing
- `transcript_hash` – Hash of transcript at last processing
- `sections_hash` – Hash of normalized sections.md at last control session

This allows the tool to warn users if their source materials have changed since last preparation.

### 2. Presentation Controller (`presentation_controller.py`)

**Responsibility**: Real-time audio processing and slide navigation during presentation.

**Key Components**:
- **State Machine**: Manages three states
  - `ACTIVE` – Listening, auto-navigation enabled
  - `PAUSED` – Microphone paused, keyboard still works
  - `LOCKED` – Listening but navigation disabled
- **Audio Pipeline**:
  - Microphone stream (via `sounddevice`)
  - Voice Activity Detector (VAD) – filters silence
  - Speech-to-Text (STT) – offline ONNX model (Sherpa-ONNX)
- **Similarity Matching** – Finds best matching section
- **UI Dashboard** – Rich-powered terminal UI showing:
  - Current slide / total slides
  - Similarity scores (semantic + phonetic)
  - Recognized speech
  - System state (listening, paused, locked)
- **Keyboard Control**:
  - `←` / `→` – Previous / Next
  - `M` – Toggle pause/resume
  - `Q` – Exit

**Thread Model**:
- Main thread: UI rendering + keyboard listener
- Audio thread: Continuous microphone + VAD + STT
- Queues: Thread-safe communication between audio and main threads

### 3. Similarity Calculator (`similarity_calculator.py`)

**Responsibility**: Match recognized speech to sections using a hybrid approach.

**Algorithm**:
1. **Semantic Similarity** – Uses embeddings (FastEmbed, all-MiniLM-L6-v2)
2. **Phonetic Similarity** – Uses fuzzy matching (JellyFish, RapidFuzz)
3. **Score Merging** – Weighted combination (60% semantic, 40% phonetic by default)

**Key Features**:
- Normalizes scores across both engines
- Applies fairness factors to balance scoring
- Tie-breaking: prefers candidates closer to current position (forward bias)
- Configurable weights in `config.py` (`SEMANTIC_WEIGHT`, `PHONETIC_WEIGHT`)

**Threshold**:
Slide advances when similarity score ≥ `SIMILARITY_THRESHOLD` (default: 0.7)

### 4. Section & Chunk System

**Section** (`models.py`):
- Represents a single slide/section
- Contains: `content` (speech text), `section_index` (slide number)
- Immutable (frozen dataclass)

**Chunk**:
- Sliding window of words across sections
- Represents a snippet of speech that might appear in live input
- Used for matching (more granular than full section)

**Chunk Producer** (`chunk_producer.py`):
- Generates all chunks from sections using a sliding window
- Window size: `WINDOW_SIZE` (default: 12 words)
- Each chunk tracks which sections it spans

**Section Producer** (`section_producer.py`):
- Parses markdown format (sections.md) into Section objects
- Handles markdown-to-plain-text conversion
- Extracts text from multiple document formats using **100% free libraries**:
  - **PDF** - PyMuPDF4LLM (LLM-optimized markdown extraction)
  - **DOCX** - python-docx (Microsoft Word)
  - **PPTX** - python-pptx (PowerPoint)
  - **TXT** - Native text file support
  - No commercial licenses (PyMuPDF Pro) required
  - Automatic format detection based on file extension

### 5. Settings Editor (`settings_editor.py`)

**Responsibility**: Manage user configuration.

**Configuration**:
- `model` – LLM model name (stored in `settings.toml`)
- `format` – LLM API format (`chat`, `responses`, `auto`) (stored in `settings.toml`)
- `base_url` – Optional LLM base URL (used when set) (stored in `settings.toml`)
- `key` – API key (stored in Windows Credential Manager via keyring)

**Supported LLMs** (via LiteLLM):
- `gemini/*` – Google's Gemini models
- `gpt-*` – OpenAI models
- `claude-*` – Anthropic models
- Many others supported by LiteLLM

## Data Flow: Preparation Phase

```
┌─────────────────────────────────┐
│ Input: Presentation + Transcript│
└──────────────┬──────────────────┘
               ↓
        ┌──────────────────┐
        │ Document Extraction │ → Extract slide boundaries (multi-format)
        └──────────┬───────┘
                   ↓
        ┌──────────────────────┐
        │ Transcript Analysis  │ → Segment into sections
        │ (via Mistune parsing)│
        └──────────┬───────────┘
                   ↓
        ┌──────────────────────────────┐
        │ LLM Instruction Processing   │ (Auto mode)
        │ (via Instructor + LiteLLM)   │
        │                              │
        │ Generate speech labels for   │
        │ each slide based on content  │
        └──────────┬───────────────────┘
                   ↓
        ┌──────────────────────┐
        │ Markdown Generation  │ → Generate sections.md
        │ + Hashing            │ → Store file hash
        └──────────┬───────────┘
                   ↓
        ┌──────────────────────┐
        │ Output: sections.md  │
        └──────────────────────┘
```

## Data Flow: Presentation Phase

```
┌──────────────┐
│ Microphone   │ → Raw audio stream
└──────┬───────┘
       ↓
┌──────────────────────────────┐
│ Voice Activity Detector (VAD)│ → Filter silence, detect speech
│ (Sherpa-ONNX VAD model)      │    segments
└──────┬───────────────────────┘
       ↓
┌──────────────────────────────┐
│ Speech-to-Text (STT)         │ → Convert audio to text
│ (Sherpa-ONNX Zipformer)      │
└──────┬───────────────────────┘
       ↓
┌──────────────────────────────┐
│ Text Normalization           │ → Clean up speech text
│ (remove numbers→words, etc)  │
└──────┬───────────────────────┘
       ↓
┌──────────────────────────────┐
│ Similarity Calculator        │ → Generate candidate chunks
│ (Semantic + Phonetic)        │ → Score each chunk
│                              │ → Merge scores
└──────┬───────────────────────┘
       ↓
┌──────────────────────────────┐
│ Threshold Check              │ → If score ≥ 0.7:
│                              │    Advance to best match slide
└──────┬───────────────────────┘
       ↓
┌──────────────────────────────┐
│ UI Update                    │ → Show current slide
│ (Rich dashboard)             │ → Show similarity scores
│                              │ → Show recognized text
└──────────────────────────────┘
```

## File Organization

```
src/moves_cli/
├── cli.py                          # Main CLI entry point (Typer)
├── config.py                       # Configuration constants
├── models.py                       # Data models (Section, Chunk, Speaker, etc.)
│
├── core/
│   ├── presentation_controller.py  # Real-time audio + slide navigation
│   ├── speaker_manager.py          # Speaker profile management
│   ├── settings_editor.py          # Settings management (LLM, API key)
│   │
│   └── components/
│       ├── chunk_producer.py       # Generate chunks from sections
│       ├── section_producer.py     # Parse markdown into sections
│       ├── similarity_calculator.py # Similarity matching engine
│       │
│       └── similarity_units/
│           ├── semantic.py         # Semantic similarity (embeddings)
│           └── phonetic.py         # Phonetic similarity (fuzzy matching)
│
└── utils/
    ├── data_handler.py             # File I/O utilities
    ├── formatters.py               # Output formatting (Rich tables)
    ├── text_normalizer.py          # Text preprocessing
    ├── google_handler.py           # Google Drive integration
    ├── model_preparer.py           # Download/prepare ONNX models
    ├── id_generator.py             # Generate speaker IDs
    └── calculate_hash.py           # Hashing utilities
```

## Configuration Parameters

Key settings in `config.py`:

```python
# Similarity tuning
SEMANTIC_WEIGHT = 0.6              # Semantic vs phonetic balance
PHONETIC_WEIGHT = 0.4
SIMILARITY_THRESHOLD = 0.7         # Min score to auto-advance

# Chunk generation
WINDOW_SIZE = 12                   # Words per chunk
CANDIDATE_RANGE_MIN_OFFSET = -3    # Search range around current slide
CANDIDATE_RANGE_MAX_OFFSET = 5

# VAD (Voice Activity Detection)
VAD_THRESHOLD = 0.35               # Lower = more sensitive to speech
VAD_MIN_SILENCE = 0.5              # Seconds of silence to end segment
VAD_MIN_SPEECH = 0.1               # Minimum speech duration

# Storage
DATA_FOLDER = ~/.moves             # User data directory
SECTIONS_FILENAME = "sections.md"
SPEAKER_FILENAME = "speaker.yaml"
```

## Model Dependencies

The tool uses several pre-trained models:

| Model | Size | Purpose |
|-------|------|---------|
| **Sherpa-ONNX Nemo Zipformer** | ~130MB | Speech-to-Text (offline) |
| **Sherpa-ONNX VAD** | ~2MB | Voice Activity Detection |
| **all-MiniLM-L6-v2 (Quant)** | ~90MB | Semantic similarity embeddings |

Total: ~400-500MB for all models (downloaded on first use).

## Error Handling

Key error scenarios:

1. **Missing speaker** – User tries to use non-existent speaker
   - Resolved by `speaker_manager.resolve()` which provides helpful suggestions

2. **Stale sections.md** – Source files modified since preparation
   - Detected via hash comparison
   - User prompted to re-prepare or continue

3. **Microphone failure** – Audio stream unable to start
   - Graceful error message suggesting to check system audio settings

4. **Model download failure** – ONNX model download interrupted
   - Retry mechanism in `model_preparer.py`

5. **LLM API errors** – During preparation phase
   - Caught and reported with context
   - User can retry or use `--manual` mode

## Thread Safety

The presentation controller uses queues for thread-safe communication:
- `Queue` from `queue` module
- Audio processing thread → Main UI thread
- Non-blocking puts with timeout handling

## Performance Considerations

1. **First run** – Model downloads (~5-10 minutes depending on connection)
2. **Preparation** – LLM calls scale with presentation size (~30-60 seconds typical)
3. **Presentation** – Audio processing: ~32ms per window (responsive)
4. **Memory** – ~200-300MB when running (models + audio buffers)

## Extension Points

To extend `moves`, consider these areas:

1. **New similarity algorithms** – Add files in `similarity_units/`
2. **New model providers** – Extend `model_preparer.py`
3. **Alternative UI** – Replace Rich dashboard with custom UI
4. **New audio sources** – Extend `presentation_controller.py` audio stream handling
5. **Batch processing** – Add parallelization to speaker preparation

---

For more details, see [CLI Reference](CLI_REFERENCE.md) and [Configuration Guide](CONFIGURATION.md).
