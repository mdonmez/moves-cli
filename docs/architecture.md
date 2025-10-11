# Architecture

The `moves` system is architected around a distinct separation of concerns, dividing its operation into an offline data preparation pipeline and a real-time presentation control engine. This dual-phase design maximizes live performance by pre-processing all computationally intensive tasks. The architecture is layered, comprising a Command-Line Interface (CLI), a Data Management Layer, a Data Preparation Pipeline, and a Real-time Control Engine.

## System Components

### 1. Command-Line Interface (CLI)

The CLI, built with the Typer library, serves as the exclusive user-facing entry point. It translates user commands, arguments, and options into calls to the underlying manager classes. It is responsible for validating user input (e.g., file paths), orchestrating the application's workflow, and providing structured, informative feedback to the user.

### 2. Data Management Layer

This foundational layer governs all file system interactions within the sandboxed `~/.moves` directory, ensuring data integrity and consistency.

- **Settings Management (`SettingsEditor`):** Manages global configurations stored in `~/.moves/settings.toml`. It utilizes the `tomlkit` library to parse and write settings, which preserves comments and file structure from the system template. On initialization, it merges the default template with the user's settings, ensuring robustness and providing a clear configuration schema.
- **Speaker Management (`SpeakerManager`):** Orchestrates the lifecycle of speaker profiles. Each speaker is assigned a unique directory (`~/.moves/speakers/<speaker_id>/`) containing their metadata (`speaker.json`), local copies of their source files, and the processed `sections.json` data. The manager implements logic to resolve speaker profiles from either a unique ID or a name, handling potential ambiguities when multiple speakers share the same name.
- **File System Abstraction (`data_handler`):** A critical utility that centralizes all file system operations. It ensures that all file paths are resolved relative to the `~/.moves` root directory, creating a secure sandbox that prevents the application from accessing or modifying files outside its designated data folder.

### 3. Data Preparation Pipeline

This offline pipeline, triggered by the `moves speaker process` command, transforms raw user inputs (PDFs) into a structured data format optimized for real-time analysis. The process is designed to be idempotent and can be re-run to update a speaker's data.

- **Section Production (`section_producer`):** This is the first and most intelligent stage. It employs `PyMuPDF` for raw text extraction from the presentation and transcript. The core of this component is its interaction with a Large Language Model (LLM) through `litellm` (providing a universal API) and `instructor`. `instructor` enforces a Pydantic data model on the LLM's output, guaranteeing that the response is a well-structured list of sections that exactly matches the number of presentation slides. The LLM is guided by a sophisticated system prompt that instructs it to perform a semantic alignment task: segmenting the monolithic transcript into "Sections," each corresponding to the core topic of a single slide.
- **Chunk Production (`chunk_producer`):** This stage consumes the `sections.json` file to produce "Chunks." A sliding window algorithm moves across the entire corpus of section text, one word at a time, creating overlapping text segments of a fixed length (e.g., 12 words). Each chunk retains metadata linking it back to its source sections. This process creates a highly granular and redundant dataset that is resilient to variations in spoken delivery.

### 4. Real-time Control Engine

Activated by the `moves presentation control` command, this engine manages the live, voice-controlled session using a multi-threaded architecture to ensure non-blocking performance.

- **Streaming Speech-to-Text (STT):** An `OnlineRecognizer` from the `sherpa-onnx` library, configured with a local Nemo transducer model, performs continuous, low-latency transcription. Audio is captured in 100ms frames by `sounddevice`, buffered in a `deque`, and fed to the recognizer in a dedicated thread.
- **Similarity Calculation (`SimilarityCalculator`):** This component performs the core real-time analysis. For each new phrase transcribed by the STT engine, it compares the phrase against a dynamically selected subset of "candidate chunks." The comparison is a hybrid model:
  - **Semantic Similarity:** The `fastembed` library generates vector embeddings for the spoken text and candidate chunks using the `all-MiniLM-l6-v2` model. The cosine similarity between these vectors is calculated to evaluate closeness in meaning.
  - **Phonetic Similarity:** The `jellyfish` library generates Metaphone phonetic keys for the text, and `rapidfuzz` calculates the similarity ratio between these keys. This provides resilience to homophones and minor pronunciation errors.
  - **Weighted Scoring:** Raw scores from both methods are independently normalized using a min-max scaling algorithm after filtering out low-confidence initial matches. These normalized scores are then combined into a final score using configurable weights, providing a balanced assessment of similarity.
- **Presentation Navigation:** The engine identifies the chunk with the highest final similarity score. It determines the target slide by examining the last source section associated with that chunk. The difference between the target and current slide indices dictates the required navigation (e.g., a positive difference triggers Right Arrow key presses). The `pynput` library simulates these keyboard events. A parallel `pynput` listener thread concurrently monitors for manual keyboard input, allowing the user to override the automatic navigation or pause the system at any time.
