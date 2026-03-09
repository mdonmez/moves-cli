# AGENTS.md - moves-cli

Guidance for coding agents working in this repository.
Derived from current repo state in `src/moves_cli`.

## Project Snapshot

- Python CLI app (`moves`) for voice-controlled slide navigation.
- Python requirement: `>=3.13`.
- Package/build tooling: `uv` + `uv_build`.
- Console script entry: `moves = moves_cli.cli:app`.
- Core libraries in use:
  - **CLI/UX**: `typer`, `rich`
  - **Data**: `ruamel.yaml`, `tomlkit`, `pydantic`, `xxhash`
  - **Text processing**: `mistune`, `num2words`, `unidecode`
  - **Similarity**: `fastembed`, `jellyfish`, `rapidfuzz`, `numpy`
  - **LLM integration**: `litellm`, `instructor[litellm]`
  - **Document parsing**: `pymupdf`, `pymupdf4llm`, `python-docx`, `python-pptx`
  - **Speech**: `sherpa-onnx`, `sherpa-onnx-core`, `sounddevice`
  - **OS integration**: `pynput`, `keyring`
  - **Network**: `httpx`

## High-Signal Layout

- `src/moves_cli/cli.py`: Typer command tree and top-level UX.
- `src/moves_cli/core/speaker_manager.py`: speaker CRUD, processing pipeline, xxhash checksums.
- `src/moves_cli/core/presentation_controller.py`: live STT/VAD control loop, Rich dashboard.
- `src/moves_cli/core/settings_editor.py`: settings CRUD (TOML file + system keyring for API key).
- `src/moves_cli/core/components/chunk_producer.py`: sliding-window chunk generation from sections.
- `src/moves_cli/core/components/section_producer.py`: document extraction (PDF/DOCX/PPTX), LLM-assisted section generation via `instructor` + `litellm`.
- `src/moves_cli/core/components/similarity_calculator.py`: combined semantic+phonetic scoring with tie-breaking.
- `src/moves_cli/core/components/similarity_units/semantic.py`: fastembed cosine similarity (all-MiniLM-L6-v2, weight 0.6).
- `src/moves_cli/core/components/similarity_units/phonetic.py`: jellyfish metaphone + rapidfuzz ratio (weight 0.4).
- `src/moves_cli/models.py`: dataclasses/enums and ML model metadata (`EmbeddingModel`, `SttModel`, `VadModel`, `Section`, `Chunk`, `Speaker`, `SimilarityResult`, `Settings`, `ProcessResult`).
- `src/moves_cli/config.py`: global constants/defaults (`SIMILARITY_THRESHOLD=0.7`, `WINDOW_SIZE=12`, `SEMANTIC_WEIGHT=0.6`, `PHONETIC_WEIGHT=0.4`, VAD params).
- `src/moves_cli/utils/data_handler.py`: file I/O abstraction rooted at `~/.moves/`.
- `src/moves_cli/utils/formatters.py`: Rich output formatter (`output()`), markdown-to-plain-text renderer.
- `src/moves_cli/utils/google_handler.py`: Google Drive/Docs/Slides URL detection, ID extraction, and file download.
- `src/moves_cli/utils/id_generator.py`: speaker ID slug generation (`name-xxxxx`) and random chunk ID generation.
- `src/moves_cli/utils/model_preparer.py`: async ONNX model download with xxhash verification and progress display.
- `src/moves_cli/utils/text_normalizer.py`: Unicode normalization, diacritics removal, emoji stripping, num2words conversion.
- `src/moves_cli/utils/calculate_hash.py`: standalone dev utility for computing xxh3_64 hashes of model files.
- `src/moves_cli/data/llm_instruction.md`: LLM system prompt for section generation.
- `src/moves_cli/data/ml_models/*`: bundled ONNX model files (embedding + STT + VAD).
- `docs/*`: architecture and contributor documentation.
- `experiments/*`: ad-hoc scripts (not formal tests).

## Setup Commands

Use `uv` tooling only.

```powershell
uv sync
uv pip install -e .
```

If local tooling is missing:

```powershell
uv add -d ruff pytest
```

## Build / Lint / Test Commands

### Build

```powershell
uv build
```

### Lint and Format

```powershell
uv run ruff check src
uv run ruff check src --fix
uv run ruff format src
```

### Tests

There is no committed `tests/` directory yet. Use these patterns when tests exist:

```powershell
uv run pytest
uv run pytest tests/test_file.py
uv run pytest tests/test_file.py::test_name
uv run pytest tests/test_file.py::TestClass::test_name
uv run pytest -k "keyword"
uv run pytest -x -q
```

Single-test guidance (important):

- Single file: `uv run pytest tests/test_similarity.py`
- Single function: `uv run pytest tests/test_similarity.py::test_exact_match`
- Single class method: `uv run pytest tests/test_similarity.py::TestCalc::test_exact_match`

Current runnable validation scripts:

```powershell
uv run experiments/test_renderer_results.py
uv run experiments/test_mistune_renderer.py
```

## Quick CLI Smoke Checks

```powershell
moves --version
moves --help
moves speaker list
moves settings list
```

## Domain Knowledge

### CLI Command Tree

| Command                                   | Description                                            |
| ----------------------------------------- | ------------------------------------------------------ |
| `moves speaker add <name> <pres> <trans>` | Create speaker profile                                 |
| `moves speaker edit <speaker>`            | Update source files (`--presentation`, `--transcript`) |
| `moves speaker list`                      | List all speakers and status                           |
| `moves speaker show <speaker>`            | Show detailed speaker info                             |
| `moves speaker prepare <speaker>`         | Generate sections (`--manual`, `--all`, `--yes`)       |
| `moves speaker delete <speaker>`          | Delete speaker(s) (`--all`, `--yes`)                   |
| `moves present <speaker>`                 | Start live voice presentation                          |
| `moves settings list`                     | Show config (`--show` reveals full API key)            |
| `moves settings set model <model>`        | Set LLM model                                          |
| `moves settings set key`                  | Set API key (interactive, hidden input)                |
| `moves settings unset <key>`              | Reset to default                                       |

### Supported File Formats

- **Presentation**: PDF (via `pymupdf4llm`), DOCX (via `python-docx`), PPTX (via `python-pptx`)
- **Transcript**: PDF, DOCX
- **Google Drive / Google Docs / Google Slides**: public URLs auto-downloaded by `google_handler.py`

### ML Models (bundled in `data/ml_models/`; also auto-downloaded on first run)

| Role                     | Model                               | Library       |
| ------------------------ | ----------------------------------- | ------------- |
| Voice Activity Detection | silero-vad-int8 (~208 KB)           | `sherpa-onnx` |
| Speech-to-Text           | NeMo streaming conformer 480ms int8 | `sherpa-onnx` |
| Semantic Embeddings      | all-MiniLM-L6-v2 quint8 avx2        | `fastembed`   |

Model file integrity is verified via xxh3_64 checksums in `models.py` on every `present` run. Do **not** modify those checksums unless model files are recalculated.

### Settings Storage

- `~/.moves/settings.toml`: LLM model name (plain TOML).
- API key: **system keyring only** (`keyring` library → Windows Credential Manager). Never written to disk. `moves settings set key` always uses interactive hidden input; passing a value as CLI argument is blocked on purpose.

## Code Style Guidelines

### Imports

- Group imports as stdlib, third-party, local.
- Keep imports explicit (no wildcard imports).
- Prefer top-level imports; use lazy imports only for heavy deps/startup/cycle concerns (pattern already used in `cli.py`).

### Formatting

- Use Ruff formatting as source of truth.
- Split long calls/collections for readability.
- Keep helper functions small and composable.

### Typing

- Annotate parameters and return values.
- Prefer built-in generics: `list[str]`, `dict[str, int]`, `tuple[int, ...]`.
- Prefer modern unions: `str | None`.
- Existing code still has some `typing.Optional`; do not add new `Optional` unless staying local to untouched legacy code.

### Naming

- `snake_case`: functions/variables/modules.
- `PascalCase`: classes.
- `UPPER_SNAKE_CASE`: constants.
- Prefix private helpers with `_`.

### Data Models

- Dataclasses are primary model style (`models.py`).
- Use `frozen=True` when immutability is required.
- Use `StrEnum` for string enums.

### Paths and IO

- Use `pathlib.Path` for filesystem paths.
- Route app file operations through `DataHandler` when practical.
- Use UTF-8 explicitly for text reads/writes.

### Error Handling

- Raise specific exceptions with actionable messages.
- Preserve original exceptions with `raise ... from e` when wrapping.
- In CLI handlers, display user-facing errors and exit with `typer.Exit(1)`.
- Re-raise `typer.Exit`; handle `typer.Abort` deliberately.

### Output and UX

- Prefer `typer.echo(output(...))` for user-visible messages.
- Keep error messages concise and include the next step when possible.
- Use `err=True` for error-path output.

### Async / Concurrency

- Prefer `asyncio` for orchestration.
- Use `asyncio.to_thread` for blocking operations.
- Keep signal/cancellation behavior consistent with existing `SpeakerManager.process` flow.

## Testing Guidance for New Work

- Add tests under `tests/` with `test_*.py` naming.
- Mirror source layout where helpful.
- Prioritize tests around speaker resolution, data handling edge cases, and similarity scoring.
- For bug fixes, add a regression test before or with the code change.

## Domain-Specific Cautions

- Do not edit model checksum constants in `src/moves_cli/models.py` unless model files actually changed and hashes were recalculated.
- Preserve `speaker.yaml` compatibility when changing `Speaker` dataclass fields.
- Keep offline/manual (`--manual`) workflows intact when changing preparation logic.
- `moves settings set key` must **never** accept a plain CLI argument value — the interactive `getpass` prompt is intentional for security.
- `calculate_hash.py` is a development utility (not a CLI subcommand of `moves`); do not wire it into the main app.
- `NormalizationMode.LIVE` skips `num2words` for speed during live STT processing; `PREPROCESS` uses full normalization during preparation. Keep this distinction.

## Cursor/Copilot Rules Check

Searched for:

- `.cursor/rules/`
- `.cursorrules`
- `.github/copilot-instructions.md`

None are present in this repository right now.
If added later, merge their directives into this file and treat them as authoritative.

## Recommended Agent Workflow

1. Read `pyproject.toml`, `README.md`, and relevant `docs/*.md` first.
2. Make focused changes in `src/moves_cli/*`.
3. Run lint/format on changed code.
4. Run the narrowest test target possible (single test when available).
5. If coverage is missing for changed behavior, add tests.
6. Run a quick CLI smoke check for touched command paths.
