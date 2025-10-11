# Test System Documentation

## Test Execution

To run all tests:

```bash
uv run pytest
```

To run with verbose output:

```bash
uv run pytest -v
```

To run tests with coverage:

```bash
uv run pytest --cov=src --cov-report=html
```

## Test Structure

The test suite is organized to mirror the source code structure:

```
tests/
├── test_app.py                          # CLI application tests
├── test_presentation_controller.py      # Presentation controller tests
├── test_settings_editor.py              # Settings management tests
├── test_speaker_manager.py              # Speaker management tests
├── components/                          # Component tests
│   ├── test_chunk_producer.py
│   ├── test_section_producer.py
│   ├── test_similarity_calculator.py
│   └── similarity_units/
│       ├── test_phonetic.py
│       └── test_semantic.py
└── utils/                               # Utility tests
    ├── test_data_handler.py
    ├── test_id_generator.py
    └── test_text_normalizer.py
```

## Test Coverage by Module

### 1. CLI Application (`test_app.py`)

**Total Tests: 47**

Tests for the Typer-based command-line interface covering:

- **Speaker Commands** (31 tests)

  - `speaker add`: File validation, error handling, duplicate detection
  - `speaker edit`: Single/multiple file updates, validation
  - `speaker list`: Display formatting, empty states
  - `speaker show`: Detailed speaker information display
  - `speaker process`: Single/multiple/all speaker processing, LLM integration
  - `speaker delete`: Single/multiple/all speaker deletion

- **Settings Commands** (13 tests)

  - `settings list`: Display all settings, missing values
  - `settings set`: Model/API key configuration, validation
  - `settings unset`: Reset to defaults

- **Presentation Control** (1 test)

  - Error handling for missing speakers

- **Version Command** (2 tests)
  - Version display and error handling

**Key Testing Approaches:**

- Extensive mocking of managers and LLM dependencies
- File system operations using `tmp_path` fixtures
- Typer CLI testing with `CliRunner`
- Edge case handling for empty inputs and invalid states

---

### 2. Core Components

#### Speaker Manager (`test_speaker_manager.py`)

**Total Tests: 29**

Comprehensive testing of speaker lifecycle management:

- **Add Operations** (6 tests): File validation, ID generation, special characters
- **Edit Operations** (6 tests): Path updates, no-change scenarios
- **Resolve Operations** (8 tests): ID/name resolution, duplicate handling, error messages
- **List Operations** (6 tests): Empty/populated states, filtering, path conversion
- **Delete Operations** (4 tests): File removal, data cleanup
- **Integration Workflows** (3 tests): Complete CRUD workflows

**Testing Highlights:**

- JSON persistence validation
- Path resolution (relative to absolute)
- Duplicate name handling with unique IDs
- Case-sensitive name matching

#### Settings Editor (`test_settings_editor.py`)

**Total Tests: 30**

TOML-based settings management:

- **Initialization** (5 tests): File creation, default loading, merge behavior
- **Set Operations** (8 tests): Valid/invalid keys, persistence, type handling
- **Unset Operations** (8 tests): Default restoration, multi-key operations
- **Persistence** (4 tests): Cross-instance consistency, TOML validity, comments preservation
- **List Operations** (4 tests): Settings display, current values
- **Error Handling** (3 tests): Invalid types, readonly files
- **Integration** (3 tests): Complete workflows

**Testing Highlights:**

- Template merging with user settings
- TOML comment preservation
- Atomic file operations
- Cross-instance consistency

#### Presentation Controller (`test_presentation_controller.py`)

**Total Tests: 43**

Real-time presentation navigation system:

- **Initialization** (10 tests): Section setup, window size, frame duration
- **Audio Queue** (6 tests): Deque behavior, size limits, FIFO operations
- **Keyboard Controller** (4 tests): Controller/listener setup
- **Navigator State** (5 tests): Thread management, flags, daemon threads
- **Recent Words** (7 tests): Window tracking, deque management
- **Recognizer Setup** (5 tests): Model loading, stream creation
- **Edge Cases** (4 tests): Minimal sections, large datasets
- **Attributes** (16 tests): Complete attribute verification

**Testing Highlights:**

- Extensive mocking of ML models (OnlineRecognizer, sounddevice)
- Thread initialization without execution
- Lazy loading patterns
- State management validation

---

### 3. Processing Components

#### Chunk Producer (`test_chunk_producer.py`)

**Total Tests: 37**

Sliding window chunk generation:

- **Generate Chunks** (12 tests): Window sizes, normalization, edge cases
- **Source Section Tracking** (7 tests): Multi-section spans, sorting, uniqueness
- **Candidate Chunks** (9 tests): Range calculations, boundary handling
- **Integration** (5 tests): Complete workflows, special characters, large datasets

**Testing Highlights:**

- Sliding window algorithm validation
- Section boundary handling
- Text normalization verification
- Edge cases: empty sections, exact window sizes

#### Section Producer (`test_section_producer.py`)

**Total Tests: 31**

PDF extraction and LLM-based section generation:

- **Transcript Extraction** (6 tests): Multi-page handling, whitespace normalization
- **Presentation Extraction** (8 tests): Slide markers, page separation
- **Error Handling** (6 tests): Corrupt PDFs, nonexistent files
- **Conversion Functions** (7 tests): Section/dict conversion, round-trip validation
- **LLM Integration** (6 tests): Mocked generation, ordering
- **Integration** (3 tests): Real PDF handling, special characters

**Testing Highlights:**

- Real PDF creation with PyMuPDF
- Slide marker insertion
- LLM call mocking
- Exception wrapping with context

#### Similarity Calculator (`test_similarity_calculator.py`)

**Total Tests: 38**

Hybrid semantic-phonetic similarity scoring:

- **Initialization** (5 tests): Weight configuration, component creation
- **Weighting** (4 tests): Custom weights, zero-weight edge cases
- **Normalization** (5 tests): 0-1 range, relative order preservation
- **Threshold** (4 tests): 0.5 cutoff enforcement
- **Empty Candidates** (4 tests): Edge case handling
- **Result Format** (5 tests): Sorting, type validation
- **Error Handling** (3 tests): Exception wrapping, messages
- **Integration** (3 tests): Complete workflows, combined scoring

**Testing Highlights:**

- Dual-method weighting (60% semantic, 40% phonetic by default)
- Score normalization to [0, 1]
- Threshold filtering at 0.5
- Descending sort by score

---

### 4. Similarity Units

#### Phonetic Similarity (`test_phonetic.py`)

**Total Tests: 33**

Metaphone-based phonetic matching:

- **Similar Sounding** (6 tests): Homophones (write/right, knight/night)
- **Different Sounding** (4 tests): Unrelated words, opposite meanings
- **Caching** (6 tests): Result caching, cache hits
- **Result Format** (5 tests): SimilarityResult instances, sorting
- **Edge Cases** (7 tests): Empty inputs, special characters, unicode
- **Error Handling** (2 tests): Exception wrapping
- **Integration** (3 tests): Multi-comparison workflows

**Testing Highlights:**

- Homophone detection validation
- Cache efficiency verification
- Fuzzy ratio calculations
- Phonetic code generation

#### Semantic Similarity (`test_semantic.py`)

**Total Tests: 36**

FastEmbed-based semantic matching:

- **Model Loading** (6 tests): Lazy loading, single initialization
- **Similar Phrases** (4 tests): Synonyms, related concepts
- **Different Phrases** (3 tests): Unrelated concepts, opposites
- **Result Format** (6 tests): Cosine similarity, sorting
- **Edge Cases** (7 tests): Empty inputs, unicode, long text
- **Error Handling** (3 tests): Exception handling, empty embeddings
- **Integration** (4 tests): Model reuse, dimension consistency

**Testing Highlights:**

- Lazy model initialization
- Mock embedding generation
- Cosine similarity calculation
- Model path validation

---

### 5. Utilities

#### Data Handler (`test_data_handler.py`)

**Total Tests: 32**

File system operations wrapper:

- **Write/Read** (5 tests): File creation, unicode, multiline
- **Directory Creation** (2 tests): Nested directories
- **Error Handling** (4 tests): Missing files, permission errors
- **List Operations** (4 tests): Directory listing, sorting
- **Delete Operations** (5 tests): Files/directories, cleanup
- **Rename Operations** (3 tests): File renaming, overwriting
- **Copy Operations** (7 tests): Files/directories, recursive copy

**Testing Highlights:**

- Temporary directory fixtures
- Exception wrapping with context
- UTF-8 encoding enforcement
- Path resolution

#### ID Generator (`test_id_generator.py`)

**Total Tests: 8**

Unique identifier generation:

- **Speaker ID** (5 tests): Format validation, URL-safety, special characters
- **History ID** (1 test): Timestamp format
- **Suffix Generation** (2 tests): 5-character alphanumeric

**Testing Highlights:**

- URL-safe character validation
- Consistent format enforcement
- Timestamp-based IDs

#### Text Normalizer (`test_text_normalizer.py`)

**Total Tests: 4**

Text preprocessing:

- **Normalization** (4 tests): Lowercase, number-to-words, special characters, accents

**Testing Highlights:**

- inflect library integration
- Accent removal
- Special character stripping

---

## Other Details

### 1. Test Organization

Each test file follows a consistent structure:

```python
# Fixtures at the top
@pytest.fixture
def fixture_name():
    ...

# Test classes grouped by functionality
class TestFeatureName:
    def test_specific_behavior(self, fixtures):
        # Arrange
        # Act
        # Assert
```

### 2. Edge Case Coverage

All modules test:

- Empty inputs
- Single item inputs
- Large datasets
- Unicode characters
- Special characters
- Invalid types
- Missing files
- Permission errors
- Corrupt data

---

## Testing Dependencies

The test suite requires:

```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.4.1",
    "pytest-cov>=7.0.0",
    "pytest-mock>=3.15.1",
    "pytest-asyncio>=1.2.0",
    "pytest-timeout>=2.4.0"
]
```
