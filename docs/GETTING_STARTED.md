# Getting Started Guide

Step-by-step guide to using `moves` for hands-free presentation control.

## Table of Contents

1. [Installation](#installation)
2. [Understanding the Data Directory](#understanding-the-data-directory)
3. [Creating Your First Speaker](#creating-your-first-speaker)
4. [Preparing for Presentation](#preparing-for-presentation)
5. [Giving a Presentation](#giving-a-presentation)
6. [Managing Speakers](#managing-speakers)
7. [Troubleshooting](#troubleshooting)
8. [FAQ](#frequently-asked-questions)

## Installation

### Step 1: Install Python 3.13+

`moves` requires Python 3.13 or newer.

**Windows:**
1. Download from [python.org](https://www.python.org/downloads/)
2. Run installer and check "Add Python to PATH"
3. Verify: `python --version`

**macOS/Linux:**
```bash
# Using pyenv (recommended)
pyenv install 3.13
pyenv global 3.13

# Or using your package manager
```

### Step 2: Install `uv` Package Manager (Recommended)

```bash
pip install uv
```

Or use pip directly if you prefer.

### Step 3: Install `moves-cli`

```bash
# Using uv (recommended)
uv tool install moves-cli

# Or using pip
pip install moves-cli
```

### Step 4: Verify Installation

```bash
moves --version
```

Expected output: `moves-cli version 0.3.3`

---

## Understanding the Data Directory

All moves data is stored in `~/.moves/`:

```
~/.moves/
├── settings.toml              # LLM model configuration
├── ml_models/                 # ONNX models (downloaded on first use)
│   ├── all-MiniLM-L6-v2_quint8_avx2/   # Semantic embedding model (~90MB)
│   ├── nemo-streaming-stt-480ms-int8/   # Speech-to-text model (~130MB)
│   └── silero-vad-int8/                 # Voice activity detection (~2MB)
└── speakers/                  # Speaker profiles
    └── <speaker-id>/
        ├── speaker.yaml       # Metadata and file hashes
        └── sections.md        # Speech content for each slide
```

Check this directory:
```bash
# Windows
dir %USERPROFILE%\.moves

# macOS/Linux
ls ~/.moves
```

---

## Creating Your First Speaker

### Gather Your Materials

You need:
1. **Presentation file** – PDF, DOCX, PPTX, or TXT format
2. **Transcript file** – Text file with what you plan to say

**Supported formats** (all 100% free, no commercial licenses):
| Format | Library | Notes |
|--------|---------|-------|
| PDF | PyMuPDF4LLM | Optimized for LLM processing |
| DOCX | python-docx | Microsoft Word documents |
| PPTX | python-pptx | PowerPoint presentations |
| TXT | Native | Plain text files |

### Transcript Format

Your transcript should roughly align with your slides:

```text
Hello everyone, thanks for coming today. I'm excited to share this project with you.

This is the overview. We have three main topics to cover: architecture, implementation, and results.

First, let's dive into the architecture. The system consists of several key components...
```

### Create the Speaker Profile

```bash
# Using local files
moves speaker add MyTalk /path/to/presentation.pdf /path/to/transcript.txt

# Using PowerPoint
moves speaker add MyTalk /path/to/presentation.pptx /path/to/transcript.txt

# Using Word document
moves speaker add MyTalk /path/to/document.docx /path/to/notes.txt
```

Output:
```
Speaker MyTalk (a1b2c) has been successfully added.

  Data directory: ~/.moves/speakers/a1b2c
  Presentation source: /path/to/presentation.pdf
  Transcript source: /path/to/transcript.txt
```

### Using Google Drive URLs

If your files are on Google Drive:

```bash
moves speaker add MyTalk \
  "https://drive.google.com/file/d/ABC123/view?usp=sharing" \
  "https://drive.google.com/file/d/DEF456/view?usp=sharing"
```

**Requirements:**
- Files must be shared ("Anyone with the link can view")
- Google Docs/Slides are exported as PDF automatically

---

## Preparing for Presentation

### Option A: Automatic Preparation (Uses LLM)

The LLM analyzes your transcript and generates speech content for each slide.

#### 1. Configure Your LLM

**Google Gemini (Free, Recommended):**
```bash
# Get free API key from https://aistudio.google.com/app/apikey
moves settings set model gemini/gemini-2.5-flash-lite
moves settings set key
# Paste your API key when prompted (hidden input)
```

**OpenAI:**
```bash
moves settings set model gpt-4o-mini
moves settings set key
# Paste your OpenAI API key
```

**Verify configuration:**
```bash
moves settings list
```

#### 2. Run Preparation

```bash
moves speaker prepare MyTalk
```

Output:
```
Preparing 1 speaker(s).

MyTalk (a1b2c)
  Presentation: presentation.pdf (15 slides)
  Transcript: transcript.txt
  Estimated tokens: ~2,500
  Estimated cost: ~$0.0001 (gemini/gemini-2.5-flash-lite)

Proceed? [Y/n]: y

Speaker MyTalk (a1b2c) prepared.

  Sections created: 15
  Processing time: 45.3s
  Sections file: ~/.moves/speakers/a1b2c/sections.md
```

### Option B: Manual Preparation (No LLM)

If you don't want to use an LLM:

```bash
moves speaker prepare MyTalk --manual
```

This creates an empty template. Edit the sections file:

```bash
# Windows
notepad %USERPROFILE%\.moves\speakers\a1b2c\sections.md

# macOS/Linux
nano ~/.moves/speakers/a1b2c/sections.md
```

The template format:
```markdown
# 1. Slide

Add speech content here for slide 1...

# 2. Slide

Add speech content here for slide 2...

# 3. Slide

Add speech content here for slide 3...
```

Fill in each section with what you'll say during that slide:
```markdown
# 1. Slide

Hello everyone, thanks for coming today. I'm excited to share this project with you.

# 2. Slide

This is the overview. We have three main topics to cover: architecture, implementation, and results.

# 3. Slide

First, let's dive into the architecture. The system consists of several key components that work together.
```

---

## Giving a Presentation

### Start the Presentation

```bash
moves present MyTalk
```

The first run downloads ONNX models (~500MB total):
- Speech-to-text model (NeMo Streaming Fast Conformer)
- Voice activity detection (Silero VAD)
- Semantic embedding model (all-MiniLM-L6-v2)

### The Dashboard

You'll see a Rich terminal UI showing:
- **State**: ACTIVE, PAUSED, or LOCKED
- **Slide**: Current slide / total slides
- **Similarity**: Match score percentage
- **Speech**: Recognized words from your microphone
- **Match**: Content from current section

### Keyboard Controls

| Key | Action |
|-----|--------|
| `←` | Previous slide |
| `→` | Next slide |
| `M` | Toggle pause/resume microphone |
| `Q` | Quit presentation |
| `Ctrl+C` | Force exit |

### States Explained

- **ACTIVE** – Listening and auto-navigating. When speech matches next section content above 70% threshold, slide advances automatically.
- **PAUSED** – Microphone muted. Use for Q&A or breaks. Keyboard navigation still works.
- **LOCKED** – Manual navigation detected (you pressed arrow keys). Auto-advance disabled until speech matches current section again.

### Tips for Best Results

1. **Speak clearly** – Normal conversational pace works best
2. **Match your script** – Use similar phrasing to what's in sections.md
3. **Quiet environment** – Less background noise = better recognition
4. **Test first** – Do a dry run before your actual presentation
5. **Use pauses strategically** – Press M during questions or discussions

### Exit Presentation

Press `Q` or `Ctrl+C` to exit:
```
Presentation ended.
```

---

## Managing Speakers

### List All Speakers

```bash
moves speaker list
```

Output:
```
There are 2 registered speaker(s).

NAME       ID      STATUS      LAST PROCESSED
MyTalk     a1b2c   Ready       2024-01-15 14:30
OtherTalk  d1e2f   Not Ready   N/A

Data directory: ~/.moves/speakers
```

**Status meanings:**
- `Ready` – Prepared and has sections.md
- `Not Ready` – Added but not yet prepared

### Show Speaker Details

```bash
moves speaker show MyTalk
```

Output:
```
Showing details for MyTalk (a1b2c)

  Name: MyTalk
  ID: a1b2c
  Status: Ready
  Last Processed: 2024-01-15 14:30
  Data directory: ~/.moves/speakers/a1b2c
  Sections file: ~/.moves/speakers/a1b2c/sections.md
  Presentation source: /path/to/presentation.pdf
  Transcript source: /path/to/transcript.txt
```

### Update Speaker Files

If you update your presentation or transcript:

```bash
# Update presentation only
moves speaker edit MyTalk --presentation /new/path/to/presentation.pdf

# Update transcript only
moves speaker edit MyTalk --transcript /new/path/to/transcript.txt

# Update both
moves speaker edit MyTalk -p /new/presentation.pdf -t /new/transcript.txt
```

Then re-prepare:
```bash
moves speaker prepare MyTalk
```

### Delete a Speaker

```bash
# Delete single speaker
moves speaker delete MyTalk

# Delete without confirmation
moves speaker delete MyTalk --yes

# Delete all speakers
moves speaker delete --all
```

---

## Troubleshooting

### "No speakers found"

**Problem:** `moves speaker list` shows no speakers.

**Solution:**
```bash
# Check if any exist
ls ~/.moves/speakers/

# Create one
moves speaker add MyTalk presentation.pdf transcript.txt
```

### "Speaker has not been prepared yet"

**Problem:** Can't present because sections.md doesn't exist.

**Solution:**
```bash
moves speaker prepare MyTalk

# Or use manual mode
moves speaker prepare MyTalk --manual
```

### "LLM model not configured"

**Problem:** Automatic preparation requires LLM configuration.

**Solutions:**
```bash
# Option 1: Configure LLM
moves settings set model gemini/gemini-2.5-flash-lite
moves settings set key
moves speaker prepare MyTalk

# Option 2: Use manual mode (no LLM)
moves speaker prepare MyTalk --manual
```

### Microphone Not Working

**Problem:** No speech being recognized.

**Solutions:**
1. Check system microphone settings
2. Verify microphone is not muted
3. Test microphone in another application
4. Try a different microphone

### Speech Not Matching

**Problem:** Speaking but slides don't advance.

**Causes & Solutions:**
1. **Content mismatch** – Your sections.md may not match what you're saying
   - Edit sections.md to match your actual speech
2. **Low similarity** – Threshold is 70%
   - Speak more clearly or closely match the section content
3. **Background noise** – VAD might filter your speech
   - Try a quieter environment

### Source Files Changed Warning

**Problem:** Warning that files have changed since last preparation.

**Solution:**
```bash
# Re-prepare with updated files
moves speaker prepare MyTalk

# Or continue with old data
# Choose 'y' when prompted
```

### Models Taking Too Long

**Problem:** First run is slow.

**Explanation:** ONNX models (~500MB) are downloaded on first use.

**Solution:** Wait for downloads to complete (5-10 minutes typical). Progress is shown.

---

## Frequently Asked Questions

### Q: Is my voice data sent to the cloud?

**A:** No. Speech recognition happens **100% offline** using local ONNX models. Your voice never leaves your machine. The only cloud call is the optional LLM for section generation, which can be skipped using `--manual` mode.

### Q: What file formats are supported?

**A:** Four formats using 100% free, open-source libraries:
- **PDF** – PyMuPDF4LLM
- **DOCX** – python-docx
- **PPTX** – python-pptx
- **TXT** – Native

No commercial licenses required.

### Q: What if my transcript doesn't perfectly match my slides?

**A:** That's fine! The system uses hybrid similarity matching (semantic + phonetic) to handle variations. Tips:
- Add approximate content for each slide
- Use keyboard shortcuts for manual backup
- Edit sections.md to better match what you actually say

### Q: Can I have multiple presentations?

**A:** Yes! Create multiple speakers:
```bash
moves speaker add Talk1 talk1.pdf transcript1.txt
moves speaker add Talk2 talk2.pdf transcript2.txt

moves present Talk1  # First presentation
moves present Talk2  # Different presentation
```

### Q: How accurate is the slide detection?

**A:** Depends on:
- **Content match** – How well sections.md matches your speech
- **Speech clarity** – Clear speech = better recognition
- **Environment** – Quiet rooms work best

Typical: 85-95% automatic advances with keyboard backup.

### Q: Can I use a different LLM provider?

**A:** Yes! Any provider supported by [LiteLLM](https://docs.litellm.ai/):
```bash
moves settings set model claude-3-5-sonnet
moves settings set model gpt-4o
moves settings set model groq/mixtral-8x7b-32768
```

See [Configuration Guide](CONFIGURATION.md) for full list.

### Q: What if I mess up sections.md?

**A:** Re-prepare to regenerate:
```bash
moves speaker prepare MyTalk
```

This overwrites existing content. Keep a backup if you have manual edits.

### Q: Can I use this without internet?

**A:** **Presentation:** Yes, fully offline after models are downloaded.
**Preparation:** Requires internet for LLM, unless using `--manual` mode.

### Q: How much disk space is needed?

**A:**
- Models: ~500MB (one-time download)
- Speaker data: ~1-10MB per speaker
- Total: ~500MB + speaker data

### Q: How do I update my presentation slides?

**A:**
```bash
# Update the presentation file
moves speaker edit MyTalk --presentation /new/presentation.pdf

# Re-prepare to regenerate sections
moves speaker prepare MyTalk
```

### Q: What happens if I interrupt preparation?

**A:** The process stops. Run again to restart:
```bash
moves speaker prepare MyTalk
```

### Q: Can I edit the generated sections?

**A:** Yes! After preparation, edit the file:
```bash
# Open sections.md in your editor
nano ~/.moves/speakers/a1b2c/sections.md
```

The system will detect the changes and prompt you when presenting.

### Q: What are the keyboard shortcuts during presentation?

**A:**
| Key | Action |
|-----|--------|
| `←` | Previous slide |
| `→` | Next slide |
| `M` | Pause/Resume microphone |
| `Q` | Quit |
| `Ctrl+C` | Force exit |

### Q: How does the similarity matching work?

**A:** Two methods combined:
1. **Semantic (60%)** – all-MiniLM-L6-v2 embeddings compare meaning
2. **Phonetic (40%)** – Metaphone + RapidFuzz for sound-alike matching

Score ≥ 70% triggers auto-advance.

### Q: Why did my slide advance incorrectly?

**A:** Possible causes:
- Speech matched a different section's content
- Sections have similar content
- Threshold set too low

Solution: Edit sections.md to make each section more distinct.

---

For more details, see:
- [Architecture Guide](ARCHITECTURE.md) – How the system works
- [CLI Reference](CLI_REFERENCE.md) – All commands
- [Configuration Guide](CONFIGURATION.md) – Tuning options
