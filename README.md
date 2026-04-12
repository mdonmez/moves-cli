# moves

> **Presentation control, reimagined.** Hands-free slide navigation using offline speech recognition and hybrid similarity matching.

[![moves](https://img.shields.io/badge/moves-003399?style=flat-square&color=003399&logoColor=ffffff)](https://github.com/mdonmez/moves-cli)
[![Python](https://img.shields.io/badge/python-3.13-3776ab?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-d32f2f?style=flat-square&logo=gnu&logoColor=white)](https://www.gnu.org/licenses/gpl-3.0)

## _Regarding the stoppage of the development of the moves._

> [!IMPORTANT]
> _I built `moves` to solve the inevitable friction between natural human storytelling and the rigid mechanics of digital presentations. After months of coding, the project has reached its end. Not because of a technical failure, but because of a philosophical one._
>
> _Here is why I am stopping development of this project._
>
> ### The Engineering Illusion
>
> Technically, the current version (v0.3.3) does exactly what I wanted. It uses LLMs to structure a transcript, runs an offline Voice Activity Detector (VAD) to filter silence, feeds audio into a local Speech-to-Text model, and scores the transcription against slide chunks using both vector embeddings and phonetic algorithms. Building this has helped me develop my ability to assemble different parts, design architecture, and solve problems in general.
>
> But as I was planning the next massive update (`moves with intelligence`), I hit a wall. I realized the core premise of the app is deeply flawed in the real world.
>
> ### Main Problems
>
> **The input bottleneck**
>
> The system requires a static presentation file (PDF/PPTX) and a written transcript to function. In the real world, speakers use dynamic cloud tools like Canva or Microsoft 365 (moves have Google Workspace support but it is not enough), and they change their slides 5 minutes before walking on stage. Worse, demanding a written transcript is absurd; most speakers use rough bullet points or memorize their flow. For an event with 8 speakers, managing and re-processing these files locally becomes a logistical nightmare. It solves one problem by creating a much bigger one.
>
> **The offline-first lie and the LLM issue**
>
> I advertised this as an "offline-first" tool. That was only half true. While the live stage execution is offline, the mandatory preparation phase relies on LLMs to map transcripts to slides. (Even manual mode idea was trash!) This introduces API costs and painful processing times. If a speaker tweaks one slide backstage, the entire deck must be re-processed, or the user must manually intervene which is cumbersome. And the "offline" part requires a massive, undocumented 200MB download of ONNX models on the user's first run.
>
> **The user experience and system integration**
>
> The people running presentations at conferences are not developers working at terminals. Expecting them to configure Python, uv, manage API keys, and run CLI commands in a high-stress environment is unrealistic. However, even if I had created a web interface, the browser would prevent controlling other applications without an additional companion application. Therefore, I used `pynput` to simulate pressing physical keyboard keys. This is a fatal design flaw: If the person there clicks on Spotify or a system notification pops up, the window focus is lost and the AI starts sending “Next Slide” commands into the void.
>
> **Possible chain of failure**
>
> For moves to change just one slide, lots of things must work perfectly at the exact same millisecond:
>
> - Hardware (The microphone doesn't drop).
> - OS Audio Drivers (The buffer doesn't overflow).
> - VAD Model (Doesn't mistake a cough or applause for speech).
> - STT Model (Correctly transcribes heavily accented speech in real-time).
> - NLP Engine (Calculates the correct semantic/phonetic score instantly).
> - State Machine (The app isn't paused or locked).
> - Operating System (PowerPoint retains absolute window focus).
>
> If just one of these fails for a single second, the system collapses. Live events are pure chaos; a zero-fault-tolerance architecture cannot survive there.
>
> **Cost of errors**
>
> In machine learning, an accuracy rate of 95% or 99% is excellent. On a stage in front of 1,000 people, a 1% error rate is a disaster. If the motor selects the wrong slide due to an error in transcription or similarity scoring, everything ruins.
>
> **Inevitable Latency**
>
> When a human clicks a remote, the visual changes instantly with their speech. In my architecture, the audio is captured, VAD filters silence, STT transcribes, a chunk is formed, embeddings are generated, similarity is calculated, and an OS keypress is simulated. No matter how much I optimize the code, this pipeline will always take 500ms to 1 second. That slight delay completely destroys a speaker's natural rhythm.
>
> ### Biggest Epistemological Limit
>
> The biggest reason I am stopping this project is a fundamental mismatch between human causality and algorithmic prediction.
>
> moves relies on this assumption:
> **Speech (Cause) -> Slide Change (Effect)**  
> _(The system thinks: "The speaker is on these words, therefore current slide should be replaced with the next slide.")_
>
> But on a real stage, the causality is reversed:
> **Slide Change (Cause) -> Speech (Effect)**  
> _(The speaker clicks the remote, sees the new visual and immediately shapes their next sentence based on that visual cue.)_
>
> This is where the system collapses. moves tries to predict the intent to change a slide at `t=1` by analyzing the audio at `t=0`. However, the speaker makes the decision to speak at `t=2` based on the slide they will see at `t=1`. The system is trying to predict a future that hasn't even fully formed in the speaker's mind yet.
>
> This is not an engineering problem that can be solved with a better design. (Maybe issues above can be solved with better implementations, but this can't.) This is a limit of human-machine interaction. Unless we use something like Neuralink to read the motor cortex before the finger moves, no voice-based system will ever surpass the pure, lossless, and instantaneous translation of human intent provided by a simple remote control.
>
> ### Cancelled `moves with intelligence` Update
>
> I had planned a massive update to fix the issue of speakers deviating from their scripts. The plan was to rip out the semantic/phonetic engines and replace them with a ~350M parameters LLM fine-tuned via LoRA (unsloth distillation) using synthetic data from massive models like Claude, GPT etc.
>
> This would maintain a slide sliding window in the KV cache and analyze the incoming live STT stream at every word, enabling it to quickly think through and execute action commands as learned from the large model without requiring a transcript.
>
> It sounded perfect in theory, but I killed it without writing a single line of code due to these realities:
>
> - Running an LLM inferencing loop thousands of times during a presentation will overheat any entry-level laptop (MacBook Air, standard Dell/HP) and also end up the battery immediately. It will never maintain the required 100+ TPS while a presentation software and other apps are open.
> - Even with a fixed seed at 0 degrees, the 350M model is not 100% reliable. No matter how much reasoning we teach large models about edge cases, missing an edge case in a live setting was unacceptable.
> - Deploying `llama.cpp` requires a nightmare of vendor-specific runtimes (Vulkan, Metal, CPU fallbacks) that defeats the purpose of a simple CLI tool.
> - This time, we would again need an LLM to generate detailed explanations to convey the slide data to a small model.
>
> ### Final Thoughts
>
> _The repository will remain here as a legacy of searches such as real-time offline STT, LLM, semantic, and phonetic similarity algorithms in Python. I will try to maintain its current state and update dependencies as much as I can, but no new features will be added._
>
> **Thank you to everyone who checked it out.**

---

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

1. **Prepare** – Extract slides from a PDF, DOCX, or PPTX; analyze your transcript; generate sections with speech content (LLM-assisted or manual)
2. **Control** – Start live voice-controlled navigation with keyboard backups and a real-time Rich dashboard
3. **Manage** – Add, edit, show, list, and delete speaker profiles

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

Supported formats: **PDF**, **DOCX**, **PPTX** for presentations; **PDF**, **DOCX** for transcripts.

You can also use Google Drive / Google Docs / Google Slides URLs (no authentication needed — file must be shared publicly):

```bash
moves speaker add MyPresentation \
  "https://drive.google.com/file/d/.../view?usp=sharing" \
  "https://drive.google.com/file/d/.../view?usp=sharing"
```

To inspect a speaker's details:

```bash
moves speaker show MyPresentation
```

### 2. Configure LLM (for automatic section generation)

```bash
# Set your LLM model (e.g., Gemini 2.5 Flash)
moves settings set model gemini/gemini-2.5-flash-lite

# Set LLM API format: chat | responses | auto
moves settings set format chat

# Optional: set base URL (used when provided)
moves settings set base_url https://your-openai-compatible-endpoint/v1

# Set your API key (securely prompted)
moves settings set key
```

> **Tip**: You can skip LLM setup and use `--manual` mode to generate empty templates you fill in yourself. See https://models.litellm.ai/ for all supported model providers.

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
- `M` – Pause/Resume microphone
- `Q` – Exit

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
│ • Extract slides from PDF / DOCX / PPTX                 │
│ • Analyze transcript (PDF / DOCX / plain text)          │
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
├── settings.toml          # LLM model + API format + optional base URL configuration
│                          # API key stored in system keyring (Windows Credential Manager)
└── speakers/
    └── <speaker-id>/
        ├── speaker.yaml   # Speaker metadata and file hashes
        └── sections.md    # Speech content for each slide
```

The API key is **never** written to disk — it is stored and retrieved via the OS keyring (`keyring` library).

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

- **Offline processing** – No cloud calls during live presentation; LLM is only used during the preparation phase
- **Real-time audio** – ~32ms VAD analysis windows (512 samples at 16 kHz), responsive slide detection
- **Memory efficient** – Processed sections cached in `sections.md`; chunk embeddings precomputed at startup
- **First run slower** – Three ONNX models are downloaded on first use: VAD (silero-vad-int8, ~208 KB), STT (NeMo streaming conformer, int8), and embeddings (all-MiniLM-L6-v2, int8 avx2).
- **Stale-data detection** – xxhash (xxh3_64) checksums on presentation, transcript, and sections files; warns if sources changed since last prepare

## CLI Reference

| Command                                                        | Description                               |
| -------------------------------------------------------------- | ----------------------------------------- |
| `moves speaker add <name> <pres> <trans>`                      | Create speaker profile                    |
| `moves speaker edit <speaker> [--presentation] [--transcript]` | Update source files                       |
| `moves speaker list`                                           | List all speakers and their status        |
| `moves speaker show <speaker>`                                 | Show detailed speaker info                |
| `moves speaker prepare <speaker> [--manual] [--all] [--yes]`   | Generate sections (LLM or empty template) |
| `moves speaker delete <speaker> [--all] [--yes]`               | Delete speaker(s)                         |
| `moves present <speaker>`                                      | Start live voice-controlled presentation  |
| `moves settings list [--show]`                                 | Show current configuration                |
| `moves settings set model <model>`                             | Set LLM model                             |
| `moves settings set format <chat\|responses\|auto>`          | Set LLM API format                        |
| `moves settings set base_url <url>`                            | Set optional LLM base URL                 |
| `moves settings set key`                                       | Set API key (interactive, hidden input)   |
| `moves settings unset <key>`                                   | Reset a setting to its default            |

## Contributing

Contributions are closed for this project, read above.

## License

Licensed under the **GNU General Public License v3.0**. See [LICENSE](./LICENSE) for details.
