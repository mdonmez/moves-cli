# Refactoring Plan — moves-cli

## Target Architecture

```
src/moves_cli/
├── cli.py                          # Composition root — all wiring is done here
├── config.py                       # Immutable — constants only
├── models.py                       # Domain models + Protocol ports
├── ml_models.py                    # ML model instances (EmbeddingModel, SttModel, VadModel)
├── controller.py                   # Brain — orchestration + state machine
│
├── modules/
│   ├── presentation/
│   │   ├── chunks.py               # Sliding window generation + candidate index
│   │   ├── similarity.py           # Phonetic + semantic + score fusion
│   │   ├── pipeline.py             # Microphone + VAD + STT (audio → words)
│   │   ├── navigator.py            # Physical key presses (SlideNavigator adapter)
│   │   ├── display.py              # Rich live dashboard (Display adapter)
│   │   └── model_manager.py        # ML model download + verification
│   │
│   ├── speaker/
│   │   ├── __init__.py             # SpeakerManager — CRUD
│   │   ├── processor.py            # SectionProducer — LLM pipeline
│   │   └── google.py               # Google Drive handler
│   │
│   └── settings.py                 # SettingsEditor — TOML + keyring
│
└── utils/
    ├── data_handler.py             # Filesystem abstraction
    ├── formatters.py               # output(), markdown_to_plain_text(), format_datetime()
    ├── text_normalizer.py          # normalize_text(), NormalizationMode
    ├── hasher.py                   # calculate_hash() — dev CLI part removed
    └── id_generator.py             # generate_chunk_id(), generate_speaker_id()
```

---

## Layer Contract

```
utils/        →  knows nothing (stdlib + 3rd party only)
models.py     →  knows nothing (stdlib only, defines Protocols)
ml_models.py  →  models + config
modules/      →  models + utils (modules do not know each other, do not know controller)
controller.py →  models + utils (does not import modules — receives Protocol implementations via injection)
cli.py        →  modules + controller (composition root, single wiring point)
```

---

## Protocol Definitions (to be added in models.py)

```python
from typing import Protocol, runtime_checkable
from moves_cli.models import Chunk, Section, SimilarityResult

@runtime_checkable
class SimilarityEngine(Protocol):
    def compare(
        self,
        input_str: str,
        candidates: list[Chunk],
        current_section_index: int,
    ) -> list[SimilarityResult]: ...

@runtime_checkable
class AudioPipeline(Protocol):
    def start(self) -> None: ...
    def stop(self) -> None: ...
    def get_words(self, timeout: float) -> list[str] | None: ...
    def is_vad_active(self) -> bool: ...

@runtime_checkable
class SlideNavigator(Protocol):
    def navigate(self, target: Section) -> None: ...
    def get_manual_delta(self) -> int: ...

@runtime_checkable
class Display(Protocol):
    def update(self, data: UIData) -> None: ...
```

---

## Step-by-Step Implementation Plan

### Step 1 — Create ml_models.py

**Source:** `src/moves_cli/models.py` (last 40 lines)
**Target:** `src/moves_cli/ml_models.py` (new file)

Move the following:

- `MlModel` dataclass
- `EmbeddingModel` instance
- `SttModel` instance
- `VadModel` instance

These parts are removed from `models.py`.

`ml_models.py` dependencies:

```python
from moves_cli.config import DATA_FOLDER
from moves_cli.models import MlModel  # MlModel dataclass remains in models.py
```

`MlModel` stays in `models.py` because it is a typical domain model structure.

---

### Step 2 — Add Protocols to models.py

Add the following to `models.py`:

```python
from typing import Protocol, runtime_checkable
```

Protocols to add:

- `SimilarityEngine`
- `AudioPipeline`
- `SlideNavigator`
- `Display`
- `UIData` dataclass (currently defined in `presentation_controller.py`)

`UIData` should be defined here because both `controller.py` and `modules/presentation/display.py` will use it.

---

### Step 3 — Create utils/hasher.py

**Source:** `src/moves_cli/utils/calculate_hash.py`
**Target:** `src/moves_cli/utils/hasher.py`

Current `calculate_hash.py`:

- `calculate_hash(filepath)` function — STAYS
- `Typer` app and `@app.command()` — REMOVED

`hasher.py` should only contain:

```python
from pathlib import Path
import xxhash

CHUNK_SIZE = 1024 * 1024

def calculate_hash(filepath: Path) -> str | None:
    ...
```

`calculate_hash.py` is deleted.

Note: `SpeakerManager.compute_file_hash()` contains similar logic. They can be merged, but that is out of scope — keep it in `hasher.py` for now.

---

### Step 4 — Create modules/presentation/display.py

**Source:** `src/moves_cli/core/presentation_controller.py` (lines 46–168)
**Target:** `src/moves_cli/modules/presentation/display.py`

Items to move (zero logic changes):

- `THEME = Theme({...})`
- `STATE_STYLE = {...}`
- `UIData` dataclass → actually moved to `models.py`, imported from there
- `_format_speech_text()`
- `_build_header()`
- `_build_content()`
- `_build_footer()`
- `_build_frame()`

`display.py` public interface:

```python
class DisplayEngine:
    """Rich dashboard implementing the Display Protocol."""
    def __init__(self, console: Console, live: Live): ...
    def update(self, data: UIData) -> None: ...
```

`display.py` dependencies:

```python
from rich import ...
from moves_cli.models import UIData, ControllerState
```

---

### Step 5 — Create modules/presentation/navigator.py

**Source:** `src/moves_cli/core/presentation_controller.py`
**Target:** `src/moves_cli/modules/presentation/navigator.py`

Items to move:

- `_on_key_press()` — key handling logic for Q, M, ←/→
- `_perform_navigation()` — physical key press via pynput
- `Listener` start/stop

`navigator.py` public interface:

```python
class KeyboardNavigator:
    """Implements SlideNavigator Protocol."""

    def __init__(self, sections: list[Section]): ...

    def start(self) -> None:
        """Start keyboard listener."""

    def stop(self) -> None:
        """Stop keyboard listener."""

    def navigate(self, target: Section) -> None:
        """Press physical key with echo suppression."""

    def get_manual_delta(self) -> int:
        """Return total manual navigation in the last 1 second."""

    def poll_key_event(self) -> str | None:
        """Fetch pending key event: 'quit', 'toggle_pause', None."""
```

**Important:** State machine decisions must NOT be in `navigator.py`.

- Old: `_on_key_press` called `_set_state(PAUSED)` when M was pressed
- New: `poll_key_event()` returns `'toggle_pause'`, decision is made in `controller.py`

`navigator.py` dependencies:

```python
from pynput.keyboard import Controller, Key, Listener
from moves_cli.models import Section
```

---

### Step 6 — Create modules/presentation/pipeline.py

**Source:** `src/moves_cli/core/presentation_controller.py`
**Target:** `src/moves_cli/modules/presentation/pipeline.py`

Items to move:

- `_audio_sampler_callback()` — VAD-gated audio capture
- `_stt_processor_task()` — Sherpa ONNX stream processing
- `OnlineRecognizer` initialization
- `VoiceActivityDetector` initialization
- Sliding word buffer (`_word_buffer`, `_display_buffer`)

`pipeline.py` public interface:

```python
class VoicePipeline:
    """Implements AudioPipeline Protocol."""

    SAMPLE_RATE: int = 16000
    FRAME_DURATION: float = 0.1
    NUM_THREADS: int = 8

    def __init__(self, stt_model_dir: Path, vad_model_dir: Path, window_size: int): ...

    def start(self) -> None:
        """Start STT thread and audio stream."""

    def stop(self) -> None:
        """Stop thread and stream."""

    def get_words(self, timeout: float = 1.0) -> list[str] | None:
        """Read from word queue. Return None if empty."""

    def is_vad_active(self) -> bool:
        """Is VAD currently detecting speech?"""

    def get_display_buffer(self) -> list[str]:
        """Return recent words for display."""
```

`pipeline.py` dependencies:

```python
import sounddevice as sd
from sherpa_onnx import OnlineRecognizer, VadModelConfig, VoiceActivityDetector
from moves_cli.config import VAD_THRESHOLD, VAD_MIN_SILENCE, ...
from moves_cli.ml_models import SttModel, VadModel
from moves_cli.utils.text_normalizer import normalize_text
```

---

### Step 7 — Create modules/presentation/chunks.py

**Source:** `src/moves_cli/core/components/chunk_producer.py`
**Target:** `src/moves_cli/modules/presentation/chunks.py`

Items to move (zero changes):

- `generate_chunks()` function
- `CandidateChunkGenerator` class

Update dependencies:

```python
# Old:
from moves_cli.utils import text_normalizer
from moves_cli.utils.id_generator import generate_chunk_id
# New: same, path unchanged
```

---

### Step 8 — Create modules/presentation/similarity.py

**Source:** merge 3 files

- `src/moves_cli/core/components/similarity_calculator.py`
- `src/moves_cli/core/components/similarity_units/phonetic.py`
- `src/moves_cli/core/components/similarity_units/semantic.py`

**Target:** `src/moves_cli/modules/presentation/similarity.py`

Structure:

```python
# --- Phonetic Engine (old phonetic.py content) ---
class _PhoneticEngine:
    def __init__(self, all_chunks: list[Chunk]) -> None: ...
    def compare(self, input_str: str, candidates: list[Chunk]) -> list[SimilarityResult]: ...

# --- Semantic Engine (old semantic.py content) ---
class _SemanticEngine:
    def __init__(self, all_chunks: list[Chunk]) -> None: ...
    def compare(self, input_str: str, candidates: list[Chunk]) -> list[SimilarityResult]: ...

# --- Public class (old similarity_calculator.py) ---
# Satisfies SimilarityEngine Protocol
class SimilarityCalculator:
    def __init__(
        self,
        all_chunks: list[Chunk],
        semantic_weight: float = SEMANTIC_WEIGHT,
        phonetic_weight: float = PHONETIC_WEIGHT,
    ) -> None:
        self._phonetic = _PhoneticEngine(all_chunks)
        self._semantic = _SemanticEngine(all_chunks)
        ...

    def compare(
        self,
        input_str: str,
        candidates: list[Chunk],
        current_section_index: int = 0,
    ) -> list[SimilarityResult]: ...
```

`_PhoneticEngine` and `_SemanticEngine` are private (leading underscore) — only `SimilarityCalculator` is exposed publicly.

To add a new similarity algorithm, only this file changes; nothing else needs to know.

Dependencies:

```python
from jellyfish import metaphone
from rapidfuzz import fuzz, process
import numpy as np
from fastembed import TextEmbedding
from moves_cli.config import PHONETIC_WEIGHT, SEMANTIC_WEIGHT
from moves_cli.ml_models import EmbeddingModel
from moves_cli.models import Chunk, SimilarityResult
```

---

### Step 9 — Create modules/presentation/model_manager.py

**Source:** `src/moves_cli/utils/model_preparer.py`
**Target:** `src/moves_cli/modules/presentation/model_manager.py`

Zero logic changes. Dependency update:

```python
# Old:
from moves_cli.models import EmbeddingModel, SttModel, VadModel
# New:
from moves_cli.ml_models import EmbeddingModel, SttModel, VadModel
```

`model_preparer.py` is deleted.

---

### Step 10 — Create modules/speaker/google.py

**Source:** `src/moves_cli/utils/google_handler.py`
**Target:** `src/moves_cli/modules/speaker/google.py`

Zero logic changes. File is only moved.

Imports to update:

```python
# In cli.py:
# Old: from moves_cli.utils.google_handler import resolve_source_path
# New: from moves_cli.modules.speaker.google import resolve_source_path
```

`google_handler.py` is deleted.

---

### Step 11 — Create modules/speaker/**init**.py

**Source:** `src/moves_cli/core/speaker_manager.py`
**Target:** `src/moves_cli/modules/speaker/__init__.py`

Imports to update:

```python
# Old:
from moves_cli.core.components.section_producer import SectionProducer
# New:
from moves_cli.modules.speaker.processor import SectionProducer
```

```python
# Old:
from moves_cli.utils import id_generator
# New: same — utils path unchanged
```

`speaker_manager.py` is deleted.

---

### Step 12 — Create modules/speaker/processor.py

**Source:** `src/moves_cli/core/components/section_producer.py`
**Target:** `src/moves_cli/modules/speaker/processor.py`

Zero logic changes. Dependencies stay the same.

`section_producer.py` is deleted.

---

### Step 13 — Create modules/settings.py

**Source:** `src/moves_cli/core/settings_editor.py`
**Target:** `src/moves_cli/modules/settings.py`

Zero logic changes.

```python
# Old import path:
from moves_cli.core.settings_editor import SettingsEditor
# New:
from moves_cli.modules.settings import SettingsEditor
```

`settings_editor.py` is deleted.

---

### Step 14 — Create controller.py

**Source:** `src/moves_cli/core/presentation_controller.py` (main structure)
**Target:** `src/moves_cli/controller.py`

This is the file that requires the most rewriting.

**New `controller.py` structure:**

```python
from moves_cli.models import (
    ControllerState, Section, UIData,
    AudioPipeline, SlideNavigator, Display, SimilarityEngine
)
from moves_cli.modules.presentation.chunks import (
    generate_chunks, CandidateChunkGenerator
)

class Controller:
    SIMILARITY_THRESHOLD: float = SIMILARITY_THRESHOLD
    SHUTDOWN_CHECK_INTERVAL: float = 0.1
    KEY_EVENT_CHECK_INTERVAL: float = 0.05
    MANUAL_DELTA_TTL: float = 1.0

    def __init__(
        self,
        sections: list[Section],
        window_size: int,
        pipeline: AudioPipeline,
        navigator: SlideNavigator,
        display: Display,
        similarity: SimilarityEngine,
    ) -> None:
        self.sections = sections
        self._state = ControllerState.ACTIVE
        self._state_lock = threading.Lock()
        self.shutdown_flag = threading.Event()

        # Chunk engine — imported from presentation module directly by controller
        self.chunks = generate_chunks(sections, window_size)
        self.candidate_generator = CandidateChunkGenerator(self.chunks)

        # Injected dependencies — depends on Protocols, does not know concrete classes
        self.pipeline = pipeline
        self.navigator = navigator
        self.display = display
        self.similarity = similarity

        # State
        self.section_lock = threading.Lock()
        self.current_section = sections[0]
        self._manual_delta: int = 0
        self._manual_delta_expiry: float = 0.0
        self._last_similarity: float = 0.0

        # Navigator thread
        self._navigator_thread = threading.Thread(
            target=self._navigator_loop, daemon=True
        )

    def _get_state(self) -> ControllerState: ...
    def _set_state(self, new_state: ControllerState) -> None: ...

    def _handle_key_event(self, event: str | None) -> None:
        """State transition decisions are made here — not in navigator."""
        match event:
            case 'quit':
                self.shutdown_flag.set()
            case 'toggle_pause':
                match self._get_state():
                    case ControllerState.ACTIVE | ControllerState.LOCKED:
                        self._set_state(ControllerState.PAUSED)
                    case ControllerState.PAUSED:
                        self._set_state(ControllerState.ACTIVE)
            case 'manual_nav':
                if self._get_state() == ControllerState.ACTIVE:
                    self._set_state(ControllerState.LOCKED)

    def _navigator_loop(self) -> None:
        """Similarity computation and navigation loop."""
        ...

    def run(self) -> None:
        """Main loop — pipeline + navigator + display."""
        self.pipeline.start()
        self._navigator_thread.start()

        try:
            with Live(...) as live:
                with sd.InputStream(...):
                    while not self.shutdown_flag.is_set():
                        # Key events — state decisions are handled here
                        event = self.navigator.poll_key_event()
                        self._handle_key_event(event)

                        # UI update
                        ...

                        self.shutdown_flag.wait(timeout=self.SHUTDOWN_CHECK_INTERVAL)
        finally:
            self.pipeline.stop()
            ...
```

**Important change:** `_audio_sampler_callback` is now in `pipeline.py`. Controller no longer manages audio stream directly — it polls pipeline via `get_words()` and `is_vad_active()`.

---

### Step 15 — Update cli.py

`cli.py` becomes the composition root. All lazy imports and instance factories are updated.

**Changed imports:**

```python
# Old factory functions:
def speaker_manager_instance():
    from moves_cli.core.speaker_manager import SpeakerManager
    ...

def presentation_controller_instance(sections, window_size):
    from moves_cli.core.presentation_controller import PresentationController
    ...

def settings_editor_instance():
    from moves_cli.core.settings_editor import SettingsEditor
    ...

# New factory functions:
def speaker_manager_instance():
    from moves_cli.modules.speaker import SpeakerManager
    ...

def settings_editor_instance():
    from moves_cli.modules.settings import SettingsEditor
    ...

def controller_instance(sections: list[Section], window_size: int):
    from moves_cli.controller import Controller
    from moves_cli.modules.presentation.pipeline import VoicePipeline
    from moves_cli.modules.presentation.navigator import KeyboardNavigator
    from moves_cli.modules.presentation.display import DisplayEngine
    from moves_cli.modules.presentation.similarity import SimilarityCalculator
    from moves_cli.modules.presentation.chunks import generate_chunks
    from moves_cli.ml_models import SttModel, VadModel

    chunks = generate_chunks(sections, window_size)

    pipeline = VoicePipeline(SttModel.model_dir, VadModel.model_dir, window_size)
    navigator = KeyboardNavigator(sections)
    display = DisplayEngine()
    similarity = SimilarityCalculator(chunks)

    return Controller(
        sections=sections,
        window_size=window_size,
        pipeline=pipeline,
        navigator=navigator,
        display=display,
        similarity=similarity,
    )
```

**`present` command:**

```python
# Old:
from moves_cli.core.components.section_producer import SectionProducer
controller = presentation_controller_instance(sections, window_size=window_size)
controller.control()

# New:
from moves_cli.modules.speaker.processor import SectionProducer
controller = controller_instance(sections, window_size=window_size)
controller.run()
```

**`speaker_prepare` command:**

```python
# Old (inside lazy import):
from moves_cli.core.components.section_producer import SectionProducer
# New:
from moves_cli.modules.speaker.processor import SectionProducer
```

**`google_handler` imports:**

```python
# Old:
from moves_cli.utils.google_handler import resolve_source_path
# New:
from moves_cli.modules.speaker.google import resolve_source_path
```

**`Optional` → `X | None`:**

```python
# Old (cli.py line 6):
from typing import Optional
# New: removed

# Old:
source_presentation: Optional[str] = typer.Option(...)
# New:
source_presentation: str | None = typer.Option(...)
```

---

### Step 16 — Files to Delete

After refactoring is complete, delete the following files and folders:

```
src/moves_cli/core/presentation_controller.py   → split into controller.py + modules/presentation/
src/moves_cli/core/speaker_manager.py            → modules/speaker/__init__.py
src/moves_cli/core/settings_editor.py            → modules/settings.py
src/moves_cli/core/components/chunk_producer.py  → modules/presentation/chunks.py
src/moves_cli/core/components/section_producer.py → modules/speaker/processor.py
src/moves_cli/core/components/similarity_calculator.py → modules/presentation/similarity.py
src/moves_cli/core/components/similarity_units/phonetic.py → modules/presentation/similarity.py
src/moves_cli/core/components/similarity_units/semantic.py → modules/presentation/similarity.py
src/moves_cli/utils/calculate_hash.py            → utils/hasher.py
src/moves_cli/utils/google_handler.py            → modules/speaker/google.py
src/moves_cli/utils/model_preparer.py            → modules/presentation/model_manager.py

# Empty folders left behind:
src/moves_cli/core/                              → remove completely
src/moves_cli/core/components/
src/moves_cli/core/components/similarity_units/
```

---

### Step 17 — `__init__.py` Files

Create the following `__init__.py` files:

```
src/moves_cli/modules/__init__.py
src/moves_cli/modules/presentation/__init__.py
src/moves_cli/modules/speaker/__init__.py   ← Not empty, SpeakerManager lives here
```

---

## Implementation Order

By dependency order — dependencies first, dependents later:

```
1.  ml_models.py                      (depends only on models + config)
2.  models.py update                  (add Protocols, add UIData)
3.  utils/hasher.py                   (independent)
4.  modules/presentation/display.py   (depends on models)
5.  modules/presentation/navigator.py (depends on models)
6.  modules/presentation/chunks.py    (depends on models + utils)
7.  modules/presentation/similarity.py (depends on models + ml_models)
8.  modules/presentation/pipeline.py  (depends on models + ml_models + config)
9.  modules/presentation/model_manager.py (depends on ml_models)
10. modules/speaker/google.py         (depends on stdlib + httpx)
11. modules/speaker/processor.py      (depends on models)
12. modules/speaker/__init__.py       (depends on models + utils + processor)
13. modules/settings.py               (depends on models + utils)
14. controller.py                     (depends on models + presentation/*)
15. cli.py update                     (depends on all modules + controller)
16. Delete old files
17. Delete empty core/ folder
```

---

## Unchanged Files

```
src/moves_cli/config.py               # Untouched
src/moves_cli/utils/data_handler.py   # Untouched
src/moves_cli/utils/formatters.py     # Untouched
src/moves_cli/utils/text_normalizer.py # Untouched
src/moves_cli/utils/id_generator.py   # Untouched
src/moves_cli/data/                   # Untouched — package data
pyproject.toml                        # Untouched — only file structure changes
```

---

## Summary Change Table

| Current                                                           | Target                                     | Type                                    |
| ----------------------------------------------------------------- | ------------------------------------------ | --------------------------------------- |
| `models.py`                                                       | `models.py` + `ml_models.py`               | Split                                   |
| `core/presentation_controller.py`                                 | `controller.py` + `modules/presentation/*` | Decomposition                           |
| `core/components/chunk_producer.py`                               | `modules/presentation/chunks.py`           | Move                                    |
| `core/components/similarity_calculator.py` + `similarity_units/*` | `modules/presentation/similarity.py`       | Merge + Move                            |
| `core/speaker_manager.py`                                         | `modules/speaker/__init__.py`              | Move                                    |
| `core/components/section_producer.py`                             | `modules/speaker/processor.py`             | Move                                    |
| `core/settings_editor.py`                                         | `modules/settings.py`                      | Move                                    |
| `utils/google_handler.py`                                         | `modules/speaker/google.py`                | Move                                    |
| `utils/model_preparer.py`                                         | `modules/presentation/model_manager.py`    | Move                                    |
| `utils/calculate_hash.py`                                         | `utils/hasher.py`                          | Simplification                          |
| —                                                                 | `ml_models.py`                             | New                                     |
| —                                                                 | `controller.py`                            | New                                     |
| —                                                                 | `modules/presentation/display.py`          | New                                     |
| —                                                                 | `modules/presentation/navigator.py`        | New (narrowed navigator responsibility) |
| —                                                                 | `modules/presentation/pipeline.py`         | New                                     |

---

## Numeric Comparison

| Metric                          | Current                                           | Target                             |
| ------------------------------- | ------------------------------------------------- | ---------------------------------- |
| Total file count                | 16                                                | 19                                 |
| Longest file                    | 909 lines (`cli.py`)                              | ~350 lines (`controller.py`, est.) |
| `core/` depth                   | 4 levels                                          | 0 (removed)                        |
| Single-responsibility violation | `presentation_controller.py` (7 responsibilities) | None                               |
| Testable component              | 0 (concrete dependencies)                         | 4 (Protocol-mockable)              |
