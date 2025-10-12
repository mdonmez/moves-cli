# moves-cli Development Guide

## Project Overview

`moves` is an offline, voice-controlled presentation system with a two-phase architecture:

1. **Offline Processing**: LLM-based transcript segmentation → overlapping chunk generation
2. **Real-time Control**: Streaming STT → hybrid similarity matching → keyboard automation

All data lives in `~/.moves/` sandbox managed by `data_handler` module.

## Architecture & Data Flow

### Core Components (`src/moves_cli/core/`)

- **SpeakerManager**: CRUD operations for speaker profiles in `~/.moves/speakers/<speaker_id>/`
  - Speaker resolution: accepts name or ID, handles ambiguous names
  - Each speaker has `speaker.json` (metadata) and `sections.json` (processed data)
- **SettingsEditor**: Manages `~/.moves/settings.toml` using `tomlkit`
  - Always merges with template (`src/moves_cli/data/settings_template.toml`) on init
  - Preserves comments and structure from template
- **PresentationController**: Multi-threaded real-time control engine
  - Audio thread: `sounddevice` → `deque` → `sherpa-onnx` streaming STT
  - Navigator thread: compares STT output against candidate chunks every 0.5s
  - Keyboard listener thread: manual override with pause/resume controls

### Data Pipeline Components (`src/moves_cli/core/components/`)

**Section Production** (`section_producer.py`):

- `PyMuPDF` extracts text from presentation/transcript PDFs
- `instructor` + `litellm` forces LLM output to match exact slide count via Pydantic validation
- System prompt from `src/moves_cli/data/llm_instruction.md` guides semantic alignment

**Chunk Production** (`chunk_producer.py`):

- Sliding window (default 12 words) over concatenated section text
- Each chunk tracks `source_sections` for mapping back to slides
- Normalized via `text_normalizer.normalize_text()` (lowercased, diacritics stripped, numbers→words)

**Similarity Calculation** (`similarity_calculator.py`):

- Hybrid scoring: 60% semantic (fastembed cosine) + 40% phonetic (Metaphone + rapidfuzz)
- Min-max normalization on scores ≥0.5 before weighted combination
- `get_candidate_chunks()` filters to window `[current_slide-2, current_slide+3]`
- Edge heuristic: excludes single-section chunks at window boundaries

## Critical Conventions

### Type Annotations

- Use built-in generics: `list[int]`, `dict[str, int]`, not `typing.List`/`typing.Dict`
- Use `|` for unions: `str | None`, not `typing.Optional` or `typing.Union`
- Only import from `typing` for advanced features: `Literal`, `cast`, `Protocol`

### Package Management (uv)

- **Always use `uv`**, never `pip` directly:
  - Add deps: `uv add <package>`
  - Run scripts: `uv run <script.py>`
  - Run tests: `uv run pytest`
  - Sync deps: `uv sync`

### Data Access Pattern

```python
from moves_cli.utils import data_handler

# All paths relative to ~/.moves/
data_handler.write(Path("speakers/abc123/sections.json"), json_data)
data_handler.read(Path("settings.toml"))
```

Never access filesystem directly—always through `data_handler` for sandbox security.

### Model Storage

Local ONNX models bundled at build time:

- STT: `src/moves_cli/core/components/ml_models/nemo-streaming-stt-480ms-int8/`
- Embeddings: `src/moves_cli/core/components/ml_models/all-MiniLM-L6-v2_quint8_avx2/`

Downloaded to `~/.moves/ml_models/` on first use via `model_downloader.download_model()`.

## Testing Strategy

### Mock System Dependencies

`conftest.py` mocks hardware-dependent modules for CI/CD:

```python
sys.modules["sounddevice"] = MagicMock()  # Audio capture
sys.modules["pynput"] = MagicMock()       # Keyboard control
```

### Test Organization (`tests/`)

- `test_components.py`: chunk/section production, similarity scoring
- `test_core.py`: SpeakerManager, SettingsEditor logic
- `test_utils.py`: data_handler, text_normalizer edge cases
- `test_cli.py`: Typer command validation

Run with: `uv run pytest` (never `pytest` alone)

## Common Workflows

### Adding a New Similarity Unit

1. Create `src/moves_cli/core/components/similarity_units/new_unit.py`
2. Implement `compare(input_str: str, candidates: list[Chunk]) -> list[SimilarityResult]`
3. Add to `SimilarityCalculator.__init__()` and update scoring weights
4. Add tests in `test_components.py::TestSimilarityCalculator`

### Debugging Real-time Control

- STT output is normalized before matching—use `text_normalizer.normalize_text()` on test phrases
- Check candidate chunk filtering: current slide ±2/+3 window may exclude expected matches
- Audio queue has `maxlen=5` (500ms buffer)—older frames drop silently

### Processing Speaker Data

```bash
# Full pipeline test
uv run python -c "
from moves_cli.core.speaker_manager import SpeakerManager
sm = SpeakerManager()
result = sm.process(['speaker_id'], model='gemini/gemini-2.5-flash-lite', key='YOUR_KEY')
"
```

## Key Files Reference

- **CLI entry**: `src/moves_cli/main.py` (Typer app structure)
- **Data models**: `src/moves_cli/data/models.py` (frozen dataclasses)
- **Normalization**: `src/moves_cli/utils/text_normalizer.py` (critical for STT→chunk matching)
- **Sandbox utilities**: `src/moves_cli/utils/data_handler.py` (all file operations)
- **Architecture docs**: `docs/architecture.md`, `docs/about/chunks.md`
