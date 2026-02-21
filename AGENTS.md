# Agent Guidelines for moves-cli

moves-cli is a Python CLI tool for voice-controlled presentation navigation.

**Tech Stack**: Python 3.13+, Typer, Rich, Sherpa-ONNX, FastEmbed, LiteLLM, PyMuPDF4LLM, python-pptx, python-docx

## Commands

### Package Management (uv)

```powershell
uv add <package>           # Add dependency
uv add -d <package>        # Add dev dependency
uv sync                    # Install from lockfile
uv pip install -e .        # Editable install
```

### Lint & Format

```powershell
uv run ruff check src/         # Check issues
uv run ruff format src/        # Format code
uv run ruff check --fix src/   # Auto-fix
```

### Testing

```powershell
uv run pytest tests/                        # All tests
uv run pytest tests/test_file.py            # Single file
uv run pytest tests/test_file.py::test_name # Single test
uv run pytest -v tests/                     # Verbose
```

### CLI

```powershell
moves --version
moves --help
moves speaker list
moves present <speaker>
```

## Code Style

### Type Hints

- Built-in collections: `list[int]`, `dict[str, int]`
- Pipe for unions: `int | None`, `str | int`
- Avoid `typing.List`, `typing.Dict`, `typing.Optional`

### Imports

- Alphabetical within groups, separate stdlib/third-party/local
- Explicit imports, no wildcards

```python
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

import typer

from moves_cli.config import DATA_FOLDER
from moves_cli.models import Section
```

### Dataclasses & Models

- Use `@dataclass`, `frozen=True` for immutable
- Use `StrEnum` for string enums

### Naming

- Classes: `PascalCase`
- Functions: `snake_case`
- Constants: `ALL_CAPS`
- Private: leading underscore

### Docstrings

- Google-style for complex functions
- One-line for simple functions

### File Operations

- Use `pathlib.Path`, convert to `str()` for libraries
- Use context managers

### Error Handling

- Specific exceptions, re-raise with `from e`
- CLI: handle `typer.Exit`, use `output()` formatter

```python
try:
    ...
except typer.Exit:
    raise
except (ValueError, FileNotFoundError) as e:
    typer.echo(output(f"Error: {str(e)}"), err=True)
    raise typer.Exit(1)
```

### Logging

- Use `loguru`, include `exc_info=True` for errors

### CLI Commands (Typer)

- `@app.command()` decorators, help text for all args
- Use `typer.Option` and `typer.Argument`

### String Formatting

- Use f-strings only

### Async

- Use `asyncio`, wrap CLI entry points with `asyncio.run()`

## Project Structure

```
src/moves_cli/
├── __init__.py           # Package entry, version
├── cli.py                # Typer CLI entry point
├── config.py             # Configuration constants
├── models.py             # Dataclass models
├── core/
│   ├── presentation_controller.py
│   ├── speaker_manager.py
│   ├── settings_editor.py
│   └── components/
│       ├── chunk_producer.py
│       ├── section_producer.py
│       └── similarity_calculator.py
├── utils/
│   ├── data_handler.py
│   ├── formatters.py
│   ├── text_normalizer.py
│   └── google_handler.py
└── data/                 # ML models
```

## Important Notes

- **Windows-first**: Assumes Windows paths and keyring
- **Model files**: ML models in `data/` - don't modify hashes
- **Editable install**: Changes reflected immediately
