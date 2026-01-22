# Agent Guidelines for moves-cli

This document provides guidelines for AI agents working on the moves-cli codebase.

## Project Overview

moves-cli is a Python CLI tool for voice-controlled presentation navigation. It extracts slides from multiple formats (PDF, DOCX, PPTX, TXT), analyzes transcripts with LLMs, performs real-time speech recognition, and matches speech to presentation content.

**Tech Stack**: Python 3.13+, Typer (CLI), Rich (UI), Sherpa-ONNX (speech recognition), FastEmbed (embeddings), LiteLLM (LLM abstraction), PyMuPDF4LLM (PDF), python-pptx (PPTX), python-docx (DOCX)

## Build, Lint, and Test Commands

### Package Management (use uv)
```powershell
uv add <package>           # Add dependency
uv add -d <package>        # Add dev dependency
uv remove <package>        # Remove dependency
uv sync                    # Install from lockfile
uv pip install -e .        # Install in editable mode
uv pip install -e ".[dev]" # Install with dev dependencies
```

### Linting and Formatting
```powershell
uv run ruff check src/     # Check for issues
uv run ruff format src/    # Format code
uv run ruff check --fix src/  # Auto-fix issues
```

### Testing
```powershell
uv run pytest tests/                    # Run all tests
uv run pytest tests/test_file.py        # Run specific test file
uv run pytest tests/test_file.py::test_name  # Run single test
uv run pytest -v tests/                 # Verbose output
```

### Building
```powershell
uv build                    # Build wheel and source
uv publish                  # Publish to PyPI
```

### Running the CLI
```powershell
moves --version
moves --help
moves speaker list
moves present <speaker>
```

### Development Scripts
```powershell
uv run python experiments/test_renderer_results.py
uv run python experiments/test_mistune_renderer.py
```

## Code Style Guidelines

### Type Hints (Python 3.10+)
- Use built-in collection types: `list[int]`, `dict[str, int]`, `tuple[str, int]`
- Use pipe operator for unions: `int | None`, `str | int`
- Avoid `typing.List`, `typing.Dict`, `typing.Optional` (use built-ins)
- Always annotate function return types, including `-> None`

```python
def process_sections(
    sections: list[Section],
    window_size: int,
) -> list[Chunk]:
    """Process sections into chunks."""
    ...
```

### Imports
- Sort imports alphabetically within groups
- Separate groups: stdlib, third-party, local
- Use explicit imports: `from pathlib import Path` (not `import os.path`)
- Avoid wildcard imports

```python
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

import typer

from moves_cli.config import DATA_FOLDER
from moves_cli.models import Section
```

### Dataclasses and Models
- Use `@dataclass` for data containers
- Use `frozen=True` for immutable models (prevents accidental modification)
- Use `tuple` for truly immutable sequences in dataclasses

```python
@dataclass(frozen=True)
class Section:
    content: str
    section_index: int

@dataclass
class Speaker:
    name: str
    speaker_id: str
    source_presentation: Path
```

### Enums
- Use `StrEnum` for string-based enums (better for CLI/serialization)

```python
class NormalizationMode(StrEnum):
    LIVE = "live"
    PREPROCESS = "preprocess"
```

### Naming Conventions
- Classes: `PascalCase` (e.g., `SpeakerManager`, `SectionProducer`)
- Functions/methods: `snake_case` (e.g., `generate_sections`, `_extract_document`)
- Constants: `ALL_CAPS` (e.g., `DATA_FOLDER`, `WINDOW_SIZE`)
- Private members: leading underscore (e.g., `_internal_method`)
- Variables: `snake_case` (e.g., `speaker_id`, `section_index`)

### Docstrings
- Use Google-style docstrings for complex functions/classes
- One-line summary for simple functions
- Include Args, Returns, and Raises sections when relevant

```python
def load_from_markdown(self, markdown_content: str) -> list[Section]:
    """Load sections from markdown format.

    Parses `# N. Slide` headings as section indices, content follows
    until next heading.

    Args:
        markdown_content: Markdown string with section format.

    Returns:
        List of Section objects.
    """
```

### File Operations
- Use `pathlib.Path` for all file paths
- Convert Path to str when needed for libraries (e.g., `str(file_path)`)
- Use context managers (`with` statements)

```python
# PDF extraction with PyMuPDF4LLM
chunks = pymupdf4llm.to_markdown(str(file_path), page_chunks=True)

# Office document extraction
doc = Document(str(file_path))  # python-docx
prs = Presentation(str(file_path))  # python-pptx
```

### Error Handling
- Use specific exception types when possible
- Re-raise with context using `from e`
- Provide meaningful error messages
- Always exit with appropriate codes in CLI commands

```python
try:
    presentation_path = resolve_source_path(source_presentation)
except Exception as e:
    raise RuntimeError(f"Failed to resolve path: {e}") from e

# In CLI commands
try:
    ...
except typer.Exit:
    raise
except (ValueError, FileNotFoundError) as e:
    typer.echo(output(f"Error: {str(e)}"), err=True)
    raise typer.Exit(1)
```

### CLI Commands (Typer)
- Use `@app.command()` decorators
- Provide help text for arguments and options
- Use `typer.Option` and `typer.Argument` with help strings
- Handle `typer.Exit` and `typer.Abort` specifically
- Always use `output()` formatter from `moves_cli.utils.formatters`

```python
@speaker_app.command("add")
def speaker_add(
    name: str = typer.Argument(..., help="Speaker's name"),
    source_presentation: str = typer.Argument(..., help="Path or Google URL"),
):
    """Create a new speaker profile"""
    try:
        ...
    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(output(f"Error: {str(e)}"), err=True)
        raise typer.Exit(1)
```

### Logging
- Use `loguru` for structured logging
- Include `exc_info=True` for errors

```python
from loguru import logger

logger.info("Starting speaker preparation")
logger.debug(f"Processing section {i}")
logger.error("Failed to download model", exc_info=True)
```

### Code Organization
- Constants at module top or in `config.py`
- Public functions before private (`_private`)
- Constants in ALL_CAPS
- Private imports inside functions when needed to avoid circular deps

### String Formatting
- Use f-strings for all string formatting
- Avoid `%` formatting and `.format()`

```python
result = f"Speaker {speaker.label} prepared."
```

### Async Operations
- Use `asyncio` for I/O-bound operations
- Wrap with `asyncio.run()` for CLI entry points

```python
results = asyncio.run(speaker_manager.process(...))
```

## Project Structure

```
src/moves_cli/
├── __init__.py           # Package entry, version
├── cli.py                # Typer CLI entry point
├── config.py             # Configuration constants
├── models.py             # Pydantic/dataclass models
├── core/
│   ├── presentation_controller.py  # Real-time audio + UI
│   ├── speaker_manager.py          # Speaker lifecycle
│   ├── settings_editor.py          # Settings management
│   └── components/
│       ├── chunk_producer.py       # Generate chunks
│       ├── section_producer.py     # Parse markdown
│       └── similarity_calculator.py  # Matching engine
├── utils/
│   ├── data_handler.py     # File I/O
│   ├── formatters.py       # Output formatting
│   ├── text_normalizer.py  # Text processing
│   ├── google_handler.py   # Google Drive
│   └── ...
└── data/                   # Data files, ML models
```

## Common Development Tasks

### Adding a New CLI Command
1. Add command function in `cli.py` with `@app.command()` decorator
2. Use proper argument/option handling with typer
3. Integrate with existing managers (speaker, settings)
4. Test with `moves <command> --help`

### Adding a New Utility
1. Create file in `src/moves_cli/utils/`
2. Follow naming conventions (`snake_case.py`)
3. Add tests in `tests/utils/`

### Modifying Configuration
1. Update `src/moves_cli/config.py`
2. Update `docs/CONFIGURATION.md` if user-facing
3. Test with different values

### Adding Dependencies
```powershell
uv add package-name
```

## Important Notes

- **Windows-first**: Code assumes Windows paths and credential manager (keyring)
- **Model files**: Critical ML models in `data/ml_models/` - don't modify hashes
- **Editable install**: Changes to source code are immediately reflected
- **No formal tests**: Currently only experimental scripts in `experiments/`
