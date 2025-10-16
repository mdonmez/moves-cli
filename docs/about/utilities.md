# Utility Modules

The `moves` project includes essential utility modules in `src/moves_cli/utils/` that handle cross-cutting concerns. These utilities enforce consistency, abstract complex operations, and improve maintainability across the codebase.

## Data Handler (`data_handler`)

### Purpose

Provides a sandboxed interface for all file system operations, ensuring data security and consistent path management.

### Security Model

**Sandboxed Environment:**
- All operations confined to `~/.moves` directory
- Prevents accidental access to files outside data folder
- Centralizes file system interactions for audit and control

**Path Resolution:**
```python
DATA_FOLDER = Path.home() / ".moves"

def resolve_path(relative_path: str) -> Path:
    """Convert relative path to absolute path within DATA_FOLDER"""
    return (DATA_FOLDER / relative_path).resolve()
```

### Core Functions

**`read(file_path: Path) -> str`**
- Read file contents as UTF-8 encoded string
- Returns entire file content
- Raises `FileNotFoundError` if file doesn't exist
- Handles encoding errors gracefully

**`write(file_path: Path, content: str) -> None`**
- Write UTF-8 encoded string to file
- Creates parent directories if needed (`mkdir(parents=True)`)
- Overwrites existing file content
- Atomic write using temp file + rename (on supported systems)

**`exists(file_path: Path) -> bool`**
- Check if file or directory exists
- Returns boolean without raising exceptions
- Useful for conditional logic

**`delete(file_path: Path) -> None`**
- Remove file or directory
- Recursive deletion for directories (`rmtree`)
- No error if file doesn't exist

**`list_dir(dir_path: Path) -> list[Path]`**
- List all items in directory
- Returns list of Path objects
- Empty list if directory doesn't exist

### Usage Examples

```python
from moves_cli.utils import data_handler

# Write configuration
settings_path = data_handler.DATA_FOLDER / "settings.toml"
data_handler.write(settings_path, "model = 'openai/gpt-4o-mini'")

# Read speaker metadata
speaker_json = data_handler.DATA_FOLDER / "speakers" / "john-doe-xyz" / "speaker.json"
content = data_handler.read(speaker_json)

# Check if sections exist
sections_path = data_handler.DATA_FOLDER / "speakers" / speaker_id / "sections.json"
is_ready = data_handler.exists(sections_path)
```

### Benefits

- **Security:** Prevents directory traversal attacks
- **Consistency:** All file operations use UTF-8 encoding
- **Maintainability:** Centralized error handling
- **Portability:** Abstracts OS-specific path handling

## Text Normalizer (`text_normalizer`)

### Purpose

Ensures consistent text formatting between pre-processed chunks and real-time STT output, enabling accurate similarity matching.

### Normalization Pipeline

The `normalize_text(text: str) -> str` function applies a sequence of transformations:

**1. Unicode Normalization (NFD)**
```python
text = unicodedata.normalize("NFD", text.lower())
```
- Decomposes characters into base + combining marks
- Example: "é" → "e" + combining acute accent
- Enables subsequent accent removal

**2. Lowercase Conversion**
- Eliminates case sensitivity
- "Hello World" → "hello world"

**3. Accent and Diacritic Removal**
```python
text = "".join(c for c in text if unicodedata.category(c) != "Mn")
```
- Removes combining marks (category "Mn")
- "café" → "cafe"
- "naïve" → "naive"

**4. Emoji Removal**
- Strips all emoji characters using Unicode ranges
- Prevents emoji from interfering with text matching
- Regex pattern covers common emoji blocks

**5. Smart Quote Normalization**
```python
text = text.translate(str.maketrans({
    "'": "'", "'": "'", "‚": "'", "‛": "'",
    """: '"', """: '"', "„": '"', "‟": '"'
}))
```
- Converts typographic quotes to ASCII equivalents
- Ensures consistent quote character encoding

**6. Number-to-Word Conversion**
```python
text = re.sub(r"\d+", lambda m: num2words(m.group(0)).replace("-", " "), text)
```
- Converts all numeric digits to words
- "123" → "one hundred twenty three"
- "2024" → "two thousand twenty four"
- Critical because STT outputs words, PDFs often contain digits

**7. Punctuation Removal**
```python
text = re.sub(r"[^\w\s'\"`]", " ", text, flags=re.UNICODE)
```
- Removes most punctuation except apostrophes and quotes
- Preserves contractions ("don't", "we'll")
- Simplifies text for matching

**8. Whitespace Consolidation**
```python
text = re.sub(r"\s+", " ", text).strip()
```
- Multiple spaces → single space
- Removes leading/trailing whitespace
- Ensures consistent word separation

### Examples

```python
from moves_cli.utils import text_normalizer

# Complex input
input_text = "The Total is $1,234.56 — That's 50% More!"

# After normalization
output = text_normalizer.normalize_text(input_text)
# Result: "the total is one thousand two hundred thirty four point five six thats fifty percent more"

# Unicode and accents
input_text = "Café Niño: €15.99"
output = text_normalizer.normalize_text(input_text)
# Result: "cafe nino fifteen point nine nine"
```

### Why This Matters

**Consistency:**
- Chunks and live speech processed identically
- Eliminates false negatives from format differences

**Robustness:**
- Handles PDF extraction artifacts
- Compensates for STT variations
- Tolerates input diversity

**Accuracy:**
- Number conversion aligns with STT behavior
- Accent removal handles speaker variations
- Case insensitivity prevents trivial mismatches

## ID Generator (`id_generator`)

### Purpose

Creates unique, file-system-safe identifiers for speaker profiles, ensuring no collisions even when multiple speakers share the same name.

### ID Format

**Pattern:** `name-slug-xxxxx`

**Components:**
- **Name Slug:** URL-safe derivative of speaker name
- **Random Suffix:** 5-character cryptographic random string

**Example Transformations:**

| Speaker Name      | Generated ID                |
| :---------------- | :-------------------------- |
| "John Doe"        | `john-doe-a7k3m`            |
| "María García"    | `maria-garcia-x9p2q`        |
| "Dr. Smith"       | `dr-smith-b4n8t`            |
| "John Doe"        | `john-doe-z2w5r` (different) |

### Generation Algorithm

**Function:** `generate_speaker_id(name: str) -> str`

**Step 1: Unicode Normalization**
```python
name = unicodedata.normalize("NFKD", name)
```
- NFKD: Compatibility decomposition
- Separates base characters from diacritics
- "é" → "e" + combining acute

**Step 2: ASCII Encoding**
```python
name = name.encode("ascii", "ignore").decode("ascii")
```
- Convert to ASCII, ignoring non-ASCII characters
- "María" → "Maria"
- "naïve" → "naive"

**Step 3: Slug Creation**
```python
slug = re.sub(r"[^a-z0-9]+", "-", name.lower())
slug = slug.strip("-")
```
- Lowercase conversion
- Replace non-alphanumeric with hyphens
- Remove leading/trailing hyphens
- "Dr. Smith" → "dr-smith"

**Step 4: Random Suffix**
```python
import secrets
random_suffix = secrets.token_urlsafe(4)[:5]
```
- Cryptographically secure random string
- URL-safe character set: [A-Za-z0-9_-]
- 5 characters provide ~30 bits of entropy
- Collision probability: ~1 in 1 billion for 1000 speakers

**Step 5: Combination**
```python
speaker_id = f"{slug}-{random_suffix}"
```

### Properties

**URL-Safe:**
- No special characters requiring encoding
- Safe for use in file paths, URLs, database keys

**Uniqueness:**
- Random suffix prevents collisions
- Multiple "John Doe" speakers have distinct IDs
- No need to track existing IDs during generation

**Readability:**
- Human-readable name component
- Easy to identify speaker from ID
- Suitable for display in UI/CLI

**File-System Safe:**
- Valid directory name on all major OSes
- No reserved characters (/, \, :, *, ?, ", <, >, |)
- Compatible with Windows, Linux, macOS

### Usage

```python
from moves_cli.utils import id_generator

# Generate ID for new speaker
speaker_id = id_generator.generate_speaker_id("María García")
# Result: "maria-garcia-x9p2q"

# Use as directory name
speaker_dir = Path("~/.moves/speakers") / speaker_id
speaker_dir.mkdir(parents=True, exist_ok=True)
```

## Model Downloader (`model_downloader`)

### Purpose

Manages automatic downloading of ML models (STT and embedding) required for presentation control.

### Model Configuration

**Configuration File:** `src/moves_cli/data/model_config.toml`

**Structure:**
```toml
[models.stt]
name = "nemo-streaming-stt-480ms-int8"
base_url = "https://github.com/..."
files = [
    "tokens.txt",
    "encoder.int8.onnx",
    "decoder.int8.onnx",
    "joiner.int8.onnx"
]
checksums = {
    "tokens.txt" = "sha256:abc...",
    # ...
}

[models.embedding]
name = "all-MiniLM-l6-v2"
# Handled by fastembed library automatically
```

### Download Process

**Function:** `download_model(model_type: str) -> None`

**Flow:**

1. **Check Existing Installation**
   ```python
   model_dir = DATA_FOLDER / "ml_models" / model_name
   if model_dir.exists() and all_files_present:
       return  # Skip download
   ```

2. **Create Directory Structure**
   ```python
   model_dir.mkdir(parents=True, exist_ok=True)
   ```

3. **Download Files**
   ```python
   for file in config.files:
       url = f"{config.base_url}/{file}"
       download_file(url, model_dir / file)
   ```

4. **Verify Checksums** (if provided)
   ```python
   if config.checksums:
       verify_sha256(file_path, expected_checksum)
   ```

5. **Mark Complete**
   ```python
   (model_dir / ".download_complete").touch()
   ```

### Error Handling

**Network Errors:**
- Retry logic: 3 attempts with exponential backoff
- Clear error messages indicating network issues
- Suggestion to check internet connection

**Disk Space:**
- Check available space before download
- Models require ~100-500MB each
- Abort if insufficient space

**Corrupted Downloads:**
- Checksum verification detects corruption
- Automatic re-download on checksum mismatch
- Preserve partial downloads in temp directory

**Partial Downloads:**
- Resume support for large files (if server supports)
- Clean up incomplete downloads on failure
- Track download progress for user feedback

### User Experience

**First-Time Use:**
```
Loading speech recognition models (this may take a while)...
Downloading nemo-streaming-stt-480ms-int8...
  ├─ tokens.txt (1.2 MB)... Done
  ├─ encoder.int8.onnx (45.3 MB)... Done
  ├─ decoder.int8.onnx (12.1 MB)... Done
  └─ joiner.int8.onnx (8.7 MB)... Done
Models loaded successfully!
```

**Subsequent Uses:**
- Instant startup (no download)
- Models cached in `~/.moves/ml_models/`
- Automatic verification on each load

## Logging Utility (`logger`)

### Purpose

Provides structured, component-isolated logging for debugging and troubleshooting.

### Dynamic Module Detection

**Automatic Log File Naming:**
```python
import inspect

# Get calling module filename
frame = inspect.stack()[1]
module_file = Path(frame.filename).stem

# Create log file
log_file = DATA_FOLDER / "logs" / f"{module_file}.log"
```

**Result:**
- `speaker_manager.log` for SpeakerManager
- `presentation_controller.log` for PresentationController
- `section_producer.log` for section_producer

### Log Configuration

**Format:**
```
2024-10-16 17:20:38 [INFO] SpeakerManager: Created speaker john-doe-a7k3m
2024-10-16 17:20:45 [WARNING] SectionProducer: LLM call took 12.3 seconds
2024-10-16 17:21:02 [ERROR] PresentationController: Microphone not available
```

**Components:**
- Timestamp (ISO 8601 format)
- Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Module name
- Message

### Rotating File Handler

**Configuration:**
```python
handler = RotatingFileHandler(
    log_file,
    maxBytes=10 * 1024 * 1024,  # 10 MB
    backupCount=5                # Keep 5 old logs
)
```

**Benefits:**
- Prevents log files from growing unbounded
- Automatically rotates when 10MB reached
- Keeps 5 most recent log files
- Archives: `module.log.1`, `module.log.2`, etc.

### Log Levels

**DEBUG:** Detailed diagnostic information
```python
logger.debug(f"Processing chunk {i}/{total_chunks}")
```

**INFO:** General informational messages
```python
logger.info(f"Speaker '{speaker.name}' processed successfully")
```

**WARNING:** Warning messages for non-critical issues
```python
logger.warning(f"Source file not found, using local copy")
```

**ERROR:** Error conditions that need attention
```python
logger.error(f"LLM API call failed: {error}")
```

**CRITICAL:** Critical errors causing system failure
```python
logger.critical(f"Cannot initialize STT model: {error}")
```

### Usage Example

```python
from moves_cli.utils.logger import Logger

logger = Logger(__name__)

logger.info("Starting speaker processing")
try:
    process_speaker(speaker)
    logger.info("Processing complete")
except Exception as e:
    logger.error(f"Processing failed: {e}", exc_info=True)
```

### Benefits

- **Component Isolation:** Each module has dedicated log file
- **Debugging:** Detailed trace of execution flow
- **Troubleshooting:** Error messages with context
- **Performance Analysis:** Timing information for operations
- **Audit Trail:** Historical record of system operations
