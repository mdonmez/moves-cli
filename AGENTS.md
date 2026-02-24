# AGENTS.md - moves-cli

Guidance for coding agents working in this repository.
Derived from current repo state in `src/moves_cli`.

## Project Snapshot
- Python CLI app (`moves`) for voice-controlled slide navigation.
- Python requirement: `>=3.13`.
- Package/build tooling: `uv` + `uv_build`.
- Console script entry: `moves = moves_cli.cli:app`.
- Core libraries in use: `typer`, `rich`, `xxhash`, `ruamel.yaml`, `httpx`, `fastembed`, `litellm`, `pydantic`, `sherpa-onnx`.

## High-Signal Layout
- `src/moves_cli/cli.py`: Typer command tree and top-level UX.
- `src/moves_cli/core/speaker_manager.py`: speaker CRUD, processing, hashes.
- `src/moves_cli/core/presentation_controller.py`: live control loop.
- `src/moves_cli/core/settings_editor.py`: settings operations.
- `src/moves_cli/core/components/*`: section/chunk/similarity logic.
- `src/moves_cli/models.py`: dataclasses/enums and model metadata.
- `src/moves_cli/config.py`: global constants/defaults.
- `src/moves_cli/utils/*`: data handling, formatting, text normalization, integrations.
- `src/moves_cli/data/*`: prompt/model assets.
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
- Preserve `speaker.yaml` compatibility when changing speaker metadata fields.
- Keep offline/manual (`--manual`) workflows intact when changing preparation logic.

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
