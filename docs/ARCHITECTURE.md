# Architecture Guide

Technical documentation of how `moves` is designed and how its components work together.

## Table of Contents

1. [High-Level Overview](#high-level-overview)
2. [Core Components](#core-components)
3. [Data Flow](#data-flow)
4. [File Organization](#file-organization)
5. [Configuration Parameters](#configuration-parameters)
6. [Model Dependencies](#model-dependencies)
7. [Threading Model](#threading-model)
8. [Extension Points](#extension-points)

---

## High-Level Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         PREPARATION PHASE                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Presentation File ──┬──▶ Document Extraction ──▶ Slide Content         │
│  (PDF/DOCX/PPTX/TXT) │    (PyMuPDF4LLM, etc.)                           │
│                      │                              ↓                    │
│  Transcript File ────┴──▶ Text Parsing ──────────▶ Raw Transcript       │
│                                                     ↓                    │
│                          LLM Processing ◀──────── Combined Input         │
│                          (LiteLLM + Instructor)                          │
│                               ↓                                          │
│                          sections.md ────▶ Speech content per slide      │
│                               ↓                                          │
│                          File Hashes ────▶ Change detection              │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                        PRESENTATION PHASE                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Microphone ──▶ Audio Stream ──▶ VAD Filter ──▶ Speech-to-Text          │
│  (sounddevice)                   (Silero)       (Sherpa-ONNX NeMo)      │
│                                                         ↓                │
│                                                 Text Normalization       │
│                                                 (num2words, unidecode)   │
│                                                         ↓                │
│                                                 Sliding Window Buffer    │
│                                                 (last N words)           │
│                                                         ↓                │
│  sections.md ──▶ Chunk Generation ──────────▶ Candidate Chunks          │
│                  (sliding window)                       ↓                │
│                                                                          │
│                       Similarity Calculator ◀──────────┘                 │
│                       ├─ Semantic (60%): all-MiniLM-L6-v2 embeddings    │
│                       └─ Phonetic (40%): Metaphone + RapidFuzz          │
│                               ↓                                          │
│                       Score ≥ 70%? ──Yes──▶ Auto-advance slide          │
│                               ↓                                          │
│                       Rich Terminal UI ──▶ Real-time dashboard          │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. Speaker Manager (`core/speaker_manager.py`)

**Responsibility:** Manage speaker profiles and their lifecycle.

**Key Methods:**
| Method | Description |
|--------|-------------|
| `add()` | Create new speaker from presentation + transcript |
| `edit()` | Update source files |
| `list()` | Get all registered speakers |
| `resolve()` | Find speaker by name or ID |
| `process()` | Run preparation pipeline |
| `delete()` | Remove speaker and data |

**File Hashing:**
Uses XXH3-64 for change detection:
- `presentation_hash` – Source presentation at last process
- `transcript_hash` – Source transcript at last process
- `sections_hash` – Normalized sections.md content

---

### 2. Presentation Controller (`core/presentation_controller.py`)

**Responsibility:** Real-time audio processing and slide navigation.

**State Machine:**
```
              ┌──────────────────┐
              │      ACTIVE      │ ◀─── Default state
              │   (listening)    │
              └────────┬─────────┘
                       │
        ┌──────────────┼──────────────┐
        │ Press M      │              │ Press ←/→
        ▼              │              ▼
┌───────────────┐      │      ┌───────────────┐
│    PAUSED     │      │      │    LOCKED     │
│  (mic muted)  │      │      │ (manual nav)  │
└───────────────┘      │      └───────────────┘
        │              │              │
        │ Press M      │              │ Speech matches
        └──────────────┴──────────────┘
                       ▼
                    ACTIVE
```

**Components:**
- **Audio Pipeline:** sounddevice → VAD → STT → Queue
- **Similarity Matching:** Compare speech to chunks
- **Keyboard Listener:** pynput for manual controls
- **Rich UI:** Terminal dashboard with live updates

---

### 3. Similarity Calculator (`core/components/similarity_calculator.py`)

**Responsibility:** Match speech to sections using hybrid algorithm.

**Algorithm:**
```python
# 1. Compute individual scores
semantic_scores = semantic.compare(input, candidates)  # Embeddings
phonetic_scores = phonetic.compare(input, candidates)  # Sound matching

# 2. Normalize scores
max_semantic = max(semantic_scores)
max_phonetic = max(phonetic_scores)

# 3. Apply fairness factor (balance batch quality)
batch_quality = (PHONETIC_WEIGHT * max_phonetic) + (SEMANTIC_WEIGHT * max_semantic)
factor_phonetic = (PHONETIC_WEIGHT * batch_quality) / max_phonetic
factor_semantic = (SEMANTIC_WEIGHT * batch_quality) / max_semantic

# 4. Merge scores
final_score = (phonetic * factor_phonetic) + (semantic * factor_semantic)

# 5. Tie-breaking: prefer forward direction (next slides)
```

**Similarity Units:**
| Unit | Library | Purpose |
|------|---------|---------|
| `Semantic` | FastEmbed (all-MiniLM-L6-v2) | Meaning-based matching |
| `Phonetic` | JellyFish (Metaphone) + RapidFuzz | Sound-based matching |

---

### 4. Section Producer (`core/components/section_producer.py`)

**Responsibility:** Parse documents and generate sections.

**Document Extraction:**
| Format | Library | Method |
|--------|---------|--------|
| PDF | PyMuPDF4LLM | `_extract_pdf()` |
| DOCX | python-docx | `_extract_docx()` |
| PPTX | python-pptx | `_extract_pptx()` |
| TXT | Native | `_extract_txt()` |

**LLM Integration:**
Uses Instructor + LiteLLM for structured output:
```python
class SectionsOutputModel(BaseModel):
    sections: list[SectionItem]  # Pydantic validation
```

**Markdown Format:**
```markdown
# 1. Slide

Speech content for slide 1...

# 2. Slide

Speech content for slide 2...
```

---

### 5. Chunk Producer (`core/components/chunk_producer.py`)

**Responsibility:** Generate sliding window chunks for matching.

**Algorithm:**
```
sections = [S1, S2, S3, ...]
words = flatten(section.content.split() for section in sections)

for i in range(len(words) - WINDOW_SIZE + 1):
    window = words[i : i + WINDOW_SIZE]
    chunk = Chunk(
        partial_content=normalize(join(window)),
        source_sections=unique_sections_in_window,
        chunk_id=generate_id()
    )
```

**Candidate Selection:**
`CandidateChunkGenerator` pre-indexes chunks by section for O(1) lookup:
- Range: `current_section + [-3, +5]` slides

---

### 6. Settings Editor (`core/settings_editor.py`)

**Responsibility:** Manage user configuration.

**Storage:**
| Setting | Location |
|---------|----------|
| `model` | `~/.moves/settings.toml` |
| `key` | System keyring (Windows Credential Manager, etc.) |

**Keyring Integration:**
```python
keyring.set_password("moves-cli", "api-key", value)
keyring.get_password("moves-cli", "api-key")
```

---

## Data Flow

### Preparation Phase

```
┌─────────────────────────────────────────────────────────────────┐
│ Input: Presentation + Transcript Files                          │
└─────────────────────────────┬───────────────────────────────────┘
                              ↓
                    ┌─────────────────────┐
                    │ Document Extraction │
                    │ • Detect format     │
                    │ • Extract content   │
                    │ • Count slides      │
                    └──────────┬──────────┘
                               ↓
                    ┌─────────────────────┐
                    │ Token Estimation    │ (Auto mode only)
                    │ • Count tokens      │
                    │ • Estimate cost     │
                    │ • Display prompt    │
                    └──────────┬──────────┘
                               ↓
              ┌────────────────┴────────────────┐
              ↓                                 ↓
    ┌─────────────────┐               ┌─────────────────┐
    │ LLM Processing  │               │ Manual Template │
    │ (Auto mode)     │               │ (--manual mode) │
    │ • Call LiteLLM  │               │ • Empty sections│
    │ • Parse output  │               │                 │
    └────────┬────────┘               └────────┬────────┘
             │                                  │
             └────────────────┬─────────────────┘
                              ↓
                    ┌─────────────────────┐
                    │ Write sections.md   │
                    │ • Markdown format   │
                    └──────────┬──────────┘
                               ↓
                    ┌─────────────────────┐
                    │ Update Metadata     │
                    │ • Compute hashes    │
                    │ • Save speaker.yaml │
                    └─────────────────────┘
```

### Presentation Phase

```
┌─────────────────────────────────────────────────────────────────┐
│ Input: Microphone Audio + sections.md                           │
└─────────────────────────────┬───────────────────────────────────┘
                              ↓
                    ┌─────────────────────┐
                    │ Model Loading       │
                    │ • STT model         │
                    │ • VAD model         │
                    │ • Embedding model   │
                    │ • Chunk generation  │
                    └──────────┬──────────┘
                               ↓
         ┌─────────────────────┴─────────────────────┐
         ↓                                           ↓
┌─────────────────┐                       ┌─────────────────────┐
│ Audio Thread    │                       │ Main Thread         │
│ • Sample 16kHz  │                       │ • Keyboard listener │
│ • VAD filter    │                       │ • UI rendering      │
│ • STT decode    │                       │ • State machine     │
│ • Queue words   │                       │                     │
└────────┬────────┘                       └──────────┬──────────┘
         │                                           │
         └───────────────┬───────────────────────────┘
                         ↓
               ┌─────────────────────┐
               │ Navigator Logic     │
               │ • Get candidate     │
               │   chunks            │
               │ • Calculate         │
               │   similarity        │
               │ • Check threshold   │
               │ • Navigate if match │
               └──────────┬──────────┘
                          ↓
               ┌─────────────────────┐
               │ UI Update           │
               │ • Show state        │
               │ • Show slide        │
               │ • Show speech       │
               │ • Show similarity   │
               └─────────────────────┘
```

---

## File Organization

```
src/moves_cli/
├── cli.py                          # Typer CLI entry point
├── config.py                       # Configuration constants
├── models.py                       # Data models (Section, Chunk, Speaker, etc.)
│
├── core/
│   ├── presentation_controller.py  # Real-time audio + navigation
│   ├── speaker_manager.py          # Speaker lifecycle management
│   ├── settings_editor.py          # Settings (model, API key)
│   │
│   └── components/
│       ├── chunk_producer.py       # Generate sliding window chunks
│       ├── section_producer.py     # Parse documents + LLM
│       ├── similarity_calculator.py # Hybrid matching engine
│       │
│       └── similarity_units/
│           ├── semantic.py         # Embedding-based similarity
│           └── phonetic.py         # Sound-based similarity
│
├── utils/
│   ├── data_handler.py             # File I/O operations
│   ├── formatters.py               # Output formatting (Rich)
│   ├── text_normalizer.py          # Text preprocessing
│   ├── google_handler.py           # Google Drive integration
│   ├── model_preparer.py           # Download ONNX models
│   ├── id_generator.py             # Generate speaker/chunk IDs
│   └── calculate_hash.py           # File hashing utilities
│
└── data/
    ├── llm_instruction.md          # LLM system prompt
    └── ml_models/                  # ONNX models (generated)
```

---

## Configuration Parameters

### Similarity Matching (`config.py`)

```python
SEMANTIC_WEIGHT = 0.6              # Semantic vs phonetic balance (0-1)
PHONETIC_WEIGHT = 0.4              # Must sum to 1.0 with semantic
SIMILARITY_THRESHOLD = 0.7         # Minimum score to auto-advance (0-1)
```

### Chunk Generation (`config.py`)

```python
WINDOW_SIZE = 12                   # Words per chunk
CANDIDATE_RANGE_MIN_OFFSET = -3    # Search N slides back
CANDIDATE_RANGE_MAX_OFFSET = 5     # Search N slides forward
```

### Voice Activity Detection (`config.py`)

```python
VAD_THRESHOLD = 0.35               # Speech detection sensitivity (0-1)
VAD_MIN_SILENCE = 0.5              # Seconds of silence to end segment
VAD_MIN_SPEECH = 0.1               # Minimum speech duration to detect
VAD_WINDOW_SIZE = 512              # ~32ms at 16kHz sample rate
VAD_BUFFER_SIZE = 30.0             # Circular buffer in seconds
```

### Storage (`config.py`)

```python
DATA_FOLDER = Path.home() / ".moves"
SECTIONS_FILENAME = "sections.md"
SPEAKER_FILENAME = "speaker.yaml"
```

### ID Generation (`config.py`)

```python
SPEAKER_ID_SUFFIX_LENGTH = 5       # Random suffix length
SPEAKER_ID_GENERATION_MAX_RETRIES = 3
CHUNK_ID_LENGTH = 16               # Chunk identifier length
```

---

## Model Dependencies

### ONNX Models

| Model | Size | Purpose | Library |
|-------|------|---------|---------|
| **NeMo Streaming Fast Conformer** | ~130MB | Speech-to-text | Sherpa-ONNX |
| **Silero VAD** | ~2MB | Voice activity detection | Sherpa-ONNX |
| **all-MiniLM-L6-v2 (Quant)** | ~90MB | Semantic embeddings | FastEmbed |

**Total:** ~500MB (downloaded on first use)

**Storage:** `~/.moves/ml_models/`

### Model Checksums

Models are verified using XXH3-64 checksums defined in `models.py`:
```python
EmbeddingModel = MlModel(
    name="sentence-transformers/all-MiniLM-l6-v2",
    files={
        "model.onnx": "cda38b71e6003d03",  # xxh3_64
        "config.json": "ef5a8e793fd9b2f9",
        ...
    }
)
```

---

## Threading Model

### Thread Structure

```
┌─────────────────────────────────────────────────────────────┐
│                       Main Thread                            │
│  • Typer CLI                                                 │
│  • Rich Live UI rendering                                    │
│  • Keyboard listener (pynput)                                │
│  • State machine transitions                                 │
│  • Shutdown coordination                                     │
└─────────────────────────────────────────────────────────────┘
         ↕ Queue (audio_queue, words_queue)
┌─────────────────────────────────────────────────────────────┐
│                   STT Processor Thread                       │
│  • Consume audio from queue                                  │
│  • Run speech recognition                                    │
│  • Normalize text                                            │
│  • Produce words to queue                                    │
└─────────────────────────────────────────────────────────────┘
         ↕ Queue (words_queue)
┌─────────────────────────────────────────────────────────────┐
│                    Navigator Thread                          │
│  • Consume words from queue                                  │
│  • Generate candidate chunks                                 │
│  • Calculate similarity                                      │
│  • Perform navigation (with echo suppression)                │
└─────────────────────────────────────────────────────────────┘
```

### Thread Safety

| Resource | Protection |
|----------|------------|
| `current_section` | `threading.Lock` |
| `_state` | `threading.Lock` |
| `_word_buffer` | `threading.Lock` |
| `audio_queue` | `queue.Queue` (thread-safe) |
| `words_queue` | `queue.Queue` (thread-safe) |
| `shutdown_flag` | `threading.Event` |
| `_vad_active` | `threading.Event` |
| `_echo_suppression` | `threading.Event` |

### Shutdown Sequence

1. `Ctrl+C` or `Q` sets `shutdown_flag`
2. Main thread exits Live context
3. Threads check flag and exit loops
4. `thread.join(timeout=2.0)` for cleanup

---

## Extension Points

### Adding a New Similarity Unit

1. Create `core/components/similarity_units/lexical.py`:
```python
class Lexical:
    def __init__(self, all_chunks: list[Chunk]):
        # Pre-compute indices
        pass
    
    def compare(self, input_str: str, candidates: list[Chunk]) -> list[SimilarityResult]:
        # Return scored results
        pass
```

2. Add to `SimilarityCalculator.__init__()`:
```python
self.lexical = Lexical(all_chunks)
```

3. Integrate into `compare()` scoring.

### Adding a New Document Format

1. Add extraction method in `section_producer.py`:
```python
def _extract_odt(self, file_path: Path, extraction_type: str) -> str:
    # LibreOffice ODT extraction
    pass
```

2. Add case to `_extract_document()`:
```python
case ".odt":
    return self._extract_odt(file_path, extraction_type)
```

### Customizing the UI

1. Modify Rich components in `presentation_controller.py`:
   - `_build_header()` – Top row
   - `_build_content()` – Main content
   - `_build_footer()` – Bottom row
   - `_build_frame()` – Panel wrapper

2. Update theme in `THEME = Theme({...})`

### Adding a New CLI Command

1. Add to `cli.py`:
```python
@app.command()
def export(
    speaker: str = typer.Argument(...),
    output: Path = typer.Option("output.md"),
):
    """Export speaker sections to file."""
    pass
```

---

For more details:
- [CLI Reference](CLI_REFERENCE.md) – All commands
- [Configuration](CONFIGURATION.md) – Tuning options
- [Development](DEVELOPMENT.md) – Contributing guide
