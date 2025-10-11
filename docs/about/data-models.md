# Data Models

The `moves` system employs a series of strongly-typed data structures, primarily implemented as `dataclasses`, to ensure clarity, type safety, and predictable data flow throughout the application's lifecycle.

### `Speaker`

This is the central entity representing a user's presentation profile. It is serialized to `speaker.json` for persistence and managed exclusively by the `SpeakerManager`.

- **`name` (str):** The user-provided, human-readable name for the profile.
- **`speaker_id` (SpeakerId):** A unique, URL-safe identifier generated from the name, used as the primary key and directory name for storing all related data.
- **`source_presentation` (Path):** An absolute path to the user's original presentation PDF. This path is stored to allow for easy re-processing if the source file is updated.
- **`source_transcript` (Path):** An absolute path to the user's original transcript PDF.

### `Section`

A `Section` represents a contiguous block of the transcript that has been semantically aligned with a single presentation slide by the LLM. It is the primary output of the `section_producer` and the foundational input for the `chunk_producer`.

- **`content` (str):** The textual content of the transcript segment.
- **`section_index` (int):** The zero-based index corresponding to the slide/page number in the presentation, ensuring a direct one-to-one mapping.

### `Chunk`

A `Chunk` is the atomic unit for real-time similarity comparison. It is a small, normalized text snippet designed for efficient matching. These are generated offline and loaded into memory during a live session.

- **`partial_content` (str):** An overlapping segment of text, typically 12 words long, extracted from `Section` content via a sliding window and passed through the `text_normalizer`.
- **`source_sections` (list[Section]):** A sorted list of the source `Section`(s) from which the `partial_content` originates. This metadata is the crucial link that allows the system to trace a high-scoring chunk back to its target slide.

### `SimilarityResult`

A transient data object created in-memory during the real-time navigation loop. It encapsulates the outcome of a single comparison between live speech and a candidate `Chunk`.

- **`chunk` (Chunk):** The candidate chunk that was evaluated.
- **`score` (float):** The final, normalized, and weighted similarity score, representing the confidence of the match. The list of these objects is sorted to find the best match.

### `Settings`

An in-memory representation of the `~/.moves/settings.toml` configuration file. It provides typed access to application-wide parameters.

- **`model` (str):** The `litellm`-compatible string identifying the LLM used for section generation.
- **`key` (str):** The API key associated with the specified LLM provider.

### `ProcessResult`

A data transfer object used solely to convey the outcome of the `SpeakerManager.process` operation back to the CLI for user feedback.

- **`section_count` (int):** The total number of `Section` objects successfully generated.
- **`transcript_from` / `presentation_from` (Literal["SOURCE", "LOCAL"]):** Status flags indicating whether the processing used the user's original source files or existing local copies within the speaker's data directory.
