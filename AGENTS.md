# AGENTS.md

Practical guidance for AI coding agents working in `moves-cli`.

## 1) Mission and Status

- `moves-cli` is a Python CLI that auto-navigates slides from live speech.
- Project status: maintenance-oriented; avoid broad feature churn unless explicitly requested.
- Source of truth is code under `src/moves_cli/` (docs can lag).

## 2) Environment and Tooling

- Python: `>=3.13`.
- Package manager/build: `uv` + `uv_build`.
- Entry point: `moves = moves_cli.cli:app`.
- Typical commands:

```powershell
uv sync
uv run ruff check src
uv run moves --help
uv build
```

## 3) High-Signal File Map

- `src/moves_cli/cli.py`: Typer command tree (`speaker`, `settings`, `present`).
- `src/moves_cli/core/speaker_manager.py`: speaker CRUD + prepare pipeline + hash checks.
- `src/moves_cli/core/presentation_controller.py`: live STT/VAD loop, keyboard controls, Rich TUI.
- `src/moves_cli/core/settings_editor.py`: settings TOML + keyring API key handling.
- `src/moves_cli/core/components/section_producer.py`: document extraction + LLM section generation + markdown parsing.
- `src/moves_cli/core/components/chunk_producer.py`: sliding-window chunk generation + candidate indexing.
- `src/moves_cli/core/components/similarity_calculator.py`: semantic + phonetic score merge and ranking.
- `src/moves_cli/core/components/similarity_units/semantic.py`: FastEmbed cosine similarity.
- `src/moves_cli/core/components/similarity_units/phonetic.py`: metaphone + RapidFuzz similarity.
- `src/moves_cli/models.py`: dataclasses/enums + ML model metadata/checksums.
- `src/moves_cli/config.py`: global constants/defaults.
- `src/moves_cli/utils/*`: formatting, IO, Google URL resolution, model downloads, normalization, IDs.
- `src/moves_cli/data/llm_instruction.md`: system prompt used in section generation.

## 4) Runtime Behavior (Must Preserve)

- Two phases:
  - Prepare (`moves speaker prepare`): create/update `sections.md`.
  - Present (`moves present`): live recognition + similarity + navigation.
- Keyboard controls are standardized:
  - `M` = pause/resume
  - `←/→` = manual navigation
  - `Q` = quit
- Data root is `~/.moves`:
  - `settings.toml`
  - `speakers/<speaker-id>/speaker.yaml`
  - `speakers/<speaker-id>/sections.md`

## 5) Contracts and Invariants

- API key security:
  - API key must stay in system keyring (not plaintext files).
  - `moves settings set key` is interactive-only by design.
- Sections markdown contract:
  - Canonical heading: `# N. Slide`.
  - Parser also accepts legacy `# Slide N`.
- Similarity defaults (from `config.py`):
  - `SEMANTIC_WEIGHT=0.6`, `PHONETIC_WEIGHT=0.4`, `SIMILARITY_THRESHOLD=0.7`.
- Model integrity:
  - `EmbeddingModel`, `SttModel`, `VadModel` file hashes in `models.py` are critical.
  - Do not alter checksums unless model artifacts and hashes are intentionally updated.
- Speaker metadata compatibility:
  - Preserve `speaker.yaml` fields unless a migration is intentionally introduced.

## 6) Dependency Constraints You Should Know

- Current Windows compatibility requires:
  - `sherpa-onnx>=1.12.23,<1.12.37`
  - `sherpa-onnx-core>=1.12.23,<1.12.37`
- Reason: newer versions may lack compatible Windows wheels and force failing source builds.
- If asked to upgrade deps, validate `uv lock --upgrade && uv sync` on Windows before finalizing.

## 7) Editing Guidelines

- Keep changes minimal and targeted.
- Prefer preserving existing architecture and flow.
- Use type hints in modern style (`str | None`, `list[T]`, `dict[K, V]`).
- Preserve user-facing CLI wording consistency across:
  - `cli.py`
  - `README.md`
  - `docs/CLI_REFERENCE.md`
  - `docs/GETTING_STARTED.md`
  - `docs/ARCHITECTURE.md`
- Avoid introducing new runtime dependencies unless requested.

## 8) Verification Checklist After Code Changes

- Always run:

```powershell
uv run ruff check src
```

- For CLI-affecting changes, also run smoke checks:

```powershell
uv run moves --version
uv run moves --help
uv run moves speaker --help
uv run moves settings --help
```

- For dependency changes:

```powershell
uv lock --upgrade
uv sync
```

## 9) Current Testing Reality

- There is no committed `tests/` suite in the repository right now.
- Do not claim broad behavior guarantees from automated tests.
- When fixing bugs, prefer adding targeted tests if/when test infra is introduced.

## 10) Common Footguns

- `pynput` sends key presses to the currently focused window; focus loss can break navigation.
- Some docs/examples may mention older shortcuts or stale details; reconcile with source code.
- `utils/calculate_hash.py` is a standalone utility, not a `moves` subcommand.

## 11) Recommended Agent Workflow

1. Read `pyproject.toml`, `README.md`, and the touched source files.
2. Implement the smallest safe change.
3. Update docs if user-facing behavior changed.
4. Run lint + relevant smoke commands.
5. Report exactly what changed, where, and what was verified.
