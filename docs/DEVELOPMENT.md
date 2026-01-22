# Development Guide

Guide for contributors and developers working on `moves`.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Development Setup](#development-setup)
3. [Project Structure](#project-structure)
4. [Code Style](#code-style)
5. [Running Tests](#running-tests)
6. [Making Changes](#making-changes)
7. [Debugging](#debugging)
8. [Building & Publishing](#building--publishing)
9. [Contributing](#contributing)

---

## Prerequisites

### Required

- **Python 3.13+** – Required for type hints and modern syntax
- **uv** – Package manager (recommended) or pip
- **Git** – Version control

### Recommended

- **VS Code** or **PyCharm** – IDE with Python support
- **Microphone** – For testing presentation mode

---

## Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/mdonmez/moves-cli.git
cd moves-cli
```

### 2. Create Virtual Environment

**Using uv (recommended):**
```bash
uv venv
source .venv/bin/activate  # Linux/macOS
# or
.\.venv\Scripts\Activate.ps1  # Windows PowerShell
```

**Using standard Python:**
```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install in Development Mode

```bash
# With uv
uv pip install -e .

# Or with pip
pip install -e .
```

This installs the package in editable mode – changes to source code take effect immediately.

### 4. Verify Installation

```bash
moves --version
moves --help
```

---

## Project Structure

```
moves-cli/
├── pyproject.toml                # Project metadata, dependencies
├── README.md                     # User-facing readme
├── LICENSE                       # GPL v3 license
├── uv.lock                       # Dependency lock file
│
├── docs/                         # Documentation
│   ├── INDEX.md
│   ├── GETTING_STARTED.md
│   ├── ARCHITECTURE.md
│   ├── CLI_REFERENCE.md
│   ├── CONFIGURATION.md
│   └── DEVELOPMENT.md
│
├── src/moves_cli/                # Main package
│   ├── __init__.py
│   ├── cli.py                    # Typer CLI entry point
│   ├── config.py                 # Configuration constants
│   ├── models.py                 # Data models (Section, Chunk, etc.)
│   │
│   ├── core/                     # Core business logic
│   │   ├── presentation_controller.py  # Real-time audio + UI
│   │   ├── speaker_manager.py          # Speaker lifecycle
│   │   ├── settings_editor.py          # Settings management
│   │   │
│   │   └── components/           # Reusable components
│   │       ├── chunk_producer.py
│   │       ├── section_producer.py
│   │       ├── similarity_calculator.py
│   │       │
│   │       └── similarity_units/
│   │           ├── semantic.py
│   │           └── phonetic.py
│   │
│   ├── utils/                    # Utilities
│   │   ├── data_handler.py
│   │   ├── formatters.py
│   │   ├── text_normalizer.py
│   │   ├── google_handler.py
│   │   ├── model_preparer.py
│   │   ├── id_generator.py
│   │   └── calculate_hash.py
│   │
│   └── data/                     # Data files
│       ├── llm_instruction.md    # LLM system prompt
│       └── ml_models/            # ONNX models (generated)
│
└── experiments/                  # Experimental scripts
    └── *.py
```

---

## Code Style

### Type Hints (Python 3.10+ Style)

Use built-in types, not `typing` module:

```python
# ✅ Good
def process(items: list[str], options: dict[str, int]) -> list[Result]:
    pass

# ❌ Avoid
from typing import List, Dict
def process(items: List[str], options: Dict[str, int]) -> List[Result]:
    pass
```

Use pipe for unions:

```python
# ✅ Good
def get_value(key: str) -> str | None:
    pass

# ❌ Avoid
from typing import Optional
def get_value(key: str) -> Optional[str]:
    pass
```

Always annotate return types:

```python
# ✅ Good
def setup() -> None:
    pass

# ❌ Avoid
def setup():
    pass
```

### Dataclasses

Use `@dataclass` for data containers:

```python
from dataclasses import dataclass

@dataclass(frozen=True)  # Use frozen for immutability
class Section:
    content: str
    section_index: int

@dataclass
class Speaker:
    name: str
    speaker_id: str
```

### Enums

Use `StrEnum` for string-based enums:

```python
from enum import StrEnum

class NormalizationMode(StrEnum):
    LIVE = "live"
    PREPROCESS = "preprocess"
```

### Imports

Sort imports: stdlib, third-party, local:

```python
# Stdlib
from dataclasses import dataclass
from pathlib import Path

# Third-party
import typer
from rich.console import Console

# Local
from moves_cli.config import DATA_FOLDER
from moves_cli.models import Section
```

### Docstrings

Google-style for complex functions:

```python
def generate_chunks(sections: list[Section], window_size: int) -> list[Chunk]:
    """Generate sliding window chunks from sections.
    
    Args:
        sections: List of presentation sections.
        window_size: Number of words per chunk.
    
    Returns:
        List of generated chunks for similarity matching.
    
    Raises:
        ValueError: If window_size is less than 1.
    """
```

Brief for simple functions:

```python
def normalize_text(text: str) -> str:
    """Normalize text by removing diacritics and special characters."""
```

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Classes | `PascalCase` | `SpeakerManager`, `SimilarityCalculator` |
| Functions | `snake_case` | `generate_sections`, `_extract_pdf` |
| Constants | `ALL_CAPS` | `DATA_FOLDER`, `WINDOW_SIZE` |
| Private | `_leading_underscore` | `_internal_method` |
| Variables | `snake_case` | `speaker_id`, `section_index` |

### Linting

Use Ruff for linting and formatting:

```bash
# Check for issues
uv run ruff check src/

# Auto-fix issues
uv run ruff check --fix src/

# Format code
uv run ruff format src/
```

---

## Running Tests

### Current Status

The project uses experimental scripts in `experiments/` rather than a formal test suite.

### Running Experiments

```bash
uv run python experiments/test_renderer_results.py
uv run python experiments/test_mistune_renderer.py
```

### Adding Tests

Create `tests/` directory with pytest:

```bash
mkdir tests
```

Example test (`tests/test_similarity.py`):

```python
import pytest
from moves_cli.core.components.similarity_calculator import SimilarityCalculator
from moves_cli.models import Chunk, Section


def test_similarity_exact_match():
    """Test similarity with exact matching content."""
    section = Section(content="hello world test", section_index=1)
    chunk = Chunk(
        partial_content="hello world test",
        source_sections=(section,),
        chunk_id="test-1"
    )
    
    calculator = SimilarityCalculator([chunk])
    results = calculator.compare("hello world test", [chunk], current_section_index=1)
    
    assert len(results) == 1
    assert results[0].score > 0.8


def test_similarity_empty_input():
    """Test similarity with empty input."""
    calculator = SimilarityCalculator([])
    results = calculator.compare("", [])
    
    assert results == []
```

Run tests:

```bash
uv run pytest tests/ -v
```

---

## Making Changes

### Example: Adding a New Similarity Unit

#### 1. Create the Module

Create `src/moves_cli/core/components/similarity_units/lexical.py`:

```python
"""Lexical similarity using token overlap."""

from moves_cli.models import Chunk, SimilarityResult


class Lexical:
    """Token-based similarity comparison."""
    
    def __init__(self, all_chunks: list[Chunk]) -> None:
        """Initialize with all chunks for potential pre-computation."""
        self._chunks = all_chunks
    
    def compare(
        self,
        input_str: str,
        candidates: list[Chunk],
    ) -> list[SimilarityResult]:
        """Compare input to candidates using token overlap (Jaccard).
        
        Args:
            input_str: Input text to match.
            candidates: Chunks to compare against.
        
        Returns:
            Sorted list of similarity results.
        """
        if not candidates:
            return []
        
        input_tokens = set(input_str.lower().split())
        results = []
        
        for chunk in candidates:
            chunk_tokens = set(chunk.partial_content.lower().split())
            intersection = len(input_tokens & chunk_tokens)
            union = len(input_tokens | chunk_tokens)
            
            score = intersection / union if union > 0 else 0.0
            results.append(SimilarityResult(chunk=chunk, score=score))
        
        return sorted(results, key=lambda x: -x.score)
```

#### 2. Integrate into Calculator

Edit `src/moves_cli/core/components/similarity_calculator.py`:

```python
from moves_cli.core.components.similarity_units.lexical import Lexical

class SimilarityCalculator:
    def __init__(
        self,
        all_chunks: list[Chunk],
        semantic_weight: float = SEMANTIC_WEIGHT,
        phonetic_weight: float = PHONETIC_WEIGHT,
        lexical_weight: float = 0.0,  # New parameter
    ):
        # ... existing code ...
        self.lexical = Lexical(all_chunks)  # Add this
```

#### 3. Add Configuration

Edit `src/moves_cli/config.py`:

```python
LEXICAL_WEIGHT = 0.0  # New config option
```

#### 4. Add Tests

Create `tests/test_lexical.py`:

```python
from moves_cli.core.components.similarity_units.lexical import Lexical
from moves_cli.models import Chunk, Section


def test_lexical_exact_match():
    section = Section(content="test", section_index=1)
    chunk = Chunk(partial_content="hello world", source_sections=(section,), chunk_id="1")
    
    lexical = Lexical([chunk])
    results = lexical.compare("hello world", [chunk])
    
    assert results[0].score == 1.0


def test_lexical_partial_match():
    section = Section(content="test", section_index=1)
    chunk = Chunk(partial_content="hello world", source_sections=(section,), chunk_id="1")
    
    lexical = Lexical([chunk])
    results = lexical.compare("hello there", [chunk])
    
    # Jaccard: {"hello"} ∩ {"hello", "world"} / {"hello", "there", "world"} = 1/3
    assert 0.3 < results[0].score < 0.4
```

#### 5. Update Documentation

Add to [ARCHITECTURE.md](ARCHITECTURE.md):
> **Lexical Similarity** – Token overlap using Jaccard index

---

## Debugging

### Print Debugging

Use the output formatter:

```python
from moves_cli.utils.formatters import output
import typer

typer.echo(output("Debug message", {"key": "value"}))
```

### Interactive Debugging

Python debugger:

```bash
uv run python -m pdb -c continue src/moves_cli/cli.py speaker list
```

Or use VS Code / PyCharm debugger.

### Testing Individual Components

```python
# In Python REPL
from moves_cli.models import Section, Chunk
from moves_cli.core.components.chunk_producer import generate_chunks

sections = [
    Section(content="hello world", section_index=1),
    Section(content="foo bar baz", section_index=2),
]
chunks = generate_chunks(sections, window_size=3)
print(f"Generated {len(chunks)} chunks")
```

---

## Building & Publishing

### Local Build

```bash
uv build
```

Produces:
- `dist/moves_cli-*.whl` – Wheel package
- `dist/moves_cli-*.tar.gz` – Source archive

### Install Local Build

```bash
uv tool install dist/moves_cli-*.whl
```

### Version Update

Edit `pyproject.toml`:

```toml
[project]
version = "0.3.4"  # Update this
```

### Publishing to PyPI

1. Build:
   ```bash
   uv build
   ```

2. Publish:
   ```bash
   uv publish
   ```

Or use twine:
```bash
pip install twine
twine upload dist/*
```

---

## Contributing

### Workflow

1. **Fork** the repository
2. **Create** a feature branch:
   ```bash
   git checkout -b feature/my-feature
   ```
3. **Make changes** with clear commits
4. **Add tests** for new functionality
5. **Update docs** as needed
6. **Run linting**:
   ```bash
   uv run ruff check src/
   uv run ruff format src/
   ```
7. **Submit PR** with description

### Commit Messages

Use clear, descriptive messages:

```
Add: lexical similarity unit for token matching
Fix: VAD threshold not being applied correctly
Update: documentation for new CLI options
Refactor: extract audio processing into separate module
```

### Code Review

Expect feedback on:
- Correctness and edge cases
- Code style consistency
- Test coverage
- Documentation updates
- Performance implications

### Areas for Contribution

- **New similarity algorithms** – `similarity_units/`
- **New document formats** – `section_producer.py`
- **UI improvements** – `presentation_controller.py`
- **Performance optimizations** – Profiling and caching
- **Documentation** – Examples, tutorials, translations
- **Tests** – Unit and integration tests

---

## Common Tasks

### Add a New CLI Command

```python
# In cli.py
@app.command()
def export(
    speaker: str = typer.Argument(..., help="Speaker to export"),
    output: Path = typer.Option("output.md", help="Output file"),
):
    """Export speaker sections to file."""
    # Implementation
```

### Add a Dependency

```bash
uv add package-name

# Dev dependency
uv add -d pytest
```

### Update LLM Prompt

Edit `src/moves_cli/data/llm_instruction.md` and rebuild.

### Modify Configuration

Edit `src/moves_cli/config.py`:

```python
WINDOW_SIZE = 15  # Changed from 12
```

---

## Resources

- [Architecture Guide](ARCHITECTURE.md) – System design
- [CLI Reference](CLI_REFERENCE.md) – Command documentation
- [LiteLLM Docs](https://docs.litellm.ai/) – LLM provider reference
- [Typer Docs](https://typer.tiangolo.com/) – CLI framework
- [Rich Docs](https://rich.readthedocs.io/) – Terminal UI
- [Sherpa-ONNX](https://k2-fsa.github.io/sherpa/onnx/) – Speech recognition

---

Questions? [Open an issue](https://github.com/mdonmez/moves-cli/issues).
