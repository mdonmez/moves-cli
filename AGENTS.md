# AGENTS.md - Development Guide for moves-cli

## Project Overview

moves-cli is a presentation control system that uses offline speech recognition and a hybrid similarity engine to advance slides automatically based on speech. Built with Python 3.13+, typer CLI, Rich UI, and sherpa-onnx for STT.

## Build, Lint, and Test Commands

### Package Management

```bash
uv add <package>          # Add dependency
uv remove <package>           # Remove dependency
uv sync                          # Sync lockfile
```

### Running the Application

```bash
moves-cli <command>              # CLI entry point after installation
python -m moves_cli.cli          # Direct module execution
```

### Code Quality

```bash
uv run ruff check .              # Lint all files
uv run ruff check <file>         # Lint specific file
uv run ruff check --fix .        # Auto-fix linting issues

# Type checking (if added)
uv run pyright .                 # Type check project
uv run mypy .                    # Alternative: mypy type check
```

### Single File Execution

```bash
python src/moves_cli/cli.py      # Run CLI module directly
python -m src.moves_cli.cli      # Module execution
```

### Testing (if pytest is configured)

```bash
uv run pytest                    # Run all tests
uv run pytest tests/             # Run specific test directory
uv run pytest tests/test_file.py # Run single test file
uv run pytest -k "test_name"     # Run tests matching pattern
uv run pytest --tb=short         # Short traceback on failure
```

## Code Style Guidelines

### Imports

- Group imports in order: stdlib → third-party → local imports
- Use absolute imports: `from moves_cli.utils.data_handler import DataHandler`
- Separate import groups with a single blank line
- Local/lazy imports allowed for circular dependency resolution (see cli.py)

### Naming Conventions

```python
# Classes: PascalCase
class PresentationController:
class SectionProducer:

# Functions/variables: snake_case
def speaker_manager_instance():
def normalize_text():
similarity_calculator = ...

# Constants: UPPER_SNAKE_CASE
SAMPLE_RATE = 16000
WINDOW_SIZE = 3

# Type variables: PascalCase (when used)
Chunk: tuple[Section, ...]

# Private methods: underscore prefix
def _perform_navigation(self, target_section: Section) -> None:
```

### Type Hints

- Use Python 3.13+ type hints throughout
- Prefer explicit types over `Any`
- Use `| None` syntax over `Optional[]` (Python 3.10+)
- Use `str | None` for nullable return values
- Fully annotate function signatures including `-> None`
- Union types: `Path | None` not `Optional[Path]`

### Data Classes and Models

- Use `@dataclass` for simple data models
- Use `@dataclass(frozen=True)` for immutable types (Section, Chunk, SimilarityResult)
- Use `@dataclass(frozen=True, slots=True)` for memory-efficient frozen types (UIData)
- Use `StrEnum` for string-based enumerations
- Define model types at module level (EmbeddingModel, SttModel, VadModel)

### Error Handling

- Use specific exception types in `except` clauses
- Wrap CLI errors with `raise typer.Exit(code)` for typer commands
- Use `typer.Exit(1)` for errors, `typer.Exit(0)` for clean exit
- Handle `typer.Abort` for user-initiated cancellations
- Chain exceptions with `from e` for debugging: `raise ... from e`
- Pattern in CLI commands:
  ```python
  try:
      # operation
  except typer.Exit:
      raise
  except Exception as e:
      typer.echo(output(f"Error: {str(e)}"), err=True)
      raise typer.Exit(1)
  ```

### CLI Command Pattern

- Use `@app.command()` or `@subcommand.command()` decorators
- Use `typer.Argument()` for required positional args
- Use `typer.Option()` for optional flags
- Validate inputs early, fail fast with clear error messages
- Use `output()` formatter from `utils.formatters` for consistent output:
  ```python
  typer.echo(output(f"Message {value}", {"Key": "val"}), err=True)
  ```

### Concurrency and Threading

- Use `threading` for CPU-bound/audio processing tasks
- Use `threading.Event()` for atomic flags between threads
- Use `threading.Lock()` for mutable state
- Use shared `queue.Queue` for thread-safe communication
- Use `contextlib.suppress(ExceptionType)` for expected non-errors
- Use `asyncio.run()` for async operations (LLM calls)

### File Operations

- Use `Path` from `pathlib`, not string paths
- Validate file existence early with `.exists()`
- Use absolute paths from `Path.resolve()` when storing
- Store paths relative to `DATA_FOLDER` for portability

### Code Comments

- Keep comments concise and factual
- Explain "why", not "what"
- Use docstrings for public functions and classes
- Inline comments for complex logic or non-obvious behavior
- Document critical constants (see presentation_controller.py constants)

### Rich UI Patterns

- Define themes as `Theme` dict at module level
- Use styled text with markup: `"[accent]text[/]"`
- Use `Panel`, `Table`, `Text`, `Group` for structured output
- Use `Live` for real-time terminal updates
- Use `Progress` with spinners for async operations

### Project Structure

```
src/moves_cli/
├── __init__.py           # Package root
├── cli.py                # Typer CLI commands
├── config.py             # Global configuration
├── models.py             # Pydantic/dataclass models
├── core/                 # Core business logic
│   ├── presentation_controller.py
│   ├── speaker_manager.py
│   ├── settings_editor.py
│   └── components/
│       ├── section_producer.py
│       ├── chunk_producer.py
│       └── similarity_calculator/
├── utils/                # Utilities
│   ├── text_normalizer.py
│   ├── formatters.py
│   ├── data_handler.py
│   └── ...
└── data/                 # ML models (at build time)
```

### Critical Paths (Don't Modify Without Testing)

- `models.py:94-131` - ML model configurations with hardcoded hashes
- `cli.py:1-100` - CLI command structure
- `core/presentation_controller.py` - Audio processing and navigation logic
- `core/speaker_manager.py` - Speaker lifecycle management
- `utils/text_normalizer.py` - Speech normalization pipeline

### Performance Considerations

- Text normalization has two modes: `LIVE` (skip num2words) and `PREPROCESS`
- Use xxhash for fast file hashing
- Sliding window buffer limits memory: `self._word_buffer[-window_size:]`
- VAD gating prevents unnecessary STT processing
