# moves

> **Presentation control, reimagined.** Hands-free slide navigation using offline speech recognition and hybrid similarity matching.

[![moves](https://img.shields.io/badge/moves-003399?style=flat-square&color=003399&logoColor=ffffff)](https://github.com/mdonmez/moves-cli)
[![Python](https://img.shields.io/badge/python-3.13-3776ab?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-d32f2f?style=flat-square&logo=gnu&logoColor=white)](https://www.gnu.org/licenses/gpl-3.0)

## Overview

`moves` is a CLI tool that automates slide advancement during presentations based on your spoken words. By analyzing your presentation and corresponding transcript, it learns what you say during each slide, then uses speech recognition to detect when you move between sections—all **offline** and **hands-free**.

### Key Features

- **Offline speech recognition** – Uses local ONNX models; your voice stays on your machine
- **Hybrid similarity engine** – Combines semantic and phonetic matching for accurate slide detection
- **Automatic slide generation** – Extracts slides from PDF presentations and generates templates with LLM assistance (optional manual mode)
- **Speaker profiles** – Save and reuse multiple presentations with different speakers
- **Flexible source handling** – Load presentations and transcripts from local files or Google Drive
- **Interactive terminal UI** – Real-time feedback with Rich-powered dashboard showing current slide, similarity scores, and system state

## What It Does

1. **Prepare** – Extract slides from a PDF, analyze your transcript, generate sections with speech content
2. **Control** – Start live voice-controlled navigation with keyboard backups
3. **Manage** – Add, edit, list, and delete speaker profiles

## Installation

### Requirements
- Python 3.13+
- `uv` package manager (or pip as fallback)

### Install from PyPI

```bash
uv tool install moves-cli
# or: pip install moves-cli

# Verify installation
moves --version
```

## Quick Start

### 1. Add a Speaker Profile

```bash
moves speaker add MyPresentation \
  /path/to/presentation.pdf \
  /path/to/transcript.txt
```

You can also use Google Drive URLs (the tool handles authentication):

```bash
moves speaker add MyPresentation \
  "https://drive.google.com/file/d/.../view?usp=sharing" \
  "https://drive.google.com/file/d/.../view?usp=sharing"
```

### 2. Configure LLM (for automatic section generation)

```bash
# Set your LLM model (e.g., Gemini 2.5 Flash)
moves settings set model gemini/gemini-2.5-flash-lite

# Set your API key (securely prompted)
moves settings set key
```

> **Tip**: You can skip LLM setup and use `--manual` mode to generate empty templates you edit yourself.

### 3. Prepare the Speaker

Generate sections (speech content for each slide):

```bash
# Auto mode (uses LLM)
moves speaker prepare MyPresentation

# Or manual mode (empty template to edit yourself)
moves speaker prepare MyPresentation --manual
```

Edit `~/.moves/speakers/<speaker-id>/sections.md` to add your spoken words for each slide if using manual mode.

### 4. Start Presentation Control

```bash
moves present MyPresentation
```

**Keyboard shortcuts during presentation:**
- `←` / `→` – Previous / Next slide (manual navigation)
- `Ins` – Pause/Resume microphone
- `Ctrl+C` – Exit

The tool listens to your speech and automatically advances slides when it detects you've moved to new content.

## Documentation

- **[Getting Started Guide](docs/GETTING_STARTED.md)** – Detailed walkthrough with examples
- **[Architecture](docs/ARCHITECTURE.md)** – How the system works internally
- **[CLI Reference](docs/CLI_REFERENCE.md)** – Complete command documentation
- **[Configuration Guide](docs/CONFIGURATION.md)** – Setup LLM, API keys, and more
- **[Development Guide](docs/DEVELOPMENT.md)** – For contributors and developers

## How It Works

```
┌─────────────────────────────────────────────────────────┐
│ 1. PREPARATION PHASE                                    │
├─────────────────────────────────────────────────────────┤
│ • Extract slides from PDF                               │
│ • Analyze transcript to identify sections               │
│ • Generate speech content for each slide (LLM or manual)│
│ • Create sections.md file with structure                │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│ 2. PRESENTATION PHASE                                   │
├─────────────────────────────────────────────────────────┤
│ • Start microphone stream (real-time audio input)       │
│ • Voice Activity Detector (VAD) filters silence         │
│ • Speech Recognition converts audio to text (offline)   │
│ • Similarity Engine matches text to chunks              │
│   ├─ Semantic similarity (embeddings)                   │
│   └─ Phonetic similarity (fuzzy matching)               │
│ • Auto-advance when high similarity match detected      │
└─────────────────────────────────────────────────────────┘
```

## Data Storage

All speaker data is stored in `~/.moves/`:

```
~/.moves/
├── settings.toml          # LLM model configuration
├── settings.key           # API key (Windows Credential Manager)
└── speakers/
    └── <speaker-id>/
        ├── speaker.yaml   # Speaker metadata
        └── sections.md    # Speech content for each slide
```

## Common Issues & Solutions

**No speakers found?**
```bash
moves speaker list
# Check ~/.moves/speakers/ directory exists
```

**Sections not being created?**
```bash
# Check LLM configuration
moves settings list

# Try manual mode (no LLM required)
moves speaker prepare MyPresentation --manual
```

**Microphone not detected?**
```bash
# Verify your system microphone works:
# Settings → Sound → Volume mixer (Windows)
# Then retry: moves present MyPresentation
```

**Speech not being recognized?**
- Speak clearly and at a normal pace
- Test microphone in a quiet environment
- Check that sections.md contains expected content

## Performance Notes

- **Offline processing** – No cloud calls except for LLM section generation
- **Real-time audio** – ~32ms analysis windows, responsive slide detection
- **Memory efficient** – Processed sections cached in `sections.md`
- **First run slower** – ONNX models (~500MB) downloaded on first use

## Project Status

**Active Development** – This tool is being actively developed and improved. Feedback and contributions are welcome.

## License

Licensed under the **GNU General Public License v3.0**. See [LICENSE](./LICENSE) for details.

## Contributing

Contributions are welcome! See [Development Guide](docs/DEVELOPMENT.md) for setup instructions.

---

**Questions?** Check the [FAQ in Getting Started](docs/GETTING_STARTED.md#frequently-asked-questions) or open an issue on GitHub.
