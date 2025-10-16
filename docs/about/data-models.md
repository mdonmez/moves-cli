# Data Models

The `moves` system uses strongly-typed data structures implemented as Python `dataclasses` to ensure type safety, clarity, and predictable data flow throughout the application lifecycle. All models are defined in `src/moves_cli/data/models.py`.

## Core Data Models

### `Speaker`

Represents a presentation profile containing all metadata and file references for a speaker.

**Storage:** Serialized to `speaker.json` in `~/.moves/speakers/<speaker_id>/`

**Attributes:**

| Field                 | Type       | Description                                                  |
| :-------------------- | :--------- | :----------------------------------------------------------- |
| `name`                | `str`      | User-provided, human-readable speaker name                   |
| `speaker_id`          | `SpeakerId` | Unique URL-safe identifier (format: `name-slug-xxxxx`)      |
| `source_presentation` | `Path`     | Absolute path to original presentation PDF file              |
| `source_transcript`   | `Path`     | Absolute path to original transcript PDF file                |

**Purpose:**
- Central entity for presentation management
- Managed exclusively by `SpeakerManager`
- Links user files to processed data
- Enables re-processing when source files are updated

### `Section`

Represents a semantically-aligned segment of transcript corresponding to a single presentation slide.

**Storage:** Array element in `sections.json`

**Attributes:**

| Field           | Type  | Description                                                     |
| :-------------- | :---- | :-------------------------------------------------------------- |
| `content`       | `str` | Textual content extracted from transcript for this slide        |
| `section_index` | `int` | Zero-based index corresponding to slide/page number (0 = slide 1) |

**Purpose:**
- Primary output of `section_producer` (LLM-powered alignment)
- Foundational input for `chunk_producer`
- One-to-one mapping with presentation slides
- Preserves chronological slide order

**Characteristics:**
- Immutable (`frozen=True` dataclass)
- Content length varies based on transcript density
- Index ensures deterministic slide targeting

### `Chunk`

The atomic unit for real-time similarity matching - a small, normalized text snippet optimized for efficient comparison.

**Storage:** Generated in-memory during presentation control; not persisted

**Attributes:**

| Field             | Type            | Description                                                      |
| :---------------- | :-------------- | :--------------------------------------------------------------- |
| `partial_content` | `str`           | Normalized 12-word text segment from section content             |
| `source_sections` | `list[Section]` | Sorted list of sections this chunk originates from (by `section_index`) |

**Purpose:**
- Enables rapid real-time similarity matching
- Provides metadata for slide navigation
- Created offline via sliding window algorithm
- Loaded into memory during presentation sessions

**Characteristics:**
- Immutable (`frozen=True` dataclass)
- Default size: 12 words (configurable window size)
- Overlapping: consecutive chunks share 11 words
- Can span multiple sections (cross-boundary chunks)
- Normalized text matches STT output format

### `SimilarityResult`

Encapsulates the outcome of comparing live speech against a candidate chunk.

**Storage:** Transient in-memory object created during navigation loop

**Attributes:**

| Field   | Type    | Description                                                |
| :------ | :------ | :--------------------------------------------------------- |
| `chunk` | `Chunk` | The candidate chunk that was evaluated                     |
| `score` | `float` | Final weighted similarity score (0.0-1.0 range)            |

**Purpose:**
- Represents single comparison result
- Enables sorting to find best match
- Links score to specific chunk for navigation
- Created by `SimilarityCalculator.compare()`

**Characteristics:**
- Immutable (`frozen=True` dataclass)
- Score combines semantic and phonetic similarities
- Sorted in descending order by score
- Highest score determines slide navigation

### `Settings`

In-memory representation of system configuration from `~/.moves/settings.toml`.

**Storage:** Loaded from TOML file on application start

**Attributes:**

| Field   | Type  | Description                                              |
| :------ | :---- | :------------------------------------------------------- |
| `model` | `str` | LiteLLM-compatible model identifier                      |
| `key`   | `str` | API key for the LLM provider                             |

**Purpose:**
- Provides typed access to configuration
- Used by `section_producer` for LLM calls
- Managed by `SettingsEditor`

**Example Values:**
- `model`: `"openai/gpt-4o-mini"`, `"gemini/gemini-2.0-flash"`
- `key`: `"sk-proj-..."`

### `ProcessResult`

Data transfer object conveying processing operation outcomes to the CLI.

**Storage:** Ephemeral; used only for user feedback

**Attributes:**

| Field                | Type                         | Description                                     |
| :------------------- | :--------------------------- | :---------------------------------------------- |
| `section_count`      | `int`                        | Number of sections successfully generated       |
| `transcript_from`    | `Literal["SOURCE", "LOCAL"]` | Source of transcript file used                  |
| `presentation_from`  | `Literal["SOURCE", "LOCAL"]` | Source of presentation file used                |

**Purpose:**
- Reports processing results to user
- Indicates file source for transparency
- Returned by `SpeakerManager.process()`

**Characteristics:**
- Immutable (`frozen=True` dataclass)
- Used exclusively for CLI feedback
- Helps users verify processing success

## Type Aliases

| Alias       | Underlying Type | Purpose                          |
| :---------- | :-------------- | :------------------------------- |
| `SpeakerId` | `str`           | Speaker unique identifier type   |
| `HistoryId` | `str`           | History record identifier type   |
