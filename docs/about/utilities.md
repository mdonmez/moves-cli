# Utilities

The `moves` project contains a suite of utility modules designed to handle common, cross-cutting concerns. These utilities enforce consistency, abstract complex operations, and improve the overall maintainability and robustness of the codebase.

### Data Handler (`data_handler`)

This module provides a sandboxed interface for all file system operations. All functions within this handler operate relative to the application's root data directory (`~/.moves`). This design prevents any component from accidentally accessing or modifying files outside of this designated area. It centralizes error handling for file I/O and simplifies path management for components like the `SpeakerManager` and `SettingsEditor`.

### Text Normalizer (`text_normalizer`)

This module is fundamental to the accuracy of the similarity matching engine. It provides a single function, `normalize_text`, that applies a consistent set of transformations to both the pre-processed `Chunk` content and the real-time STT output. This ensures that comparisons are made on a level playing field. The normalization pipeline includes:

- **Unicode NFC Normalization:** Standardizes character composition.
- **Lowercase Conversion:** Eliminates case sensitivity.
- **Special Character and Punctuation Removal:** Strips all symbols except for essential apostrophes and quotes to simplify the text.
- **Number-to-Word Conversion:** Utilizes the `num2words` library to convert all numerical digits into their full-text English equivalents (e.g., "123" becomes "one hundred twenty three"). This is a critical step, as STT engines typically output words, whereas source PDFs often contain digits.
- **Whitespace Consolidation:** Collapses all sequential whitespace characters into a single space.

### ID Generator (`id_generator`)

This utility is responsible for creating unique, file-system-safe identifiers for speaker profiles. The `generate_speaker_id` function performs two key steps:

1.  It processes the user-provided name by first normalizing it with `unicodedata.normalize("NFKD", ...)` to decompose characters and then encoding to ASCII, effectively converting characters like "é" to "e". It then creates a URL-safe "slug".
2.  It appends a short, cryptographically secure random string using Python's `secrets` module. This guarantees uniqueness even if multiple speakers have the same name, preventing data collisions.

### Logger (`logger`)

The logging utility provides a structured and configurable logging system. A key feature is its dynamic module detection. Upon instantiation, the `Logger` uses Python's `inspect.stack()` to identify the filename of the module that is creating the logger instance. It then uses this module name to create a dedicated log file within `~/.moves/logs/` (e.g., `speaker_manager.log`, `presentation_controller.log`). This automatic segregation of logs by component greatly simplifies debugging and troubleshooting. The logs are managed by a `RotatingFileHandler`, which automatically archives and rotates log files when they reach a certain size, preventing excessive disk usage.
