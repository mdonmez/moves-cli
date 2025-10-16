# System Architecture

## Design Philosophy

The `moves` system follows a dual-phase architecture that separates offline data preparation from real-time presentation control. This design ensures optimal performance during live presentations by completing all computationally intensive processing beforehand.

The system is organized into four distinct architectural layers:
1. **Command-Line Interface (CLI)** - User interaction layer
2. **Data Management Layer** - File system and configuration handling
3. **Data Preparation Pipeline** - Offline AI-powered data processing
4. **Real-time Control Engine** - Live presentation navigation

## System Components

### 1. Command-Line Interface (CLI)

The CLI serves as the exclusive entry point for user interactions with the system. Built with the [Typer](https://typer.tiangolo.com/) library, it provides a clean, structured interface for all operations.

**Key Responsibilities:**
- **Input Validation:** Verifies file paths, speaker identifiers, and configuration parameters before execution
- **Workflow Orchestration:** Coordinates operations across different manager classes
- **User Feedback:** Provides clear, actionable feedback for successful operations and error conditions
- **Command Routing:** Translates user commands into appropriate manager method calls

The CLI is implemented in `main.py` and exposes three primary command groups: `speaker`, `presentation`, and `settings`.

### 2. Data Management Layer

This foundational layer manages all file system operations and configuration, ensuring data integrity and system consistency. All data is stored within the sandboxed `~/.moves` directory.

#### Settings Management (`SettingsEditor`)

Manages global configuration in `~/.moves/settings.toml` using the `tomlkit` library for TOML parsing and writing.

**Features:**
- **Template-Based Configuration:** Merges a system template (`settings_template.toml`) with user settings, preserving comments and structure
- **Initialization:** On first run, copies the template to the user's data directory; on subsequent runs, merges template defaults with user values
- **Validation:** Ensures all configuration keys are valid and properly typed

**Configuration Parameters:**
- `model` - LLM model identifier (e.g., `openai/gpt-4o-mini`)
- `key` - API key for the selected LLM provider

#### Speaker Management (`SpeakerManager`)

Orchestrates the complete lifecycle of speaker profiles, from creation to deletion.

**Profile Structure:**
Each speaker profile resides in a unique directory: `~/.moves/speakers/<speaker_id>/`

**Directory Contents:**
- `speaker.json` - Profile metadata (name, ID, source file paths)
- `presentation.pdf` - Local copy of the presentation file
- `transcript.pdf` - Local copy of the transcript file
- `sections.json` - Processed data output (indicates "Ready" status)

**Resolution Logic:**
The `resolve()` method accepts either a speaker name or unique ID. When multiple speakers share the same name, it prompts the user to specify the exact speaker ID.

#### File System Abstraction (`data_handler`)

A critical utility that centralizes all file system operations and enforces the security sandbox.

**Security Features:**
- All file paths are resolved relative to `~/.moves`
- Prevents access to files outside the designated data folder
- Provides consistent error handling for I/O operations
- Ensures UTF-8 encoding for all text operations

### 3. Data Preparation Pipeline

This offline pipeline transforms raw PDF inputs into structured, optimized data for real-time analysis. Triggered by `moves speaker process`, the pipeline is idempotent and can be re-run to update speaker data.

#### Section Production (`section_producer`)

The AI-powered semantic alignment stage that segments transcripts to match presentation slides.

**Process Flow:**

1. **PDF Text Extraction** (via `PyMuPDF`):
   - **Presentation:** Extracts text page-by-page, preserving slide structure for topical guidance
   - **Transcript:** Extracts complete text as a continuous narrative for segmentation

2. **LLM-Powered Alignment:**
   - **Technology Stack:**
     - `litellm` - Provides a universal API for multiple LLM providers (OpenAI, Gemini, etc.)
     - `instructor` - Enforces structured Pydantic output models with automatic validation and retry logic
   
   - **Output Validation:** The `SectionsOutputModel` Pydantic model ensures:
     - Exactly one section per presentation slide
     - Proper data types and constraints
     - Automatic retry if LLM output is malformed

3. **Prompt Engineering:**
   The system prompt (`llm_instruction.md`) defines strict alignment rules:
   - **One-to-One Mapping:** Generate exactly one text segment per slide
   - **Source Authority:** Extract content exclusively from the transcript
   - **Semantic Focus:** Match slide topics to transcript content, ignoring superficial elements
   - **Fallback Strategy:** If a slide topic is absent from the transcript, synthesize a brief, contextually appropriate sentence

4. **Output Persistence:**
   Validated sections are serialized to `sections.json` in the speaker's directory, marking the profile as ready for presentation.

#### Chunk Production (`chunk_producer`)

Transforms sections into overlapping text segments optimized for real-time similarity matching.

**Sliding Window Algorithm:**

1. **Word Corpus Construction:**
   - Tokenizes all section content into tuples: `(word, source_section)`
   - Maintains metadata linking each word to its originating section

2. **Window Iteration:**
   - Default window size: 12 words
   - Slides one word at a time across the entire corpus
   - Creates overlapping chunks from position 0 to `(n - window_size)`

3. **Chunk Object Creation:**
   Each chunk contains:
   - `partial_content` - Normalized 12-word text segment
   - `source_sections` - Sorted list of sections the chunk spans (by `section_index`)

**Design Benefits:**
- **Granularity:** Short phrases enable precise matching
- **Overlap:** Increases match probability for varied speech delivery
- **Performance:** Real-time comparison against small text segments is computationally efficient
- **Resilience:** Handles out-of-order delivery and ad-libbed content

### 4. Real-time Control Engine

Activated by `moves presentation control`, this engine manages live voice-controlled presentations using a multi-threaded architecture for non-blocking, responsive performance.

#### Streaming Speech-to-Text (STT)

**Technology:**
- **Library:** `sherpa-onnx` - High-performance offline speech recognition using ONNX Runtime
- **Model:** Pre-trained Nemo transducer model optimized for streaming applications
- **Decoding:** Greedy search algorithm for minimal latency (selects most probable token at each step)

**Multi-Threaded Audio Pipeline:**

1. **Audio Capture (Main Thread):**
   - `sounddevice` library captures audio from the default microphone
   - 100ms frames at 16,000 Hz sample rate
   - Registered callback function processes each frame

2. **Asynchronous Buffering:**
   - Audio frames are placed in a thread-safe `deque` buffer
   - Decouples high-priority audio capture from STT processing
   - Handles variable workload without blocking

3. **STT Processing (Dedicated Thread):**
   - Continuously pulls frames from the `deque`
   - Feeds audio to `OnlineRecognizer` via `accept_waveform()`
   - Incremental processing: `is_ready()` → `decode_stream()` → `get_result()`
   - Outputs raw transcribed text

4. **Text Normalization:**
   - Applies `text_normalizer` to ensure format matches pre-processed chunks
   - Maintains sliding window of 12 most recent normalized words
   - Passes normalized text to similarity calculator

#### Similarity Calculation (`SimilarityCalculator`)

The core real-time analysis component that determines slide transitions.

**Hybrid Scoring Model:**

1. **Semantic Similarity:**
   - **Technology:** `fastembed` library with `all-MiniLM-l6-v2` embedding model
   - **Process:** Generates vector embeddings for spoken text and candidate chunks
   - **Metric:** Cosine similarity between vectors (measures semantic closeness)

2. **Phonetic Similarity:**
   - **Technology:** `jellyfish` (Metaphone encoding) + `rapidfuzz` (fuzzy matching)
   - **Process:**
     - Generate phonetic keys for both texts (e.g., "phonetics" → "FNTKS")
     - Calculate Levenshtein distance-based similarity
     - Normalize to 0.0-1.0 scale
   - **Purpose:** Resilience to homophones and pronunciation errors
   - **Optimization:** LRU caching for recently heard phrases

3. **Score Normalization and Weighting:**
   - **Normalization:** Independent min-max scaling for semantic and phonetic scores
     - Filters scores below 0.5 confidence threshold
     - Maps remaining scores to 0.0-1.0 range within candidate set
   - **Weighted Combination:** Default weights: 60% semantic + 40% phonetic
   - **Output:** Sorted list of `SimilarityResult` objects by final weighted score

**Candidate Chunk Selection:**
- **Look-ahead/Look-behind Window:** Current slide ± contextual range
  - Range: `[current_index - 2, current_index + 3]`
- **Filtering Strategy:**
  - Include chunks where all source sections fall within window
  - Exclude single-section chunks at window edges (prevents premature matching)

#### Presentation Navigation

**Navigation Logic:**
1. Identifies chunk with highest similarity score
2. Determines target slide from chunk's last source section
3. Calculates navigation delta: `target_slide - current_slide`
4. Simulates keyboard events via `pynput` (e.g., Right Arrow keypresses)

**Manual Override:**
- Parallel `pynput` keyboard listener thread monitors user input
- Supports pause/resume and manual navigation
- Allows complete user control at any time

**Thread Architecture:**
- Main thread: Audio capture and system coordination
- STT thread: Speech recognition processing
- Navigator thread: Similarity calculation and navigation
- Listener thread: Keyboard input monitoring
