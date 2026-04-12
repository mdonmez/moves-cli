# Getting Started Guide

This guide walks you through using `moves` from installation to giving your first hands-free presentation.

## Table of Contents

1. [Installation](#installation)
2. [Initial Setup](#initial-setup)
3. [Creating Your First Speaker](#creating-your-first-speaker)
4. [Preparing for Presentation](#preparing-for-presentation)
5. [Giving a Presentation](#giving-a-presentation)
6. [Managing Speakers](#managing-speakers)
7. [Troubleshooting](#troubleshooting)
8. [FAQ](#frequently-asked-questions)

## Installation

### Step 1: Install Python

`moves` requires Python 3.13 or newer.

**On Windows:**
1. Download from [python.org](https://www.python.org/downloads/)
2. Run installer, check "Add Python to PATH"
3. Verify: Open PowerShell and type `python --version`

### Step 2: Install `uv` Package Manager

```powershell
pip install uv
```

Or use your preferred package manager. `uv` is optional; you can also use `pip` directly.

### Step 3: Install `moves`

```powershell
uv tool install moves-cli
```

Or with pip:
```powershell
pip install moves-cli
```

### Step 4: Verify Installation

```powershell
moves --version
```

You should see something like: `moves-cli version 0.3.2`

## Initial Setup

### Understand the Data Directory

`moves` stores all speaker data in: `C:\Users\<YourUsername>\.moves\`

```
~/.moves/
├── settings.toml              # Your LLM configuration
└── speakers/
    └── <speaker-id>/
        ├── speaker.yaml       # Speaker metadata
        └── sections.md        # Speech content for slides
```

Check this directory:
```powershell
dir $env:USERPROFILE\.moves
```

## Creating Your First Speaker

### Gather Your Materials

You'll need:
1. **Presentation file** – Your slides in PDF, DOCX, PPTX, or TXT format (e.g., `my_talk.pdf`, `my_talk.pptx`)
2. **Transcript file** – Text file with what you'll say (e.g., `my_talk.txt`)

**Supported presentation formats:** All formats are **100% free** with no commercial licenses required!
- **PDF** - Via PyMuPDF4LLM (optimized for LLM processing)
- **DOCX** - Via python-docx (Microsoft Word documents)
- **PPTX** - Via python-pptx (PowerPoint presentations)
- **TXT** - Native text file support

The transcript should be organized roughly by slide, like:

```
Slide 1: Hello everyone, thanks for coming today. I'm excited to share this project.

Slide 2: This is the overview. We have three main topics to cover...

Slide 3: First topic, diving deeper now...
```

### Create a Speaker Profile

Run:
```powershell
moves speaker add MyTalk C:\path\to\my_talk.pdf C:\path\to\my_talk.txt
```

Replace paths with your actual files. You'll see:

```
Speaker MyTalk (a1b2c) has been successfully added.

Data directory:
  C:\Users\<YourUsername>\.moves\speakers\a1b2c

Presentation source:
  C:\path\to\my_talk.pdf

Transcript source:
  C:\path\to\my_talk.txt
```

**Congratulations!** You've created your first speaker profile.

### Using Google Drive URLs (Optional)

If your files are on Google Drive:

```powershell
moves speaker add MyTalk `
  "https://drive.google.com/file/d/1ABC2DEF3GHI/view?usp=sharing" `
  "https://drive.google.com/file/d/1JKL2MNO3PQR/view?usp=sharing"
```

The tool will download them automatically and authenticate if needed.

## Preparing for Presentation

### Option A: Automatic Preparation (Uses LLM)

This is the easiest method. An LLM analyzes your transcript and generates speech content for each slide.

#### 1. Configure Your LLM

First, you need to set up an LLM. Here are popular free options:

**Using Google Gemini (Recommended for Free):**
1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Create a new API key (free tier available)
3. In `moves`, run:
   ```powershell
   moves settings set model gemini/gemini-2.5-flash-lite
   moves settings set format chat
   # Optional endpoint override:
   # moves settings set base_url https://your-openai-compatible-endpoint/v1
   moves settings set key
   ```
4. Paste your API key when prompted (text will be hidden)

**Using OpenAI:**
1. Create account at [OpenAI](https://platform.openai.com/)
2. Get API key from account settings
3. In `moves`, run:
   ```powershell
   moves settings set model gpt-4o-mini
   moves settings set format chat
   # Optional endpoint override:
   # moves settings set base_url https://your-openai-compatible-endpoint/v1
   moves settings set key
   ```

**Using other providers:** See [Configuration Guide](CONFIGURATION.md) for more options.

#### 2. Run Preparation

```powershell
moves speaker prepare MyTalk
```

This will:
- Analyze your PDF slides
- Process your transcript
- Use LLM to generate speech content for each slide
- Create `sections.md` file

Progress bar shows processing time. Takes 30-60 seconds typically.

### Option B: Manual Preparation (No LLM)

If you don't want to use an LLM, or prefer full control:

```powershell
moves speaker prepare MyTalk --manual
```

This creates an empty template. You then manually edit `sections.md`:

```powershell
# Open the sections file in your editor
notepad $env:USERPROFILE\.moves\speakers\a1b2c\sections.md
```

The file looks like:

```markdown
# 1. Slide
Content for slide 1

# 2. Slide
Content for slide 2

# 3. Slide
Content for slide 3
```

Add your speech notes for each slide:

```markdown
# 1. Slide
Hello everyone, thanks for coming. I'm excited to share this.

# 2. Slide
This is the overview. Three main topics today.

# 3. Slide
First, let me dive deeper into the architecture...
```

Save and you're ready!

## Giving a Presentation

### Start the Presentation

```powershell
moves present MyTalk
```

You'll see a dashboard showing:
- Current slide / total slides
- Recognized speech
- Similarity scores
- System status

### During Your Talk

**Microphone listening**: Speak naturally about each slide's content. When your speech matches the section in `sections.md`, the slide advances automatically.

**Keyboard shortcuts** (in case you need to help):
- `←` – Go to previous slide
- `→` – Go to next slide
- `M` – Pause/Resume listening (stop for questions, resume when ready)
- `Q` – Exit presentation

**Tips for best results:**
1. **Speak clearly** – Articulate words distinctly
2. **Match your script** – Use similar phrasing to what's in `sections.md`
3. **Steady pace** – Normal conversational speed works best
4. **Quiet environment** – Less background noise = better recognition
5. **Test first** – Do a dry run before the real presentation

### Exit Presentation

Press `Ctrl+C` to stop. You'll see:

```
Presentation ended.
```

## Managing Speakers

### List All Speakers

```powershell
moves speaker list
```

Shows:
```
There are 2 registered speaker(s).

NAME         ID       STATUS      LAST PROCESSED
MyTalk       a1b2c    Ready       2 hours ago
OtherTalk    d1e2f    Not Ready   Never
```

### Show Speaker Details

```powershell
moves speaker show MyTalk
```

Shows all metadata, paths, and status.

### Update Speaker Files

If you fix your PDF or update your transcript:

```powershell
moves speaker edit MyTalk `
  --presentation C:\new\my_talk.pdf `
  --transcript C:\new\my_talk.txt
```

Then re-prepare:

```powershell
moves speaker prepare MyTalk
```

### Delete a Speaker

```powershell
moves speaker delete MyTalk
```

Or delete all:

```powershell
moves speaker delete --all
```

You'll be asked to confirm. All data will be removed.

## Troubleshooting

### "No speakers found"

**Problem**: `moves speaker list` shows no speakers.

**Solution**:
1. Check if any exist: `dir $env:USERPROFILE\.moves\speakers`
2. If directory is empty, add a speaker: `moves speaker add ...`
3. If directory exists but not showing, check permissions on `~/.moves/`

### "Speaker not ready"

**Problem**: `moves present MyTalk` says speaker hasn't been prepared.

**Solution**:
```powershell
moves speaker prepare MyTalk
```

If using LLM, check your LLM is configured:
```powershell
moves settings list
```

### Microphone Not Working

**Problem**: During presentation, no speech is being recognized.

**Solutions**:
1. **Test Windows audio**: Settings → Sound → Volume mixer
2. **Check if microphone is muted**: Click volume icon, unmute microphone
3. **Test microphone**: Run `moves present MyTalk`, try speaking
4. **Try a different microphone** if available

### Speech Recognition Not Working

**Problem**: You're speaking but nothing is recognized.

**Causes & Solutions**:
- **Content mismatch** – Your sections.md might not match what you're actually saying
  - Edit sections.md to match your real script
  - Re-prepare with better transcript
- **Accent/pronunciation** – STT might struggle with your accent
  - Speak more clearly and deliberately
  - Use "Pause" (M key) between sections
- **Background noise** – Too much noise confuses the model
  - Find a quieter room
  - Close notifications, silence phone

### "LLM Configuration Not Found"

**Problem**: Can't prepare speaker, says model or API key not configured.

**Solution**:
```powershell
moves settings set model gemini/gemini-2.5-flash-lite
moves settings set format chat
moves settings set key
# (paste your API key when prompted)
```

Or use manual mode (no LLM):
```powershell
moves speaker prepare MyTalk --manual
```

### Section Files Changed Warning

**Problem**: Preparing again warns that "sections.md has been modified".

**Solution**:
This is normal if you edited sections.md manually. Choose:
- **Yes (y)** – Continue, keep your edits
- **Save (s)** – Update the hash so it doesn't warn again
- **No (n)** – Cancel and don't update

### Models Taking Too Long to Download

**Problem**: First run is very slow.

**Reason**: ONNX models (~400-500MB) are downloading.

**Solution**: 
- Wait for completion (5-10 minutes depending on internet)
- Check: `dir $env:USERPROFILE\.moves\ml_models` to see download progress

## Frequently Asked Questions

### Q: Is my voice data sent to the cloud?

**A:** No. Speech recognition happens offline using local ONNX models. Your voice never leaves your machine. The only cloud call is to the LLM (if you use automatic preparation), which is optional—you can use `--manual` mode instead.

### Q: Can I use my own presentation slides (not PDF)?

**A:** Yes! moves-cli supports multiple formats with **100% free, open-source libraries**:
- **PDF** - PyMuPDF4LLM (optimized for LLM processing)
- **DOCX** - python-docx (Word documents)
- **PPTX** - python-pptx (PowerPoint presentations)
- **TXT** - Native text support

No commercial licenses or PyMuPDF Pro required! Just provide the file path directly:
```powershell
moves speaker add MyTalk C:\talks\my_talk.pptx C:\talks\my_talk.txt
```

### Q: What if my transcript doesn't perfectly match my slides?

**A:** It's OK! The tool is designed to be flexible:
- Add approximate content for each slide in `sections.md`
- During presentation, it matches your speech approximately
- If not matching, use keyboard shortcuts (← →) to navigate manually

### Q: Can I have multiple presentations ready?

**A:** Yes! Create multiple speakers:

```powershell
moves speaker add Talk1 C:\talks\talk1.pdf C:\talks\talk1.txt
moves speaker add Talk2 C:\talks\talk2.pdf C:\talks\talk2.txt

moves present Talk1     # First presentation
moves present Talk2     # Different presentation
```

### Q: How accurate is the slide detection?

**A:** Accuracy depends on:
- **Content match** – How well your `sections.md` matches what you say
- **Speech clarity** – Clear speech recognizes better
- **Audio quality** – Quiet environment works best

Typical accuracy: 85-95% automatic advances with manual backups via keyboard.

### Q: Can I use a different LLM provider?

**A:** Yes! Any provider supported by LiteLLM works:

```powershell
moves settings set model claude-3-5-sonnet
# or
moves settings set model gpt-4o
# or others...
```

See [Configuration Guide](CONFIGURATION.md) for full list.

### Q: What if I mess up `sections.md`?

**A:** You can re-prepare to regenerate it:

```powershell
moves speaker prepare MyTalk
```

This will overwrite your manual edits. If you had custom content, keep a backup.

### Q: Can I use this without an internet connection?

**A:** Partially:
- **Presentation phase** – Yes, fully offline after models are downloaded
- **Preparation phase** – Requires internet for LLM, unless using `--manual` mode

### Q: How much disk space does this need?

**A:** 
- Models: ~400-500MB (one-time download)
- Speaker data: ~1-10MB per speaker (depending on presentation size)
- Total: ~500MB + speaker data

### Q: Can I use slides from presentation tools directly?

**A:** Yes! moves-cli supports multiple formats:
- **PDF** - Direct support (no export needed)
- **PPTX** - Direct support with PyMuPDF Pro
- **DOCX** - Direct support with PyMuPDF Pro

If you prefer PDF or don't have PyMuPDF Pro:
- **PowerPoint**: File → Export as PDF or use .pptx directly
- **Google Slides**: File → Download → PDF (or PPTX)
- **LibreOffice**: File → Export as PDF

Then use the file with `moves`.

### Q: What happens if I interrupt preparation?

**A:** Interrupting (Ctrl+C) will stop the process. You can restart:

```powershell
moves speaker prepare MyTalk
```

It will re-process from the beginning.

---

**Need more help?** Check the [Architecture Guide](ARCHITECTURE.md) for technical details or see the [CLI Reference](CLI_REFERENCE.md) for all available commands.
