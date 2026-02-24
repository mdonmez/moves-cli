# Refactoring Plan — moves-cli

## Target Architecture

```
src/moves_cli/
├── cli.py                          # Composition root — all wiring is done here
├── config.py                       # Immutable — constants only
├── models.py                       # Domain models + Protocol ports
├── ml_models.py                    # ML model instances (EmbeddingModel, SttModel, VadModel)
├── core.py                         # Brain — orchestration + state machine
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
    ├── formatters.py               # output(), markdown_to_plain_text(), format_datetime(), normalize_text()
    ├── hasher.py                   # calculate_hash() — dev CLI part removed
    └── id_generator.py             # generate_chunk_id(), generate_speaker_id()
```

---

## Layer Contract

```
utils/        →  knows nothing (stdlib + 3rd party only)
models.py     →  knows nothing (stdlib only, defines Protocols)
ml_models.py  →  models + config
modules/      →  models + utils (modules do not know each other, do not know core)
core.py       →  models + utils (does not import modules — receives Protocol implementations via injection)
cli.py        →  modules + core (composition root, single wiring point)
```

---

## Protocol Definitions (models.py)

### Enums & Data Classes

```python
from dataclasses import dataclass
from enum import StrEnum


class ControllerState(StrEnum):
    ACTIVE = "ACTIVE"   # listening, auto-navigation enabled
    PAUSED = "PAUSED"   # mic muted, keyboard still active
    LOCKED = "LOCKED"   # listening, auto-navigation disabled


class KeyEvent(StrEnum):
    QUIT         = "quit"
    TOGGLE_PAUSE = "toggle_pause"
    NAV_FORWARD  = "nav_fwd"
    NAV_BACK     = "nav_back"


@dataclass(frozen=True, slots=True)
class UIData:
    state:      ControllerState
    slide:      int
    total:      int
    similarity: float
    delta:      int
    speech:     list[str]
    match:      list[str]
    vad:        bool
```

### Protocol Ports

```python
from __future__ import annotations
from typing import Protocol, runtime_checkable


@runtime_checkable
class SimilarityEngine(Protocol):
    """Implementor: SimilarityCalculator — modules/presentation/similarity.py"""

    def compare(
        self,
        input_str: str,
        candidates: list[Chunk],
        current_section_index: int,
    ) -> list[SimilarityResult]:
        """Rank candidates by combined phonetic + semantic score. Empty list if no candidates."""
        ...


@runtime_checkable
class ChunkStore(Protocol):
    """
    Implementor: CandidateChunkGenerator — modules/presentation/chunks.py

    Injected into core.py so that core.py does not import from modules/.
    Resolves the layer contract: core.py → models + utils only.
    """

    def get_candidates(self, section: Section) -> list[Chunk]:
        """Return candidate chunks for the given section. Empty list if none."""
        ...


@runtime_checkable
class AudioPipeline(Protocol):
    """Implementor: VoicePipeline — modules/presentation/pipeline.py"""

    def start(self) -> None:
        """Start STT thread and open audio stream."""
        ...

    def stop(self) -> None:
        """Stop STT thread and close audio stream."""
        ...

    def get_words(self, timeout: float = 1.0) -> list[str] | None:
        """
        Return normalized word list from STT buffer.
        None  → queue empty (timeout reached), caller should skip.
        """
        ...

    def is_vad_active(self) -> bool:
        """Return True if VAD is currently detecting speech."""
        ...

    def get_display_buffer(self) -> list[str]:
        """Return recent words for UI display (larger rolling buffer than logic buffer)."""
        ...


@runtime_checkable
class SlideNavigator(Protocol):
    """
    Implementor: KeyboardNavigator — modules/presentation/navigator.py

    Owns:     internal current-section cursor, echo suppression, manual-delta TTL.
    Does NOT: make state-machine decisions — ACTIVE / PAUSED / LOCKED logic stays in core.py.
    """

    def start(self) -> None:
        """Start global keyboard listener."""
        ...

    def stop(self) -> None:
        """Stop keyboard listener."""
        ...

    def navigate(self, target: Section) -> None:
        """
        Press physical arrow keys to reach target section.
        Delta is calculated from navigator's internal cursor.
        Echo suppression applied internally — own key presses are ignored by listener.
        Updates internal cursor to target after navigation.
        """
        ...

    def poll_key_event(self) -> KeyEvent | None:
        """
        Dequeue the next pending user key event.
        Returns None if no event is waiting.
        Never makes state-machine decisions — that is core.py's responsibility.
        """
        ...

    def get_manual_delta(self) -> int:
        """
        Net manual navigation (user arrow presses) within the last 1 second.
        Positive = rightward, negative = leftward.
        Auto-navigations via navigate() do NOT count toward this delta.
        """
        ...


@runtime_checkable
class Display(Protocol):
    """Implementor: DisplayEngine — modules/presentation/display.py"""

    def update(self, data: UIData) -> None:
        """Render the current application state to the Rich live display."""
        ...
```

### Implementor Map

| Protocol           | Implementor Class         | File                                 |
| ------------------ | ------------------------- | ------------------------------------ |
| `SimilarityEngine` | `SimilarityCalculator`    | `modules/presentation/similarity.py` |
| `ChunkStore`       | `CandidateChunkGenerator` | `modules/presentation/chunks.py`     |
| `AudioPipeline`    | `VoicePipeline`           | `modules/presentation/pipeline.py`   |
| `SlideNavigator`   | `KeyboardNavigator`       | `modules/presentation/navigator.py`  |
| `Display`          | `DisplayEngine`           | `modules/presentation/display.py`    |

`core.py` receives all five via constructor injection — imports only `models.py`, `config.py`, `utils/`.

---

## Implementation Tasks

### New Files

- `ml_models.py` — `MlModel` instance'larını `models.py`'den çıkar (`EmbeddingModel`, `SttModel`, `VadModel`). `MlModel` dataclass `models.py`'de kalır.
- `core.py` — Orchestration + state machine. Concrete sınıf bilmez; tüm bağımlılıkları DI ile alır:
  ```python
  def __init__(
      self,
      sections: list[Section],
      window_size: int,
      pipeline: AudioPipeline,
      navigator: SlideNavigator,
      display: Display,
      similarity: SimilarityEngine,
      chunk_store: ChunkStore,   # CandidateChunkGenerator enjekte edilir
  ) -> None: ...
  ```
  `core.py` imports: `models`, `config`, `utils/` only.
- `modules/presentation/display.py` — Rich dashboard. `DisplayEngine` sınıfı `Display` Protocol'ünü karşılar.
- `modules/presentation/navigator.py` — Klavye listener. `KeyboardNavigator` sınıfı `SlideNavigator` Protocol'ünü karşılar. **State kararı vermez** — `poll_key_event()` ile `'quit'` / `'toggle_pause'` / `None` döner, karar `core.py`'dedir.
- `modules/presentation/pipeline.py` — Mikrofon + VAD + STT. `VoicePipeline` sınıfı `AudioPipeline` Protocol'ünü karşılar.

### Modified Files

- `models.py` — Şunlar eklenir/taşınır:
  - `ControllerState` StrEnum (`presentation_controller.py`'den taşınır)
  - `KeyEvent` StrEnum (yeni — NAV_FORWARD / NAV_BACK / TOGGLE_PAUSE / QUIT)
  - `UIData` dataclass (`presentation_controller.py`'den taşınır)
  - Protocol portları: `SimilarityEngine`, `ChunkStore`, `AudioPipeline`, `SlideNavigator`, `Display`
- `utils/formatters.py` — `text_normalizer.py`'deki `normalize_text()` fonksiyonunu absorbe et. `text_normalizer.py` silinir.
- `cli.py` — Composition root yeniden yaz: factory fonksiyonları güncelle (`core + modules`), `Optional` → `X | None`.

### Moves (sıfır mantık değişikliği)

- `core/components/chunk_producer.py` → `modules/presentation/chunks.py`
- `core/components/similarity_calculator.py` + `similarity_units/phonetic.py` + `similarity_units/semantic.py` → `modules/presentation/similarity.py` (3 dosya birleşir; `_PhoneticEngine` / `_SemanticEngine` private kalır)
- `core/speaker_manager.py` → `modules/speaker/__init__.py` (`compute_file_hash()` → `utils/hasher.py`'e delege eder)
- `core/components/section_producer.py` → `modules/speaker/processor.py`
- `core/settings_editor.py` → `modules/settings.py`
- `utils/google_handler.py` → `modules/speaker/google.py`
- `utils/model_preparer.py` → `modules/presentation/model_manager.py` (import güncellenir: `models` → `ml_models`)

### Simplifications

- `utils/calculate_hash.py` → `utils/hasher.py` — Typer CLI kaldırılır, sadece `calculate_hash()` fonksiyonu kalır. `SpeakerManager.compute_file_hash()` buna delege eder.

### Deletions

```
src/moves_cli/core/                        (tüm klasör)
src/moves_cli/utils/calculate_hash.py
src/moves_cli/utils/google_handler.py
src/moves_cli/utils/model_preparer.py
src/moves_cli/utils/text_normalizer.py
```

### New `__init__.py` Files

```
src/moves_cli/modules/__init__.py
src/moves_cli/modules/presentation/__init__.py
src/moves_cli/modules/speaker/__init__.py   ← boş değil, SpeakerManager burada
```

---

## Implementation Order

Bağımlılık sırasına göre — bağımlılıklar önce:

```
1.  ml_models.py                       (yalnızca models + config'e bağımlı)
2.  models.py                          (Protocol'ler + UIData + ControllerState)
3.  utils/hasher.py                    (bağımsız)
4.  utils/formatters.py               (text_normalizer absorbsiyonu)
5.  modules/presentation/display.py    (models'e bağımlı)
6.  modules/presentation/navigator.py  (models'e bağımlı)
7.  modules/presentation/chunks.py     (models + utils'e bağımlı)
8.  modules/presentation/similarity.py (models + ml_models'e bağımlı)
9.  modules/presentation/pipeline.py   (models + ml_models + config'e bağımlı)
10. modules/presentation/model_manager.py (ml_models'e bağımlı)
11. modules/speaker/google.py          (stdlib + httpx)
12. modules/speaker/processor.py       (models'e bağımlı)
13. modules/speaker/__init__.py        (models + utils + processor'a bağımlı)
14. modules/settings.py               (models + utils'e bağımlı)
15. core.py                            (models + presentation/*'e bağımlı)
16. cli.py                             (tüm modules + core — composition root)
17. Eski dosyaları sil, core/ klasörünü kaldır
```

---

## Unchanged Files

```
src/moves_cli/config.py               # Untouched
src/moves_cli/utils/data_handler.py   # Untouched
src/moves_cli/utils/id_generator.py   # Untouched
src/moves_cli/data/                   # Untouched — package data
pyproject.toml                        # Untouched — only file structure changes
```

---

## Summary Change Table

| Current                                                           | Target                                  | Type                                    |
| ----------------------------------------------------------------- | --------------------------------------- | --------------------------------------- |
| `models.py`                                                       | `models.py` + `ml_models.py`            | Split                                   |
| `core/presentation_controller.py`                                 | `core.py` + `modules/presentation/*`    | Decomposition                           |
| `core/components/chunk_producer.py`                               | `modules/presentation/chunks.py`        | Move                                    |
| `core/components/similarity_calculator.py` + `similarity_units/*` | `modules/presentation/similarity.py`    | Merge + Move                            |
| `core/speaker_manager.py`                                         | `modules/speaker/__init__.py`           | Move                                    |
| `core/components/section_producer.py`                             | `modules/speaker/processor.py`          | Move                                    |
| `core/settings_editor.py`                                         | `modules/settings.py`                   | Move                                    |
| `utils/google_handler.py`                                         | `modules/speaker/google.py`             | Move                                    |
| `utils/model_preparer.py`                                         | `modules/presentation/model_manager.py` | Move                                    |
| `utils/calculate_hash.py`                                         | `utils/hasher.py`                       | Simplification                          |
| `utils/text_normalizer.py`                                        | `utils/formatters.py` (absorbed)        | Merge                                   |
| —                                                                 | `ml_models.py`                          | New                                     |
| —                                                                 | `core.py`                               | New                                     |
| —                                                                 | `modules/presentation/display.py`       | New                                     |
| —                                                                 | `modules/presentation/navigator.py`     | New (narrowed navigator responsibility) |
| —                                                                 | `modules/presentation/pipeline.py`      | New                                     |
| — (`ChunkStore` Protocol)                                         | `models.py` (as Protocol port)          | New Protocol                            |

---

## Numeric Comparison

| Metric                          | Current                                           | Target                       |
| ------------------------------- | ------------------------------------------------- | ---------------------------- |
| Total file count                | 16                                                | 19                           |
| Longest file                    | 909 lines (`cli.py`)                              | ~350 lines (`core.py`, est.) |
| `core/` depth                   | 4 levels                                          | 0 (removed)                  |
| Single-responsibility violation | `presentation_controller.py` (7 responsibilities) | None                         |
| Testable component              | 0 (concrete dependencies)                         | 5 (Protocol-mockable)        |
