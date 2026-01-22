# Development Guide

Guide for contributors and developers who want to work on `moves` locally.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Project Structure](#project-structure)
3. [Development Setup](#development-setup)
4. [Running Tests](#running-tests)
5. [Code Style & Standards](#code-style--standards)
6. [Making Changes](#making-changes)
7. [Debugging](#debugging)
8. [Building & Publishing](#building--publishing)

## Getting Started

### Prerequisites

- **Python 3.13+** – Required version
- **uv** – Package manager (or pip)
- **Git** – For version control
- **Windows, macOS, or Linux** – Cross-platform

### Understanding the Project

`moves` is a CLI tool written in Python that:
- Extracts slides from PDFs
- Analyzes transcripts with LLM
- Performs real-time speech recognition
- Matches speech to presentation content

**Key Technologies**:
- **Typer** – CLI framework
- **Rich** – Terminal UI
- **Sherpa-ONNX** – Speech recognition (offline)
- **FastEmbed** – Semantic embeddings
- **LiteLLM** – LLM provider abstraction

---

## Project Structure

```
moves-cli/
├── pyproject.toml                    # Project metadata, dependencies
├── README.md                         # User-facing readme
├── LICENSE                           # GPL v3
│
├── docs/                             # User documentation
│   ├── GETTING_STARTED.md
│   ├── ARCHITECTURE.md
│   ├── CLI_REFERENCE.md
│   ├── CONFIGURATION.md
│   └── DEVELOPMENT.md (this file)
│
├── src/moves_cli/                    # Main package
│   ├── __init__.py
│   ├── cli.py                        # Typer CLI entry point
│   ├── config.py                     # Configuration constants
│   ├── models.py                     # Pydantic/dataclass models
│   │
│   ├── core/                         # Core business logic
│   │   ├── presentation_controller.py   # Real-time audio + UI
│   │   ├── speaker_manager.py           # Speaker lifecycle
│   │   ├── settings_editor.py           # Settings management
│   │   │
│   │   └── components/               # Reusable components
│   │       ├── chunk_producer.py        # Generate chunks
│   │       ├── section_producer.py      # Parse markdown
│   │       ├── similarity_calculator.py # Matching engine
│   │       │
│   │       └── similarity_units/     # Similarity algorithms
│   │           ├── semantic.py
│   │           └── phonetic.py
│   │
│   ├── utils/                        # Utilities
│   │   ├── data_handler.py           # File I/O
│   │   ├── formatters.py             # Output formatting
│   │   ├── text_normalizer.py        # Text processing
│   │   ├── google_handler.py         # Google Drive
│   │   ├── model_preparer.py         # Model downloads
│   │   ├── id_generator.py           # ID generation
│   │   └── calculate_hash.py         # Hashing
│   │
│   └── data/                         # Data files
│       ├── llm_instruction.md        # LLM prompt
│       └── ml_models/                # ONNX models (generated)
│
└── experiments/                      # Experimental code
    ├── test_*.py
    └── calculate_xxhash.py
```

---

## Development Setup

### 1. Clone the Repository

```powershell
git clone https://github.com/mdonmez/moves-cli.git
cd moves-cli
```

### 2. Create Virtual Environment

Using `uv`:
```powershell
uv venv
.\.venv\Scripts\Activate.ps1
```

Or traditional Python:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install in Development Mode

```powershell
uv pip install -e ".[dev]"
```

Or with pip:
```powershell
pip install -e ".[dev]"
```

This installs the package in editable mode, so changes to source code are immediately reflected.

### 4. Verify Installation

```powershell
moves --version
moves --help
```

---

## Running Tests

### Current Status

The codebase includes experimental test files in `experiments/` but no formal test suite yet. 

**Recommended**: Add pytest tests as you add features.

### Experiment Scripts

Quick test scripts available:

```powershell
python experiments/test_renderer_results.py
python experiments/test_mistune_renderer.py
python experiments/calculate_xxhash.py
```

These demonstrate various components but are not comprehensive tests.

### Adding Tests

Create a `tests/` directory with pytest tests:

```powershell
mkdir tests
```

Example test file (`tests/test_similarity.py`):

```python
import pytest
from moves_cli.core.components.similarity_calculator import SimilarityCalculator
from moves_cli.models import Chunk, Section

def test_similarity_basic():
    """Test basic similarity calculation."""
    section = Section(content="hello world", section_index=0)
    chunk = Chunk(
        partial_content="hello world",
        source_sections=(section,),
        chunk_id="test-1"
    )
    
    calculator = SimilarityCalculator([chunk])
    results = calculator.compare("hello world", [chunk])
    
    assert len(results) > 0
    assert results[0].score > 0.8  # Should be high similarity
```

Run tests:
```powershell
uv run pytest tests/
```

---

## Code Style & Standards

### Style Guidelines

The project follows modern Python best practices (see your custom instructions):

**Type Hints**:
- Use built-in types: `list[int]`, `dict[str, int]` (not `List`, `Dict`)
- Use pipe unions: `int | None` (not `Optional[int]`)
- Always annotate return types: `-> None`

**Example**:
```python
def process_sections(
    sections: list[Section],
    window_size: int,
) -> list[Chunk]:
    """Process sections into chunks.
    
    Args:
        sections: List of presentation sections
        window_size: Words per chunk
    
    Returns:
        List of generated chunks
    """
    ...
```

**Imports**:
- Sort imports (alphabet order)
- Separate: builtins, third-party, local imports
- Use `from pathlib import Path` (not `os.path`)

**Docstrings**:
- Use Google-style for complex functions/classes
- Brief one-liner for simple functions

**Code Organization**:
- Constants at top: `MY_CONST = 42`
- Public functions before private (`_private`)
- Classes with `@dataclass` when appropriate

### Linting

Using Ruff for linting:

```powershell
uv run ruff check src/
uv run ruff format src/
```

---

## Making Changes

### Adding a New Feature

Example: Add a new similarity unit.

#### 1. Create the Module

Create `src/moves_cli/core/components/similarity_units/lexical.py`:

```python
"""Lexical similarity matching using token-based comparison."""

from moves_cli.models import Chunk, SimilarityResult


class Lexical:
    """Compare chunks using lexical/token similarity."""
    
    def __init__(self, all_chunks: list[Chunk]):
        self.all_chunks = all_chunks
    
    def compare(
        self,
        input_str: str,
        candidates: list[Chunk],
    ) -> list[SimilarityResult]:
        """Compare input to candidates using lexical matching.
        
        Args:
            input_str: Input text to match
            candidates: Chunks to compare against
        
        Returns:
            Sorted list of similarity results
        """
        results = []
        input_tokens = set(input_str.lower().split())
        
        for chunk in candidates:
            chunk_tokens = set(chunk.partial_content.lower().split())
            intersection = len(input_tokens & chunk_tokens)
            union = len(input_tokens | chunk_tokens)
            
            score = intersection / union if union > 0 else 0.0
            results.append(SimilarityResult(chunk=chunk, score=score))
        
        return sorted(results, key=lambda x: -x.score)
```

#### 2. Integrate into Similarity Calculator

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
        self.semantic_weight = semantic_weight
        self.phonetic_weight = phonetic_weight
        self.lexical_weight = lexical_weight
        self.semantic = Semantic(all_chunks)
        self.phonetic = Phonetic(all_chunks)
        self.lexical = Lexical(all_chunks)  # New
        # ... rest of init
```

#### 3. Add Tests

Create `tests/test_lexical_similarity.py`:

```python
import pytest
from moves_cli.core.components.similarity_units.lexical import Lexical
from moves_cli.models import Chunk, Section


def test_lexical_exact_match():
    """Test lexical similarity with exact match."""
    section = Section(content="hello world test", section_index=0)
    chunk = Chunk(
        partial_content="hello world test",
        source_sections=(section,),
        chunk_id="test-1"
    )
    
    lexical = Lexical([chunk])
    results = lexical.compare("hello world test", [chunk])
    
    assert results[0].score == 1.0
```

#### 4. Update Config if Needed

If adding configurable parameters, add to `src/moves_cli/config.py`:

```python
LEXICAL_WEIGHT = 0.0  # New weight parameter
```

#### 5. Update Documentation

Add to [ARCHITECTURE.md](ARCHITECTURE.md) under "Similarity Calculator":

> **Lexical Similarity** – Token-based matching for exact word overlap

---

## Debugging

### Print Debugging

```python
from moves_cli.utils.formatters import output
import typer

# Simple output
typer.echo(output(f"Debug: {value}"))

# Formatted table
typer.echo(output("Processing", {"status": "running", "progress": "50%"}))
```

### Logging

Use `loguru` for structured logging:

```python
from loguru import logger

logger.info("Starting speaker preparation")
logger.debug(f"Processing section {i}")
logger.error("Failed to download model", exc_info=True)
```

### Interactive Debugging

Using Python debugger:

```powershell
# Add breakpoint
uv run python -m pdb src/moves_cli/cli.py
```

Or use an IDE debugger (VS Code, PyCharm, etc.).

### Testing Individual Components

Quick test of similarity calculator:

```python
from moves_cli.models import Section, Chunk
from moves_cli.core.components.similarity_calculator import SimilarityCalculator

# Create test data
section = Section(content="hello world", section_index=0)
chunk = Chunk(partial_content="hello world", source_sections=(section,), chunk_id="1")

# Test similarity
calc = SimilarityCalculator([chunk])
results = calc.compare("hello world", [chunk])
print(results[0].score)
```

---

## Building & Publishing

### Local Build

Build the wheel locally:

```powershell
uv build
```

Produces:
- `dist/moves_cli-*.whl` – Installable wheel
- `dist/moves_cli-*.tar.gz` – Source archive

### Installing Local Build

```powershell
uv tool install dist/moves_cli-*.whl
```

### Publishing to PyPI

**Prerequisites**:
- PyPI account
- API token from PyPI

**Process**:

1. Update version in `pyproject.toml`:
   ```toml
   version = "0.3.3"
   ```

2. Build:
   ```powershell
   uv build
   ```

3. Publish:
   ```powershell
   uv publish
   ```

(Or use `twine`: `twine upload dist/*`)

---

## Common Development Tasks

### Add a New CLI Command

Edit `src/moves_cli/cli.py`:

```python
@app.command()
def export(
    speaker: str = typer.Argument(..., help="Speaker to export"),
    output: str = typer.Option("output.md", help="Output file"),
):
    """Export speaker sections as markdown."""
    typer.echo(f"Exporting {speaker} to {output}")
    # Implementation...
```

### Modify Configuration Constants

Edit `src/moves_cli/config.py`:

```python
# Adjust thresholds
SIMILARITY_THRESHOLD = 0.75  # Was 0.7
WINDOW_SIZE = 15            # Was 12
```

Restart after changing:
```powershell
moves --help
```

### Update LLM Prompt

Edit `src/moves_cli/data/llm_instruction.md` to change how sections are generated.

### Add New Dependency

```powershell
uv add package-name
```

Or for dev-only:
```powershell
uv add -d pytest
```

This updates `pyproject.toml` automatically.

### Run a Single Experiment

```powershell
uv run experiments/test_renderer_results.py
```

---

## Troubleshooting Development

### Import Errors

Make sure you're using editable install:
```powershell
uv pip install -e .
```

### Model Download Issues

Delete model cache and let it re-download:
```powershell
rm -r $env:USERPROFILE\.moves\ml_models
moves speaker prepare MyTalk  # Re-downloads models
```

### Virtual Environment Issues

Recreate environment:
```powershell
rm -r .venv
uv venv
.\.venv\Scripts\Activate.ps1
uv pip install -e .
```

### Dependency Conflicts

Check installed versions:
```powershell
uv pip list | grep moves
```

Sync with lock file:
```powershell
uv sync
```

---

## Git Workflow

### Cloning for Development

```powershell
git clone https://github.com/mdonmez/moves-cli.git
cd moves-cli
```

### Creating a Feature Branch

```powershell
git checkout -b feature/my-new-feature
```

### Committing Changes

```powershell
git add src/moves_cli/my_file.py
git commit -m "Add: new similarity feature"
```

### Pushing Changes

```powershell
git push origin feature/my-new-feature
```

Then open a Pull Request on GitHub.

---

## Additional Resources

- [Architecture Guide](ARCHITECTURE.md) – System design
- [Configuration Guide](CONFIGURATION.md) – Settings options
- [LiteLLM Docs](https://docs.litellm.ai/) – LLM provider details
- [Typer Docs](https://typer.tiangolo.com/) – CLI framework
- [Rich Docs](https://rich.readthedocs.io/) – Terminal UI
- [Pydantic Docs](https://docs.pydantic.dev/) – Data validation

---

## Contribution Guidelines

1. **Fork** the repository
2. **Create** a feature branch
3. **Make changes** with clear commits
4. **Add tests** for new functionality
5. **Update docs** as needed
6. **Submit PR** with description

**Code Review**: Expect feedback on:
- Correctness and robustness
- Code style and clarity
- Test coverage
- Documentation completeness

---

Thank you for contributing to `moves`! Questions? Open an issue on GitHub.
