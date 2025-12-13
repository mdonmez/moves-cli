- [x] When source file paths are detected for the `process` command, display them clearly and ask for confirmation (`y/n`) so the user can verify which files will be used and cancel before the LLM process starts if needed.
- [ ] Decide on a consistent tab indentation size for all CLI output and apply it uniformly. — Also consider rethinking the entire view for the CLI to make it more user-friendly.
- [x] Replace all plain `print` statements with `typer.echo` for consistent CLI behavior.
- [x] Add a `--yes` flag to deletion commands along with an interactive confirmation prompt (similar to the source confirmation in `process`).
- [x] Improve the `process` command’s terminal output to make it more dynamic rather than static.
- [x] ~~Rewrite the logging util to use loguru.~~ Decided against — I will delay loggings for writing better logging utility.
- [x] Move the `'{name}' ({id})` formatting pattern into a data model so it can be applied consistently and automatically across the project based on the structure.
- [x] Move the `-3` and `+2` values into the configuration file.
- [x] Mask API keys by default and add a `--show` option to reveal them when necessary.
- [x] Switch back to cosine similarity instead of dot product for more reliable results.
  - [x] Normalize precomputed chunk embeddings: `self._norms[id(chunk)] = np.linalg.norm(embedding) or 1.0`
  - [x] Normalize input embedding: `input_embedding = input_embedding / np.linalg.norm(input_embedding)`
  - [x] Compute similarity using: `scores = candidate_matrix_normalized @ input_embedding`
- [x] ~~Consider implementing the `add_completion=true` option.~~ Decided against — requires manual user setup (`--install-completion`).
- [x] Add a “last processed timestamp” to `speaker.json`.
- [x] Refactor internal modules so that their dependencies are injected through external parameters, making them easier to test.
- [x] Fix `data_handler.copy` logic to properly handle source/target paths when they are already absolute or relative to `DATA_FOLDER` (currently may double-prepend `DATA_FOLDER`).
- [x] Replace hardcoded `window_size = 12` in `cli.py` with `moves_cli.config.WINDOW_SIZE`.
- [x] Refactor `SpeakerManager.process` to be an `async` function and manage the `asyncio` event loop at the CLI level for better composability.
- [x] Remove chunk generation after processing, this will improve speed and UI issues like stuck on 'Generating chunks...' while multi-speaker processing. Also in the multi-speaker case, show 'Done' if the individual speaker processing is done.
- [x] Add a loading dots to the `presentation control` command to show the loading status just like the `process` command.
- [x] Remove the settings_template.toml file and move its contents into the config file instead. But still keep the settings file at `.moves` for holding the user's settings. We will just make code changes to use the config file instead of the template file for clarity.
  - [x] The `settings --help` command's `unset` help's description's default LLM model is not correct, we should use the default LLM model from the config file.
- [x] The cancel command should cancel the current processing and not wait for it to finish.

## Potential Bugs and Code Quality Improvements (2025-12-11)

### CRITICAL: Memory Safety Issues Related to ID Usage

- [x] **`phonetic.py` (Lines 10, 23)**: Unsafe use of `id(chunk)`

  - **Issue**: In Python, `id()` returns the memory address. When chunk objects are garbage collected and recreated, IDs change.
  - **Impact**: Phonetic codes may not be found for chunks in the `candidates` list in the `compare()` method, potentially causing `KeyError` or incorrect results.
  - **Solution**: Add a unique hash or ID field to the `Chunk` model, or use an immutable tuple like `(partial_content, tuple(source_sections))`.

- [x] **`semantic.py` (Lines 24, 37)**: Unsafe use of `id(chunk)`

  - **Issue**: Same memory safety problem - when chunk objects are recreated, they won't be found in the embeddings dictionary.
  - **Impact**: `KeyError` or incorrect embedding matches, leading to errors in similarity calculations.
  - **Solution**: Use a stable identifier for chunks.

- [x] **`similarity_calculator.py` (Lines 29, 30, 51, 52)**: Unsafe use of `id(res.chunk)` and `id(candidate)`
  - **Issue**: Risk of ID collision when combining phonetic and semantic results.
  - **Impact**: Incorrect score calculations, potentially leading to navigation errors.
  - **Solution**: Use a stable identifier for chunks.

### MEDIUM: Concurrency and Thread Safety Issues

- [x] **`presentation_controller.py` (Lines 59-64)**: Race condition risk for `current_section` and queues

  - **Issue**: `self.current_section` is only protected by `section_lock` but the initial assignment (line 59) is outside the lock.
  - **Impact**: Race condition may occur during initial section assignment in multi-threaded environment.
  - **Solution**: Perform initial assignment inside the lock or before starting threads in `__init__`.

- [x] **`presentation_controller.py` (Lines 86-110)**: Error information lost in exception handling with shutdown_flag

  - **Issue**: In `except Exception:` block, only `shutdown_flag.set()` is called, error is not logged or reported to user.
  - **Impact**: Silent failures, debugging becomes difficult.
  - **Solution**: At minimum, write error to stderr or add logging.

- [x] **`speaker_manager.py` (Lines 170-178)**: Use of `os._exit()` in SIGINT handler
  - **Issue**: `os._exit()` exits without cleanup, files may not be properly closed.
  - **Impact**: Risk of data loss, especially during write operations.
  - **Solution**: Use `sys.exit()` or add graceful shutdown mechanism.

### MEDIUM: Data Consistency and Validation Issues

- [x] **`chunk_producer.py` (Line 30)**: No ordering guarantee when converting dictionary to list

  - **Issue**: Using `sections_dict.values()` but although Python 3.7+ preserves dict insertion order, this is not guaranteed behavior.
  - **Impact**: Section ordering may be mixed up, causing incorrect navigation.
  - **Solution**: Use `sorted(sections_dict.values(), key=lambda s: s.section_index)`.

- [x] **`data_handler.py` (Lines 24, 33)**: Path concatenation inconsistency

  - **Issue**: `write()` and `read()` methods use `self.DATA_FOLDER / Path(path)` but don't use the `_resolve_path()` method.
  - **Impact**: Absolute paths may be double-prepended (previously fixed but only for `copy()`).
  - **Solution**: Use `_resolve_path()` in all methods.

- [x] **`speaker_manager.py` (Lines 43-46)**: Insufficient name and ID collision check
  - **Issue**: Only checking `name in speaker_ids` but should also check the generated `speaker_id` value.
  - **Impact**: Very low probability but if the same ID is generated, data could be overwritten.
  - **Solution**: Check that the generated `speaker_id` doesn't conflict with existing IDs, add retry if needed.

### MEDIUM: Resource Management and Performance

- [ ] ~~**`presentation_controller.py` (Line 41)**: Model download with `asyncio.run()` on every `__init__` call~~

  - ~~**Issue**: Model download check is performed every time `PresentationController` is created, this is a blocking operation.~~
  - ~~**Impact**: UI freeze, unnecessary network checks.~~
  - ~~**Solution**: Perform model preparation once at CLI level, or use lazy loading.~~
  - **Not an issue**: Model preparer already has excellent caching - it verifies checksums (~50-100ms) and returns immediately if files are valid. No network calls after initial download.

- [ ] ~~**`semantic.py` (Lines 8-15)**: `TextEmbedding` model reloaded for each Semantic instance~~

  - ~~**Issue**: Model is reloaded every time a new `SimilarityCalculator` is created for each speaker.~~
  - ~~**Impact**: Memory waste, slow startup.~~
  - ~~**Solution**: Share the model using singleton pattern or dependency injection.~~
  - **Not an issue**: Each presentation control session is a separate CLI process. The model loads once per session and memory is freed when the process exits. Different speakers = different processes, no memory waste.

- [ ] ~~**`model_preparer.py` (Lines 64-71)**: Race condition during empty directory cleanup~~
  - ~~**Issue**: While traversing directory tree with `os.walk()`, another process could create files.~~
  - ~~**Impact**: `OSError` or incomplete cleanup.~~
  - ~~**Solution**: Exception handling already exists but could be made more robust.~~
  - **Not an issue**: Exception handling is already appropriate. All `OSError` cases (directory not empty, already deleted, permission denied) are safe to ignore. Cleanup is non-critical and self-healing - missed items get cleaned up next time. Over-engineering to make this "more robust".

### LOW: Code Quality and Maintainability

- [x] **`similarity_calculator.py` (Lines 32-38)**: Redundant `if max_p == 0` check

  - **Issue**: Lines 32-33 already assign 1.0 if `max()` result is 0, then check again.
  - **Impact**: Code duplication, reduced readability.
  - **Solution**: Remove second check or combine: `max_p = max(phonetic_scores.values()) if phonetic_scores else 1.0; max_p = max_p or 1.0`

- [x] **`text_normalizer.py` (Line 48)**: No exception handling for `num2words()`

  - **Issue**: `num2words()` may fail for very large numbers or special formats.
  - **Impact**: Text normalization fails, affecting entire pipeline.
  - **Solution**: Add try-except, keep original number on error.
  - **Fixed**: Added `NormalizationMode` enum (LIVE/PREPROCESS). LIVE mode skips num2words entirely for live speech. PREPROCESS mode includes exception handling with fallback.

- [x] **`section_producer.py` (Lines 59-60)**: LLM validation constraints calculated at runtime

  - **Issue**: `min_items` and `max_items` are recalculated on every LLM call.
  - **Impact**: Not a performance loss but code smell.
  - **Solution**: Calculate slide count beforehand and pass as parameter.

- [x] **`cli.py` (Lines 183-189)**: Complex list comprehension with datetime parsing

  - **Issue**: Low readability, difficult error handling.
  - **Impact**: Maintenance difficulty.
  - **Solution**: Extract to helper function.
  - **Fixed**: Replaced with constant width (16 chars for "YYYY-MM-DD HH:MM" format). Simpler, faster, no crash risk.

- [x] **`speaker_manager.py` (Lines 307-308)**: Inconsistent variable naming
  - **Issue**: `speaker_list` used as both input parameter and local variable.
  - **Impact**: Confusion, potential bug.
  - **Solution**: Use more descriptive name like `resolved_speakers`.

### LOW: Type Safety and Validation

- [x] **`models.py` (Lines 16-18)**: `Chunk` is frozen but `source_sections` is mutable list

  - **Issue**: Despite `frozen=True`, list contents can be modified.
  - **Impact**: Immutability guarantee is broken.
  - **Solution**: Use `source_sections: tuple[Section, ...]` or convert to tuple in `__post_init__`.

- [x] **`data_handler.py` (Lines 62-63)**: Unlink after target_path.exists() check in `rename()` method

  - **Issue**: Race condition - another process could delete the file between exists check and unlink.
  - **Impact**: `FileNotFoundError` may occur.
  - **Solution**: `missing_ok=True` parameter already exists but not used in `unlink()` call.

- ~~**`settings_editor.py` (Lines 22-24)**: Exception catching too broad~~ **Not an issue**

  - **Issue**: `except Exception:` catches all errors, no specific error handling.
  - **Impact**: Debugging becomes difficult, different errors handled the same way.
  - **Solution**: Separate specific exceptions like `FileNotFoundError`, `tomlkit.exceptions.ParseError`.
  - **Analysis**: The broad exception is **intentional** - settings file is self-repairing. If corrupted or missing, it automatically resets to defaults and saves. This is better UX than crashing.

- [x] Fix alignment while creating sections and starting live presentation control, sections must start start from 1—not 0—and the presentation control must start from the first section [0], so 1. This reflects the real-world presentation order and scenario.

**Issue:** Section indexing is currently 0-based (`section_index` starts at 0), causing inconsistency with real-world 1-based presentation numbering and requiring manual adjustments for user displays.

**Goal:** Standardize `section_index` to be 1-based throughout the system.

**Proposed Changes:**

1.  **`section_producer.py` (Line 32):** Update PDF slide labeling: Change `f"# Slide Page {i}"` to `f"# Slide Page {i + 1}"`.
2.  **`section_producer.py` (Lines 53-55):** Update LLM schema constraint: Change `ge=0` to `ge=1` (Index starting from 1).
3.  **`section_producer.py` (Line 138):** Adjust section creation: Change `section_index=idx` to `section_index=idx + 1`.
4.  **`presentation_controller.py` (Line 149):** Update status display: Remove manual adjustment, changing `current_section.section_index + 1` to `current_section.section_index`.

_(Array indexing like `sections[0]` remains correct, accessing the first section which now holds a `section_index` of 1.)_

- [x] Fix non %100 and always highest is %99 issue with threshold alignment

- [x] +3 -2 instead of -3 +2

- [x] ~~Move the ID generation logics from inline codes to the models' itself for more centralized and maintainable code, while still keeping the id generation utility.~~ — Do better SOLID alternative instead, DI-based chunk ID generation.

- [x] Refine and unify the CLI output function to handle text, key-value pairs, and tables consistently across the application, replacing scattered `typer.echo` formatting with a centralized `output` utility using `rich`.
