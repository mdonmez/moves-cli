# moves

> **Presentation control, reimagined.** Hands-free slide navigation using offline speech recognition and hybrid similarity matching.

[![moves](https://img.shields.io/badge/moves-003399?style=flat-square&color=003399&logoColor=ffffff)](https://github.com/mdonmez/moves-cli)
[![Python](https://img.shields.io/badge/python-3.13-3776ab?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-d32f2f?style=flat-square&logo=gnu&logoColor=white)](https://www.gnu.org/licenses/gpl-3.0)

## Overview

`moves` is a CLI tool that automates slide advancement during presentations based on your spoken words. By analyzing your presentation and corresponding transcript, it learns what you say during each slide, then uses speech recognition to detect when you move between sections—all **offline** and **hands-free**.

### Key Features

- **Offline speech recognition** – Uses Sherpa-ONNX with NeMo Streaming Fast Conformer models; your voice stays on your machine
- **Hybrid similarity engine** – Combines semantic embeddings (all-MiniLM-L6-v2) and phonetic matching (Metaphone + RapidFuzz) for accurate slide detection
- **Multi-format support** – Extracts content from PDF, DOCX, PPTX, and TXT files using 100% free, open-source libraries
- **Automatic section generation** – Uses LLM (via LiteLLM) to analyze transcript and generate speech content for each slide
- **Manual mode** – Generate empty templates to fill in yourself, no LLM required
- **Speaker profiles** – Save and reuse multiple presentations with different speakers
- **Google Drive integration** – Load presentations and transcripts directly from Google Drive URLs
- **Interactive terminal UI** – Real-time Rich-powered dashboard showing current slide, similarity scores, VAD status, and recognized speech
- **Voice Activity Detection** – Silero VAD filters silence and background noise for better recognition

## How It Works

1. **Prepare** – Extract slides from your presentation, analyze your transcript, generate speech content for each slide
2. **Control** – Start live voice-controlled navigation with real-time speech matching
3. **Manage** – Add, edit, list, show, and delete speaker profiles

## Installation

### Requirements
- Python 3.13+
- `uv` package manager (recommended) or pip
- Microphone for presentation mode

### Install from PyPI

```bash
# Using uv (recommended)
uv tool install moves-cli

# Or using pip
pip install moves-cli

# Verify installation
moves --version
```

## Quick Start

### 1. Add a Speaker Profile

```bash
# Using local files (PDF, DOCX, PPTX, or TXT supported)
moves speaker add MyPresentation /path/to/presentation.pdf /path/to/transcript.txt

# Or using Google Drive URLs
moves speaker add MyPresentation \
  "https://drive.google.com/file/d/.../view?usp=sharing" \
  "https://drive.google.com/file/d/.../view?usp=sharing"
```

### 2. Configure LLM (for automatic section generation)

```bash
# Set your LLM model (Gemini is free and recommended)
moves settings set model gemini/gemini-2.5-flash-lite

# Set your API key (input is hidden for security)
moves settings set key
```

Get a free API key from [Google AI Studio](https://aistudio.google.com/app/apikey).

> **Tip**: Skip LLM setup entirely with `--manual` mode to generate empty templates you edit yourself.

### 3. Prepare the Speaker

```bash
# Auto mode (uses LLM to generate speech content)
moves speaker prepare MyPresentation

# Manual mode (creates empty template - no LLM needed)
moves speaker prepare MyPresentation --manual
```

If using manual mode, edit `~/.moves/speakers/<speaker-id>/sections.md` to add your speech content for each slide.

### 4. Start Presentation Control

```bash
moves present MyPresentation
```

**Keyboard shortcuts during presentation:**

| Key | Action |
|-----|--------|
| `←` / `→` | Previous / Next slide |
| `M` | Pause/Resume microphone |
| `Q` | Quit presentation |
| `Ctrl+C` | Force exit |

The system listens to your speech and automatically advances slides when it detects content matching the next section.

### Presentation States

- **ACTIVE** – Listening and auto-navigating based on speech
- **PAUSED** – Microphone muted, keyboard navigation still works
- **LOCKED** – Manual navigation detected, auto-advance disabled until consensus

## Documentation

- **[Getting Started Guide](docs/GETTING_STARTED.md)** – Detailed walkthrough with examples
- **[Architecture](docs/ARCHITECTURE.md)** – How the system works internally
- **[CLI Reference](docs/CLI_REFERENCE.md)** – Complete command documentation
- **[Configuration Guide](docs/CONFIGURATION.md)** – Setup LLM, API keys, and tuning
- **[Development Guide](docs/DEVELOPMENT.md)** – For contributors and developers
- **[Documentation Index](docs/INDEX.md)** – Navigate all documentation

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│ PREPARATION PHASE                                       │
├─────────────────────────────────────────────────────────┤
│ • Extract content from presentation (PDF/DOCX/PPTX/TXT) │
│ • Parse transcript text                                 │
│ • Generate speech content per slide (LLM or manual)     │
│ • Create sections.md with slide-speech mapping          │
│ • Compute file hashes for change detection              │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│ PRESENTATION PHASE                                      │
├─────────────────────────────────────────────────────────┤
│ • Microphone stream → Voice Activity Detection (VAD)    │
│ • VAD filters silence → Speech-to-Text (offline STT)    │
│ • Text normalization → Sliding window buffer            │
│ • Hybrid similarity matching:                           │
│   ├─ Semantic: all-MiniLM-L6-v2 embeddings (60%)       │
│   └─ Phonetic: Metaphone + fuzzy matching (40%)        │
│ • Auto-advance when similarity ≥ 70% threshold          │
│ • Rich terminal UI with real-time feedback              │
└─────────────────────────────────────────────────────────┘
```

## Supported File Formats

All formats use **100% free, open-source libraries** – no commercial licenses required:

| Format | Library | Notes |
|--------|---------|-------|
| **PDF** | PyMuPDF4LLM | LLM-optimized markdown extraction |
| **DOCX** | python-docx | Microsoft Word documents |
| **PPTX** | python-pptx | PowerPoint presentations |
| **TXT** | Native | Plain text files |

## Data Storage

All data is stored in `~/.moves/`:

```
~/.moves/
├── settings.toml              # LLM model configuration
├── ml_models/                 # Downloaded ONNX models (~500MB)
│   ├── all-MiniLM-L6-v2_quint8_avx2/    # Embedding model
│   ├── nemo-streaming-stt-480ms-int8/    # STT model
│   └── silero-vad-int8/                  # VAD model
└── speakers/
    └── <speaker-id>/
        ├── speaker.yaml       # Speaker metadata and hashes
        └── sections.md        # Speech content for each slide
```

API keys are stored securely in the system keyring (Windows Credential Manager / macOS Keychain / Linux Secret Service).

## Common Issues & Solutions

### No speakers found
```bash
moves speaker list
# If empty, create a speaker:
moves speaker add MyTalk presentation.pdf transcript.txt
```

### LLM configuration error
```bash
# Check current settings
moves settings list

# Use manual mode (no LLM required)
moves speaker prepare MyTalk --manual
```

### Speech not being recognized
- Speak clearly at a normal pace
- Ensure `sections.md` contains the expected speech content
- Check microphone in system settings
- Try a quieter environment

### Source files changed warning
The tool detects when your presentation or transcript files have changed since last preparation. Re-prepare to update:
```bash
moves speaker prepare MyTalk
```

## Performance Characteristics

| Aspect | Details |
|--------|---------|
| **Audio Processing** | ~32ms analysis windows (VAD_WINDOW_SIZE: 512 samples at 16kHz) |
| **Similarity Threshold** | 70% combined score triggers auto-advance |
| **Chunk Window** | 12 words per matching chunk |
| **Models Download** | ~500MB one-time download on first use |
| **Memory Usage** | ~200-300MB during presentation |
| **Offline Capable** | Fully offline after models are downloaded (except LLM preparation) |

## Configuration Options

Key tuning parameters in `config.py`:

```python
SEMANTIC_WEIGHT = 0.6          # Semantic vs phonetic balance
PHONETIC_WEIGHT = 0.4
SIMILARITY_THRESHOLD = 0.7     # Minimum score to auto-advance
WINDOW_SIZE = 12               # Words per matching chunk

VAD_THRESHOLD = 0.35           # Voice activity sensitivity
VAD_MIN_SILENCE = 0.5          # Seconds of silence to end speech
VAD_MIN_SPEECH = 0.1           # Minimum speech duration to detect
```

See [Configuration Guide](docs/CONFIGURATION.md) for detailed tuning instructions.

## Supported LLM Providers

Via [LiteLLM](https://docs.litellm.ai/), moves supports 100+ LLM providers:

| Provider | Model Example | Cost |
|----------|--------------|------|
| **Google Gemini** | `gemini/gemini-2.5-flash-lite` | Free tier available |
| **OpenAI** | `gpt-4o-mini` | Pay-as-you-go |
| **Anthropic** | `claude-3-5-sonnet` | Pay-as-you-go |
| **Groq** | `groq/mixtral-8x7b-32768` | Free tier available |

See [Configuration Guide](docs/CONFIGURATION.md#llm-providers) for setup instructions.

## Project Status

**Active Development** – This tool is being actively developed. Feedback and contributions are welcome!

## License

Licensed under the **GNU General Public License v3.0**. See [LICENSE](./LICENSE) for details.

## Contributing

Contributions are welcome! See [Development Guide](docs/DEVELOPMENT.md) for setup instructions.

---

**Questions?** Check the [FAQ](docs/GETTING_STARTED.md#frequently-asked-questions) or [open an issue](https://github.com/mdonmez/moves-cli/issues).
