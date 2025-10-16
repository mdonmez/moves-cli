# Test System Documentation

## Overview

The `moves` test suite provides comprehensive coverage of critical functionality across 55 tests organized into 4 test modules. The suite validates CLI operations, core business logic, data processing components, and utility functions.

## Test Execution

### Running Tests

**Basic Execution:**
```bash
# Run all tests
uv run pytest

# Verbose output with test names
uv run pytest -v

# Very verbose with test details
uv run pytest -vv
```

**Coverage Analysis:**
```bash
# Generate coverage report
uv run pytest --cov=src --cov-report=html

# View coverage in browser
open htmlcov/index.html
```

**Selective Testing:**
```bash
# Run specific test file
uv run pytest tests/test_cli.py

# Run specific test class
uv run pytest tests/test_core.py::TestSpeakerManager

# Run specific test function
uv run pytest tests/test_utils.py::test_normalize_text_numbers

# Run tests matching pattern
uv run pytest -k "speaker"
```

### Test Output

**Standard Output:**
```
======================== test session starts ========================
collected 55 items

tests/test_cli.py ..........                                  [ 18%]
tests/test_core.py ...............                            [ 45%]
tests/test_components.py .............                        [ 69%]
tests/test_utils.py .................                         [100%]

======================== 55 passed in 12.34s ========================
```

## Test Organization

### Test Structure

```
tests/
├── conftest.py           # Shared fixtures and system mocks
├── test_cli.py           # CLI integration tests (10 tests)
├── test_core.py          # Core module tests (15 tests)
├── test_components.py    # Data processing tests (13 tests)
└── test_utils.py         # Utility function tests (17 tests)
```

### Test Categories

**Integration Tests (`test_cli.py`)**
- End-to-end CLI command workflows
- User-facing functionality validation
- Error handling and edge cases
- File system interactions

**Unit Tests (other modules)**
- Isolated component testing
- Business logic validation
- Data transformation verification
- Algorithm correctness

## Test Coverage Analysis

### 1. CLI Integration Tests (10 tests)

**Speaker Management Commands (4 tests)**

| Test                          | Coverage                                                  |
| :---------------------------- | :-------------------------------------------------------- |
| `test_speaker_add_success`    | Successful speaker profile creation                       |
| `test_speaker_add_missing_file` | Error handling for non-existent presentation file       |
| `test_speaker_list`           | Display all registered speakers                           |
| `test_speaker_delete`         | Profile deletion and cleanup                              |

**Settings Management (2 tests)**

| Test                   | Coverage                                       |
| :--------------------- | :--------------------------------------------- |
| `test_settings_list`   | Configuration display                          |
| `test_settings_update` | Model and API key modification                 |

**Processing Validation (2 tests)**

| Test                             | Coverage                                      |
| :------------------------------- | :-------------------------------------------- |
| `test_process_missing_api_key`   | Error when LLM credentials not configured     |
| `test_process_missing_speaker`   | Error when speaker doesn't exist              |

**Presentation Control (2 tests)**

| Test                              | Coverage                                     |
| :-------------------------------- | :------------------------------------------- |
| `test_control_unprocessed_speaker` | Error when sections.json missing            |
| `test_control_missing_speaker`    | Error when speaker profile doesn't exist     |

### 2. Core Module Tests (15 tests)

**Settings Editor (5 tests)**

| Test                              | Coverage                                          |
| :-------------------------------- | :------------------------------------------------ |
| `test_settings_file_creation`     | Automatic settings.toml creation from template    |
| `test_settings_default_loading`   | Template default value loading                    |
| `test_settings_set_and_get`       | Configuration modification and retrieval          |
| `test_settings_persistence`       | Values persist across editor instances            |
| `test_settings_corrupted_recovery` | Graceful handling of corrupted TOML files        |

**Speaker Manager (6 tests)**

| Test                              | Coverage                                          |
| :-------------------------------- | :------------------------------------------------ |
| `test_speaker_add`                | Profile creation with metadata serialization      |
| `test_speaker_list`               | Enumerate all speaker profiles                    |
| `test_speaker_resolve_by_id`      | Lookup speaker by unique ID                       |
| `test_speaker_resolve_by_name`    | Lookup speaker by name                            |
| `test_speaker_duplicate_names`    | Unique ID generation for duplicate names          |
| `test_speaker_unicode_handling`   | Unicode and special character support in names    |

**Presentation Controller (4 tests)**

| Test                                  | Coverage                                      |
| :------------------------------------ | :-------------------------------------------- |
| `test_controller_initialization`      | Controller setup with sections and models     |
| `test_controller_custom_window_size`  | Configurable chunk window size                |
| `test_controller_section_navigation`  | Slide advancement based on section index      |
| `test_controller_audio_buffer_setup`  | Audio queue and buffer initialization         |

### 3. Component Tests (13 tests)

**Chunk Producer (6 tests)**

| Test                                   | Coverage                                     |
| :------------------------------------- | :------------------------------------------- |
| `test_generate_chunks_basic`           | Sliding window chunk generation (12 words)   |
| `test_generate_chunks_normalization`   | Text normalization during chunk creation     |
| `test_generate_chunks_metadata`        | Source section tracking in chunks            |
| `test_generate_chunks_multi_section`   | Chunks spanning multiple sections            |
| `test_generate_chunks_edge_minimum`    | Behavior with minimum word count             |
| `test_generate_chunks_empty`           | Empty input handling                         |

**Section Producer (3 tests)**

| Test                              | Coverage                                      |
| :-------------------------------- | :-------------------------------------------- |
| `test_extract_pdf_presentation`   | PyMuPDF slide text extraction                 |
| `test_extract_pdf_transcript`     | PyMuPDF transcript text extraction            |
| `test_extract_whitespace_handling` | Whitespace normalization in extracted text   |

**Similarity Calculator (4 tests)**

| Test                                  | Coverage                                      |
| :------------------------------------ | :-------------------------------------------- |
| `test_similarity_default_weights`     | Default 60% semantic + 40% phonetic weighting |
| `test_similarity_custom_weights`      | Configurable weight parameters                |
| `test_similarity_semantic_only`       | 100% semantic weight (phonetic disabled)      |
| `test_similarity_phonetic_only`       | 100% phonetic weight (semantic disabled)      |

### 4. Utility Tests (17 tests)

**Data Handler (4 tests)**

| Test                           | Coverage                                         |
| :----------------------------- | :----------------------------------------------- |
| `test_data_handler_read_write` | File I/O operations with UTF-8 encoding          |
| `test_data_handler_directory`  | Directory creation and path resolution           |
| `test_data_handler_utf8`       | Unicode character handling in files              |
| `test_data_handler_nonexistent` | Error handling for missing files                |

**ID Generator (3 tests)**

| Test                            | Coverage                                        |
| :------------------------------ | :---------------------------------------------- |
| `test_id_format`                | Correct format: `name-slug-xxxxx`               |
| `test_id_uniqueness`            | Different IDs for identical names               |
| `test_id_accent_normalization`  | Accent removal and ASCII transliteration        |

**Text Normalizer (4 tests)**

| Test                                | Coverage                                    |
| :---------------------------------- | :------------------------------------------ |
| `test_normalize_lowercase`          | Case normalization                          |
| `test_normalize_numbers_to_words`   | Number-to-word conversion (123 → "one...")  |
| `test_normalize_punctuation`        | Punctuation and special character removal   |
| `test_normalize_accents`            | Accent and diacritic removal                |

**Model Downloader (6 tests)**

| Test                                  | Coverage                                    |
| :------------------------------------ | :------------------------------------------ |
| `test_model_config_validation`        | Model configuration file validation         |
| `test_download_url_construction`      | URL building from configuration             |
| `test_download_file_creation`         | File download and storage                   |
| `test_download_checksum_verification` | Downloaded file integrity checks            |
| `test_download_retry_logic`           | Retry mechanism for failed downloads        |
| `test_download_error_handling`        | Network and filesystem error handling       |

## Testing Infrastructure

### Shared Fixtures (`conftest.py`)

**Purpose:** Provide reusable test components and mock hardware dependencies

**System Mocks:**

```python
# Mock audio device to enable headless testing
sys.modules["sounddevice"] = MagicMock()

# Mock keyboard controller for CI/CD compatibility
sys.modules["pynput"] = create_pynput_mock()
```

**Why Mocking is Necessary:**
- **CI/CD Environment:** No audio devices or keyboards in cloud runners
- **Reproducibility:** Eliminate hardware-dependent test failures
- **Speed:** Mocked operations are instantaneous
- **Isolation:** Test logic without external dependencies

**Common Fixtures:**

```python
@pytest.fixture
def temp_moves_dir(tmp_path, monkeypatch):
    """Provide isolated ~/.moves directory for each test"""
    test_dir = tmp_path / ".moves"
    test_dir.mkdir()
    monkeypatch.setenv("HOME", str(tmp_path))
    return test_dir

@pytest.fixture
def sample_sections():
    """Generate sample Section objects for testing"""
    return [
        Section(content="Introduction to the topic", section_index=0),
        Section(content="Main discussion points", section_index=1),
        Section(content="Conclusion and summary", section_index=2)
    ]

@pytest.fixture
def mock_llm_response():
    """Mock LLM API response for section generation tests"""
    # Returns pre-structured response avoiding actual API calls
```

### Test Isolation

**Per-Test Isolation:**
- Each test runs in clean environment
- Temporary file system via `tmp_path` fixture
- No cross-test state contamination
- Automatic cleanup after test completion

**Database/File System:**
- No persistent data between tests
- All file operations in temporary directories
- Settings and speakers created fresh per test
- Cleanup handled by pytest automatically

## Continuous Integration

### Automated Testing

**Triggers:**
- Every pull request
- Every commit to main branch
- Scheduled nightly runs (optional)

**Test Matrix:**
- Python 3.13 (primary)
- Multiple operating systems (Linux, macOS, Windows)
- Different dependency versions (if applicable)

### Coverage Goals

**Current Coverage:** ~85% of source code

**Coverage Reports:**
- Generated automatically in CI
- HTML report available as artifact
- Line-by-line coverage visualization
- Uncovered code highlighted for attention

**Coverage Targets by Module:**

| Module                  | Target | Current | Notes                       |
| :---------------------- | :----- | :------ | :-------------------------- |
| CLI (`main.py`)         | 80%    | 82%     | Good integration coverage   |
| Core Modules            | 90%    | 88%     | High business logic coverage |
| Components              | 85%    | 87%     | Algorithmic code well-tested |
| Utilities               | 95%    | 93%     | Simple functions, easy to test |

## Test Development Guidelines

### Writing New Tests

**1. Test Naming:**
```python
# Good: Descriptive, indicates what and why
def test_speaker_add_creates_directory_with_metadata():
    pass

# Bad: Vague, doesn't indicate purpose
def test_speaker_1():
    pass
```

**2. Test Structure (Arrange-Act-Assert):**
```python
def test_chunk_generation_spans_multiple_sections():
    # Arrange: Set up test data
    sections = create_test_sections()
    
    # Act: Execute functionality
    chunks = generate_chunks(sections, window_size=12)
    
    # Assert: Verify results
    assert len(chunks) > 0
    assert any(len(c.source_sections) > 1 for c in chunks)
```

**3. Edge Cases:**
- Test boundary conditions
- Test empty inputs
- Test maximum/minimum values
- Test error conditions

**4. Isolation:**
- No dependencies between tests
- Mock external services
- Use fixtures for shared setup
- Clean up resources

### Running Tests During Development

**Fast Feedback Loop:**
```bash
# Run only tests for module you're working on
uv run pytest tests/test_cli.py -v

# Run specific test repeatedly
uv run pytest tests/test_cli.py::test_speaker_add -vv

# Run with print statements visible
uv run pytest -s

# Stop at first failure for quick debugging
uv run pytest -x
```
