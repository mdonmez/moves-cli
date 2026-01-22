# CLI Reference

Complete documentation for all `moves` commands.

## Command Structure

```
moves [OPTIONS] COMMAND [ARGS]

Global Options:
  --version    Show version and exit
  --help       Show help and exit
```

---

## Main Commands

### `moves --version`

Display the installed version.

```bash
moves --version
```

Output:
```
moves-cli version 0.3.3
```

### `moves --help`

Show all available commands.

```bash
moves --help
```

---

## Speaker Management

All speaker commands are under the `speaker` subcommand.

### `moves speaker add`

Create a new speaker profile.

**Syntax:**
```bash
moves speaker add NAME SOURCE_PRESENTATION SOURCE_TRANSCRIPT
```

**Arguments:**
| Argument | Required | Description |
|----------|----------|-------------|
| `NAME` | Yes | Speaker/presentation name |
| `SOURCE_PRESENTATION` | Yes | Path to presentation file (PDF, DOCX, PPTX, TXT) or Google Drive URL |
| `SOURCE_TRANSCRIPT` | Yes | Path to transcript file or Google Drive URL |

**Supported Formats:**
- PDF – PyMuPDF4LLM (LLM-optimized)
- DOCX – python-docx
- PPTX – python-pptx
- TXT – Native

**Examples:**
```bash
# Local files
moves speaker add MyTalk /path/to/presentation.pdf /path/to/transcript.txt

# PowerPoint
moves speaker add MyTalk /path/to/slides.pptx /path/to/notes.txt

# Google Drive URLs
moves speaker add MyTalk \
  "https://drive.google.com/file/d/ABC123/view?usp=sharing" \
  "https://drive.google.com/file/d/DEF456/view?usp=sharing"

# Mixed (local + Google Drive)
moves speaker add MyTalk \
  /local/presentation.pdf \
  "https://drive.google.com/file/d/DEF456/view?usp=sharing"
```

**Output:**
```
Speaker MyTalk (a1b2c) has been successfully added.

  Data directory: ~/.moves/speakers/a1b2c
  Presentation source: /path/to/presentation.pdf
  Transcript source: /path/to/transcript.txt
```

---

### `moves speaker edit`

Update a speaker's source files.

**Syntax:**
```bash
moves speaker edit SPEAKER [OPTIONS]
```

**Arguments:**
| Argument | Required | Description |
|----------|----------|-------------|
| `SPEAKER` | Yes | Speaker name or ID |

**Options:**
| Option | Description |
|--------|-------------|
| `--presentation, -p PATH` | New presentation file path or URL |
| `--transcript, -t PATH` | New transcript file path or URL |

At least one option must be provided.

**Examples:**
```bash
# Update presentation only
moves speaker edit MyTalk --presentation /new/path/presentation.pdf

# Update transcript only
moves speaker edit MyTalk --transcript /new/transcript.txt

# Update both
moves speaker edit MyTalk -p /new/slides.pdf -t /new/notes.txt

# Using Google Drive
moves speaker edit MyTalk --presentation "https://drive.google.com/file/d/XYZ789/view"
```

**Output:**
```
Speaker MyTalk (a1b2c) has been successfully edited.

  Data directory: ~/.moves/speakers/a1b2c
  New presentation source: /new/path/presentation.pdf
```

---

### `moves speaker list`

Display all registered speakers.

**Syntax:**
```bash
moves speaker list
```

**Output:**
```
There are 2 registered speaker(s).

NAME         ID      STATUS      LAST PROCESSED
MyTalk       a1b2c   Ready       2024-01-15 14:30
OtherTalk    d1e2f   Not Ready   N/A

Data directory: ~/.moves/speakers
```

**Status Values:**
| Status | Meaning |
|--------|---------|
| `Ready` | Prepared and has sections.md |
| `Not Ready` | Added but not yet prepared |

---

### `moves speaker show`

Display detailed information about a speaker.

**Syntax:**
```bash
moves speaker show SPEAKER
```

**Arguments:**
| Argument | Required | Description |
|----------|----------|-------------|
| `SPEAKER` | Yes | Speaker name or ID |

**Example:**
```bash
moves speaker show MyTalk
```

**Output:**
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

---

### `moves speaker prepare`

Prepare speaker(s) for presentation by generating sections.md.

**Syntax:**
```bash
moves speaker prepare [SPEAKERS...] [OPTIONS]
```

**Arguments:**
| Argument | Required | Description |
|----------|----------|-------------|
| `SPEAKERS` | No* | One or more speaker names or IDs |

*Either provide speakers or use `--all`.

**Options:**
| Option | Description |
|--------|-------------|
| `--all, -a` | Prepare all registered speakers |
| `--manual, -m` | Generate empty template (no LLM required) |
| `--yes, -y` | Skip confirmation prompts |

**Auto Mode (Default):**
Requires LLM configuration. Analyzes transcript and generates speech content.

```bash
# Single speaker
moves speaker prepare MyTalk

# Multiple speakers
moves speaker prepare MyTalk OtherTalk

# All speakers
moves speaker prepare --all

# Skip confirmation
moves speaker prepare MyTalk --yes
```

**Manual Mode:**
Creates empty template for you to fill in. No LLM needed.

```bash
moves speaker prepare MyTalk --manual
```

**Auto Mode Output:**
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
  Data directory: ~/.moves/speakers/a1b2c
```

**Manual Mode Output:**
```
Speaker MyTalk (a1b2c) prepared.

  Sections created: 15
  Sections file: ~/.moves/speakers/a1b2c/sections.md
  Data directory: ~/.moves/speakers/a1b2c
  Next step: Edit sections.md to add speech content for each slide
```

---

### `moves speaker delete`

Delete one or more speakers and their data.

**Syntax:**
```bash
moves speaker delete [SPEAKERS...] [OPTIONS]
```

**Arguments:**
| Argument | Required | Description |
|----------|----------|-------------|
| `SPEAKERS` | No* | One or more speaker names or IDs |

*Either provide speakers or use `--all`.

**Options:**
| Option | Description |
|--------|-------------|
| `--all, -a` | Delete all registered speakers |
| `--yes, -y` | Skip confirmation prompt |

**Examples:**
```bash
# Single speaker (with confirmation)
moves speaker delete MyTalk

# Multiple speakers
moves speaker delete MyTalk OtherTalk

# Without confirmation
moves speaker delete MyTalk --yes

# Delete all
moves speaker delete --all
```

**Output:**
```
Are you sure you want to delete the following 1 speaker(s)?

  a1b2c: MyTalk

Proceed? [Y/n]: y
Yes

Speaker(s) deleted.
```

---

## Presentation Control

### `moves present`

Start live voice-controlled presentation.

**Syntax:**
```bash
moves present SPEAKER
```

**Arguments:**
| Argument | Required | Description |
|----------|----------|-------------|
| `SPEAKER` | Yes | Speaker name or ID |

**Requirements:**
- Speaker must be prepared (sections.md exists)
- Microphone connected
- Source files must exist

**Example:**
```bash
moves present MyTalk
```

**Output:**
```
Presentation started for MyTalk (a1b2c).
[←/→] Previous/Next | [Ins] Pause/Resume | [Ctrl+C] Exit

[Interactive dashboard appears]

Presentation ended.
```

**Keyboard Controls:**
| Key | Action |
|-----|--------|
| `←` | Previous slide |
| `→` | Next slide |
| `M` | Toggle pause/resume microphone |
| `Q` | Quit presentation |
| `Ctrl+C` | Force exit |

**Dashboard Display:**
The Rich terminal UI shows:
- **State**: ACTIVE, PAUSED, or LOCKED
- **Slide**: Current / Total (e.g., "5/15")
- **Similarity**: Match percentage
- **VAD**: Voice activity indicator (● active, ○ inactive)
- **Speech**: Recognized words
- **Match**: Current section content

**States:**
| State | Description |
|-------|-------------|
| `ACTIVE` | Listening and auto-navigating |
| `PAUSED` | Microphone muted, keyboard still works |
| `LOCKED` | Manual navigation detected, auto-advance disabled |

**Warning Prompts:**
- **Source files changed**: Detects if presentation or transcript modified since last preparation
- **Sections.md modified**: Detects manual edits to sections file
- **Empty sections**: Warns if some sections have no content

---

## Settings Management

All settings commands are under the `settings` subcommand.

### `moves settings list`

Display current configuration.

**Syntax:**
```bash
moves settings list [OPTIONS]
```

**Options:**
| Option | Description |
|--------|-------------|
| `--show, -s` | Reveal full API key (normally masked) |

**Examples:**
```bash
# Show with masked key
moves settings list

# Show full key
moves settings list --show
```

**Output:**
```
moves CLI Configuration

  Configuration file: ~/.moves/settings.toml
  model (LLM Model): gemini/gemini-2.5-flash-lite
  key (API Key): gemi****b8fk
  Note: API keys are stored in Windows Credential Manager (keyring)
```

---

### `moves settings set`

Configure a setting.

**Syntax:**
```bash
moves settings set SETTING [VALUE]
```

**Arguments:**
| Argument | Required | Description |
|----------|----------|-------------|
| `SETTING` | Yes | Setting name: `model` or `key` |
| `VALUE` | Depends | Required for `model`, not allowed for `key` |

**Setting: `model`**

Sets the LLM model for section generation.

```bash
# Google Gemini (free)
moves settings set model gemini/gemini-2.5-flash-lite

# OpenAI
moves settings set model gpt-4o-mini

# Anthropic
moves settings set model claude-3-5-sonnet

# Groq (free)
moves settings set model groq/mixtral-8x7b-32768
```

**Output:**
```
Setting 'model' updated.

  New value: gemini/gemini-2.5-flash-lite
  Storage: ~/.moves/settings.toml
```

**Setting: `key`**

Sets the API key (interactive, hidden input).

```bash
moves settings set key
```

**Output:**
```
Note: Your input will not be shown on screen.
Enter API key: [hidden input]

Setting 'key' updated.

  New value: gemi****b8fk
  Storage: Windows Credential Manager
```

---

### `moves settings unset`

Reset a setting to its default value.

**Syntax:**
```bash
moves settings unset SETTING
```

**Arguments:**
| Argument | Required | Description |
|----------|----------|-------------|
| `SETTING` | Yes | Setting name: `model` or `key` |

**Examples:**
```bash
# Reset model to default
moves settings unset model

# Remove API key
moves settings unset key
```

**Output:**
```
Setting 'model' reset to default.

  New Value: gemini/gemini-2.5-flash-lite
  Removed from: ~/.moves/settings.toml
```

---

## Speaker Resolution

Commands that take a `SPEAKER` argument accept:

1. **Speaker name** – Exact name from `moves speaker list`
2. **Speaker ID** – Short ID in parentheses (e.g., `a1b2c`)

```bash
# By name
moves speaker show MyTalk
moves present MyTalk

# By ID
moves speaker show a1b2c
moves present a1b2c
```

**Ambiguity:**
If multiple speakers have the same name, use the ID:
```
Multiple speakers found matching 'MyTalk'. Be more specific:
    MyTalk (a1b2c)
    MyTalk (d3e4f)
```

---

## Common Patterns

### Quick Setup
```bash
# 1. Add speaker
moves speaker add MyTalk presentation.pdf transcript.txt

# 2. Configure LLM (one-time)
moves settings set model gemini/gemini-2.5-flash-lite
moves settings set key

# 3. Prepare
moves speaker prepare MyTalk

# 4. Present
moves present MyTalk
```

### Manual Mode (No LLM)
```bash
moves speaker add MyTalk presentation.pdf transcript.txt
moves speaker prepare MyTalk --manual
# Edit sections.md manually
moves present MyTalk
```

### Batch Operations
```bash
# Prepare all speakers
moves speaker prepare --all --yes

# Delete multiple speakers
moves speaker delete Talk1 Talk2 Talk3 --yes
```

### Re-prepare After Changes
```bash
moves speaker edit MyTalk --presentation /updated/slides.pdf
moves speaker prepare MyTalk
```

---

## Error Messages

### "No speaker found matching 'X'"
Speaker doesn't exist. Check available speakers:
```bash
moves speaker list
```

### "LLM model not configured"
Set a model before preparing:
```bash
moves settings set model gemini/gemini-2.5-flash-lite
```
Or use manual mode:
```bash
moves speaker prepare MyTalk --manual
```

### "LLM API key not configured"
Set an API key:
```bash
moves settings set key
```
Or use manual mode.

### "Speaker has not been prepared yet"
Run preparation first:
```bash
moves speaker prepare MyTalk
```

### "Missing source files"
Source files were moved or deleted. Update paths:
```bash
moves speaker edit MyTalk --presentation /new/path/slides.pdf
```

### "At least one update parameter must be provided"
The `edit` command requires at least one option:
```bash
moves speaker edit MyTalk --presentation /path/to/new.pdf
```

---

## Tips

1. **Tab completion** – Your shell may autocomplete file paths
2. **Home directory** – Use `~/.moves` to reference the data directory
3. **Speaker ID** – Use the short ID when names conflict
4. **Quiet mode** – Use `--yes` to skip prompts in scripts
5. **Check settings** – Run `moves settings list` to verify configuration

---

For detailed guides, see:
- [Getting Started](GETTING_STARTED.md) – Step-by-step walkthrough
- [Configuration](CONFIGURATION.md) – LLM and tuning options
- [Architecture](ARCHITECTURE.md) – How it works internally
