# Test System Documentation

## Overview

The test suite evaluates the system's critical areas and overall functionality across **51 tests** organized into 4 main test files.

---

## Running Tests

```bash
# Run all tests
uv run pytest

# Verbose output
uv run pytest -v

# With coverage report
uv run pytest --cov=src --cov-report=html

# Specific test file
uv run pytest tests/test_cli.py
```

---

## Test Structure

```
tests/
├── conftest.py          # Shared fixtures and mocks
├── test_cli.py          # CLI tests (10)
├── test_core.py         # Core logic tests (17)
├── test_components.py   # Component tests (13)
└── test_utils.py        # Utility tests (11)
```

---

## Test Coverage

### 1. CLI Integration (10 tests)

Tests command-line interface workflows:

| Category               | Tests | Coverage                                         |
| ---------------------- | ----- | ------------------------------------------------ |
| **Speaker Management** | 4     | Add, list, delete speakers; handle missing files |
| **Settings**           | 2     | List and update configuration                    |
| **Processing**         | 2     | Validate API key and speaker existence           |
| **Presentation**       | 2     | Error handling for missing data                  |

---

### 2. Core Modules (17 tests)

Tests business logic and management systems:

#### Settings Editor (5 tests)

- File creation and TOML management
- Default value loading from templates
- Configuration persistence
- Corrupted file recovery

#### Speaker Manager (6 tests)

- Speaker CRUD operations
- Unique ID generation for duplicates
- JSON persistence
- Unicode/special character support

#### Presentation Controller (6 tests)

- Controller initialization
- Custom window sizing
- Flexible section navigation
- Audio buffer setup with mocked ML models

---

### 3. Components (13 tests)

Tests data processing pipeline:

#### Chunk Producer (6 tests)

- Sliding window chunk generation (default: 12 words)
- Text normalization
- Multi-section spanning
- Edge case handling

#### Section Producer (3 tests)

- PDF text extraction (PyMuPDF)
- Whitespace normalization
- Slide extraction from presentations

#### Similarity Calculator (4 tests)

- Hybrid scoring: **60% semantic + 40% phonetic** (default)
- Custom weight configuration
- Extreme weight edge cases

---

### 4. Utilities (11 tests)

Tests helper functions:

| Module              | Tests | Key Features                                         |
| ------------------- | ----- | ---------------------------------------------------- |
| **Data Handler**    | 4     | File I/O, UTF-8 encoding, directory creation         |
| **ID Generator**    | 3     | Format: `name-slug-xxxxx`, URL-safe, accent handling |
| **Text Normalizer** | 4     | Lowercase, number-to-words, accent removal           |

---

## System Mocks (`conftest.py`)

Mocks hardware dependencies for CI/CD compatibility:

```python
sys.modules["sounddevice"] = MagicMock()      # Audio device
sys.modules["pynput"] = pynput_mock           # Keyboard controller
```

**Purpose:** Enables headless testing without physical devices.

---

## Dependencies

```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.4.1",
    "pytest-cov>=7.0.0",
]
```
