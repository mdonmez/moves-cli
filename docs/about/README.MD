# About `moves` - Technical Details

This section provides a granular, in-depth exploration of the internal architecture, operational logic, and key design decisions behind the `moves` system. Each document below details a specific component or concept, offering a comprehensive technical understanding of how the system functions from data preparation to live presentation control.

- **[Speaker Management](speaker-management.md):** Delves into the "Speaker" entity, detailing its data structure, storage on the file system, and the complete lifecycle managed by the `SpeakerManager`, including asynchronous processing.

- **[Section Generation](sections.md):** Explains the LLM-powered semantic alignment process that uses structured prompting and output modeling via `instructor` to intelligently segment speaker transcripts.

- **[Chunk Generation](chunks.md):** Provides a precise breakdown of the sliding window algorithm used to create overlapping text "Chunks" and the logic behind selecting a relevant subset of "candidate chunks" for real-time analysis.

- **[Similarity Calculations](similarity-calculations.md):** Outlines the hybrid analysis engine, detailing the semantic vector comparison, phonetic key matching, and the score normalization and weighting strategy.

- **[Streaming Speech-to-Text](streaming-stt.md):** Covers the low-latency, multi-threaded audio processing pipeline, including the role of the `sherpa-onnx` transducer model and the greedy search decoding method.

- **[Data Models](data-models.md):** Defines the core data structures (`Speaker`, `Section`, `Chunk`, etc.) and their roles in facilitating the flow of information throughout the system's different architectural layers.

- **[Editing Settings](editing-settings.md):** Explains the robust configuration management system, the role of the `tomlkit` library in preserving file structure, and the process of merging user settings with system defaults.

- **[Utilities](utilities.md):** Provides an overview of the essential helper modules responsible for sandboxed file handling, canonical text normalization, unique ID generation, and component-isolated logging.

- **[Test System](tests.md):** Documents the comprehensive test suite with 385 tests covering CLI commands, core components, processing logic, and utilities, including testing patterns, coverage analysis, and CI/CD integration guidelines.
