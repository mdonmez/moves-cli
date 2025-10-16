# Technical Deep Dive

This section provides comprehensive technical documentation of the `moves` system's internal architecture, implementation details, and design decisions. Each document explores a specific component or concept in depth.

## Core System Components

### [Speaker Management](speaker-management.md)
Explores the Speaker entity, its data structure, file system storage, and complete lifecycle management by the `SpeakerManager`. Covers profile creation, modification, asynchronous processing, and resolution logic.

### [Settings Management](editing-settings.md)
Details the configuration system, including TOML-based settings storage, template merging, validation, and the role of `tomlkit` in preserving file structure and comments.

## Data Processing Pipeline

### [Section Generation](sections.md)
Examines the LLM-powered semantic alignment process that segments speaker transcripts to match presentation slides. Covers PDF extraction, structured prompting, output validation via `instructor`, and the alignment task specification.

### [Chunk Generation](chunks.md)
Analyzes the sliding window algorithm that creates overlapping text chunks from sections. Explains the rationale, chunk object structure, and candidate chunk selection logic for real-time matching.

## Real-Time Control Components

### [Similarity Calculations](similarity-calculations.md)
Dissects the hybrid similarity engine combining semantic vector comparison and phonetic key matching. Details score normalization, weighting strategy, and the mathematical approach to determining slide transitions.

### [Streaming Speech-to-Text](streaming-stt.md)
Investigates the low-latency, multi-threaded audio processing pipeline. Covers the `sherpa-onnx` transducer model, greedy search decoding, audio buffering, and text normalization for matching.

## Data and Infrastructure

### [Data Models](data-models.md)
Documents the core data structures (`Speaker`, `Section`, `Chunk`, `SimilarityResult`, etc.) and their roles in facilitating information flow throughout the system.

### [Utilities](utilities.md)
Describes essential helper modules: sandboxed file handling (`data_handler`), canonical text normalization (`text_normalizer`), unique ID generation (`id_generator`), and component-isolated logging.

## Quality Assurance

### [Test System](tests.md)
Outlines the comprehensive test suite covering CLI workflows, core business logic, data processing components, and utility functions. Details test organization, coverage areas, and mocking strategies for hardware dependencies.
