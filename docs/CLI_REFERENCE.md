# CLI Reference

Complete documentation of all `moves` commands and options.

## Command Structure

```
moves [OPTIONS] COMMAND [ARGS]

Global Options:
  --version                Show version and exit
  --help                   Show help and exit
```

## Main Commands

### `moves --version`

Display the installed version of `moves-cli`.

```powershell
moves --version
```

Output:
```
moves-cli version 0.3.2
```

---

## Speaker Management Commands

All speaker commands are under the `speaker` subcommand.

### `moves speaker add`

Create a new speaker profile.

**Syntax:**
```powershell
moves speaker add NAME SOURCE_PRESENTATION SOURCE_TRANSCRIPT
```

**Arguments:**
- `NAME` (required) – Speaker/presentation name
- `SOURCE_PRESENTATION` (required) – Path to presentation file or Google Drive URL
  - **Supported formats:** PDF, DOCX, PPTX, TXT (all 100% free, no commercial licenses)
- `SOURCE_TRANSCRIPT` (required) – Path to transcript or Google Drive URL

**Example:**
```powershell
# Local files
moves speaker add MyTalk C:\presentations\talk.pdf C:\presentations\transcript.txt

# Google Drive URLs
moves speaker add MyTalk `
  "https://drive.google.com/file/d/ABC123/view?usp=sharing" `
  "https://drive.google.com/file/d/DEF456/view?usp=sharing"

# Mixed
moves speaker add MyTalk `
  "C:\presentations\talk.pdf" `
  "https://drive.google.com/file/d/DEF456/view?usp=sharing"
```

**Output:**
```
Speaker MyTalk (a1b2c) has been successfully added.

Data directory:
  C:\Users\<YourUsername>\.moves\speakers\a1b2c

Presentation source:
  C:\presentations\talk.pdf

Transcript source:
  C:\presentations\transcript.txt
```

---

### `moves speaker edit`

Update a speaker's source files.

**Syntax:**
```powershell
moves speaker edit SPEAKER [OPTIONS]
```

**Arguments:**
- `SPEAKER` (required) – Speaker name or ID

**Options:**
- `--presentation PATH, -p PATH` – New presentation file path or URL (PDF, DOCX*, PPTX*, TXT, etc.)
- `--transcript PATH, -t PATH` – New transcript file path or URL

**Requirements:**
- At least one option must be provided

**Examples:**
```powershell
# Update only presentation
moves speaker edit MyTalk --presentation C:\new_talk.pdf

# Update only transcript
moves speaker edit MyTalk --transcript C:\new_transcript.txt

# Update both
moves speaker edit MyTalk -p C:\new.pdf -t C:\new.txt

# Using Google Drive
moves speaker edit MyTalk --presentation "https://drive.google.com/file/d/ABC123/view"
```

**Output:**
```
Speaker MyTalk (a1b2c) has been successfully edited.

New presentation source:
  C:\new_talk.pdf

New transcript source:
  C:\new_transcript.txt
```

---

### `moves speaker list`

Display all registered speakers and their status.

**Syntax:**
```powershell
moves speaker list
```

**Output:**
```
There are 2 registered speaker(s).

NAME       ID     STATUS      LAST PROCESSED
MyTalk     a1b2c  Ready       2 hours ago
OtherTalk  d1e2f  Not Ready   Never

Data directory: C:\Users\<YourUsername>\.moves\speakers
```

**Status meanings:**
- `Ready` – Prepared and ready to present
- `Not Ready` – Added but not yet prepared

---

### `moves speaker show`

Display detailed information about a specific speaker.

**Syntax:**
```powershell
moves speaker show SPEAKER
```

**Arguments:**
- `SPEAKER` (required) – Speaker name or ID

**Example:**
```powershell
moves speaker show MyTalk
```

**Output:**
```
Showing details for MyTalk (a1b2c)

Name:
  MyTalk

ID:
  a1b2c

Status:
  Ready

Last Processed:
  2 hours ago

Data directory:
  C:\Users\<YourUsername>\.moves\speakers\a1b2c

Sections file:
  C:\Users\<YourUsername>\.moves\speakers\a1b2c\sections.md

Presentation source:
  C:\presentations\talk.pdf

Transcript source:
  C:\presentations\transcript.txt
```

---

### `moves speaker prepare`

Prepare speaker(s) for presentation. Generates `sections.md` with speech content.

**Syntax:**
```powershell
moves speaker prepare [SPEAKERS] [OPTIONS]
```

**Arguments:**
- `SPEAKERS` (optional) – One or more speaker names or IDs

**Options:**
- `--all, -a` – Prepare all registered speakers
- `--manual, -m` – Generate empty template (no LLM)
- `--yes, -y` – Skip confirmation prompts

**Requirements:**
- Either provide speaker names OR use `--all`
- If not using `--manual`, LLM settings must be configured

**Examples:**
```powershell
# Prepare single speaker (with LLM)
moves speaker prepare MyTalk

# Prepare multiple speakers
moves speaker prepare MyTalk OtherTalk

# Prepare all speakers
moves speaker prepare --all

# Manual mode (empty template)
moves speaker prepare MyTalk --manual

# Auto mode, skip confirmation
moves speaker prepare MyTalk --yes

# Multiple with flags
moves speaker prepare MyTalk OtherTalk --yes
```

**Output (Single speaker, auto mode):**
```
Speaker MyTalk (a1b2c) prepared.

Sections created:
  15

Processing time:
  45.3s

Sections file:
  C:\Users\<YourUsername>\.moves\speakers\a1b2c\sections.md

Data directory:
  C:\Users\<YourUsername>\.moves\speakers\a1b2c
```

**Output (Single speaker, manual mode):**
```
Speaker MyTalk (a1b2c) prepared.

Sections created:
  15

Sections file:
  C:\Users\<YourUsername>\.moves\speakers\a1b2c\sections.md

Data directory:
  C:\Users\<YourUsername>\.moves\speakers\a1b2c

Next step:
  Edit sections.md to add speech content for each slide
```

**Output (Multiple speakers):**
```
2 speakers prepared.

MyTalk (a1b2c):
  15 sections (45.3s)

OtherTalk (d1e2f):
  12 sections (38.1s)

Total preparation time: 83.4 seconds.
```

---

### `moves speaker delete`

Delete one or more speakers and their data.

**Syntax:**
```powershell
moves speaker delete [SPEAKERS] [OPTIONS]
```

**Arguments:**
- `SPEAKERS` (optional) – One or more speaker names or IDs

**Options:**
- `--all, -a` – Delete all registered speakers
- `--yes, -y` – Skip confirmation prompt

**Requirements:**
- Either provide speaker names OR use `--all`

**Examples:**
```powershell
# Delete single speaker (with confirmation)
moves speaker delete MyTalk

# Delete multiple speakers
moves speaker delete MyTalk OtherTalk

# Delete all (with confirmation)
moves speaker delete --all

# Delete without confirmation
moves speaker delete MyTalk --yes
```

**Output (With confirmation):**
```
Are you sure you want to delete the following 1 speaker(s)?

MyTalk: a1b2c

Proceed? [Y/n]: y
Yes

Speaker MyTalk (a1b2c) deleted.

Data directory removed:
  C:\Users\<YourUsername>\.moves\speakers\a1b2c
```

---

## Presentation Control

### `moves present`

Start live voice-controlled presentation navigation.

**Syntax:**
```powershell
moves present SPEAKER
```

**Arguments:**
- `SPEAKER` (required) – Speaker name or ID

**Requirements:**
- Speaker must be prepared (sections.md exists)
- Microphone must be connected
- Source files (PDF, transcript) must still exist

**Example:**
```powershell
moves present MyTalk
```

**Output:**
```
Presentation started for MyTalk (a1b2c).

[M] Pause/Resume | [←/→] Previous/Next | [Q] Exit

[Interactive dashboard shows during presentation]

Presentation ended.
```

**Keyboard Controls During Presentation:**
| Key | Action |
|-----|--------|
| `←` (Left Arrow) | Go to previous slide |
| `→` (Right Arrow) | Go to next slide |
| `M` | Toggle pause/resume (freeze microphone) |
| `Q` | Exit presentation |

**Dashboard Display:**
The Rich UI shows:
- Current slide number
- Total slides
- Recognized speech text
- Similarity scores (semantic + phonetic)
- System state (ACTIVE / PAUSED / LOCKED)
- Last detected chunks

---

## Settings Management

All settings commands are under the `settings` subcommand.

### `moves settings list`

Display current system configuration.

**Syntax:**
```powershell
moves settings list [OPTIONS]
```

**Options:**
- `--show, -s` – Reveal full API key (normally hidden)

**Examples:**
```powershell
# Show masked key
moves settings list

# Show full key
moves settings list --show
```

**Output:**
```
moves CLI Configuration

Configuration file:
  C:\Users\<YourUsername>\.moves\settings.toml

model (LLM Model):
  gemini/gemini-2.5-flash-lite

format (LLM API Format):
  chat

base_url (LLM Base URL):
  Not configured

key (API Key):
  gemi****b8fk

Note:
  API keys are stored in Windows Credential Manager (keyring)
```

---

### `moves settings set`

Configure a setting (model, format, base_url, or API key).

**Syntax:**
```powershell
moves settings set SETTING [VALUE]
```

**Arguments:**
- `SETTING` (required) – Setting name: `model`, `format`, `base_url`, or `key`
- `VALUE` (optional) – Setting value (required for `model`, `format`, and `base_url`)

**Examples:**
```powershell
# Set LLM model
moves settings set model gemini/gemini-2.5-flash-lite

# Set LLM API format
moves settings set format chat
moves settings set format responses
moves settings set format auto

# Set optional LLM base URL
moves settings set base_url https://your-openai-compatible-endpoint/v1

# Set API key (interactive, hidden input)
moves settings set key
# Then paste your key when prompted

# Other models
moves settings set model gpt-4o-mini
moves settings set model claude-3-5-sonnet
```

**Output (Model):**
```
Setting 'model' updated.

New value:
  gemini/gemini-2.5-flash-lite

Storage:
  C:\Users\<YourUsername>\.moves\settings.toml
```

**Output (API Key):**
```
Note: Your input will not be shown on screen.
Enter API key: [hidden input]

Setting 'key' updated.

New value:
  gemi****b8fk

Storage:
  Windows Credential Manager
```

---

### `moves settings unset`

Reset a setting to its default value.

**Syntax:**
```powershell
moves settings unset SETTING
```

**Arguments:**
- `SETTING` (required) – Setting name: `model`, `format`, `base_url`, or `key`

**Examples:**
```powershell
# Reset model to default
moves settings unset model

# Reset format to default
moves settings unset format

# Reset base URL to default (empty)
moves settings unset base_url

# Reset API key
moves settings unset key
```

**Output:**
```
Setting 'model' reset to default.

New Value:
  gemini/gemini-2.5-flash-lite

Removed from:
  C:\Users\<YourUsername>\.moves\settings.toml
```

---

## Speaker Resolution

Many commands take a `SPEAKER` argument. This can be:

1. **Speaker name** – Exact name from `moves speaker list`
   ```powershell
   moves speaker show MyTalk
   ```

2. **Speaker ID** – Short ID in parentheses from listings
   ```powershell
   moves speaker show a1b2c
   ```

If the speaker isn't found, you'll get an error with suggestions of available speakers.

---

## Common Patterns

### Prepare All Speakers

```powershell
moves speaker prepare --all --yes
```

### Delete Old Speaker

```powershell
moves speaker delete OldPresentation --yes
```

### Quick Setup

```powershell
# 1. Add speaker
moves speaker add MyTalk C:\talk.pdf C:\transcript.txt

# 2. Configure LLM (one time)
moves settings set model gemini/gemini-2.5-flash-lite
moves settings set key

# 3. Prepare
moves speaker prepare MyTalk

# 4. Present
moves present MyTalk
```

### Switch LLM Provider

```powershell
moves settings set model gpt-4o-mini
moves settings set key
```

Then re-prepare your speakers to use the new model:

```powershell
moves speaker prepare MyTalk --yes
```

---

## Error Messages

### "Speaker not found: 'MyTalk'"

The named speaker doesn't exist. List available speakers:

```powershell
moves speaker list
```

### "LLM model not configured"

You tried to prepare without setting an LLM model:

```powershell
moves settings set model gemini/gemini-2.5-flash-lite
moves speaker prepare MyTalk
```

Or use `--manual` mode:

```powershell
moves speaker prepare MyTalk --manual
```

### "Speaker has not been prepared yet"

You tried to present before running prepare:

```powershell
moves speaker prepare MyTalk
moves present MyTalk
```

### "Missing source files"

Your PDF or transcript files were moved or deleted. Update:

```powershell
moves speaker edit MyTalk --presentation C:\new_talk.pdf
```

---

## Tips & Tricks

1. **Using Tab to expand paths** – PowerShell autocompletes file paths with Tab

2. **Using `$env:USERPROFILE`** – Refer to home directory:
   ```powershell
   explorer $env:USERPROFILE\.moves
   ```

3. **Listing speakers in code** – Parse the table output:
   ```powershell
   moves speaker list | findstr "Ready"
   ```

4. **Batch operations** – Multiple speaker names:
   ```powershell
   moves speaker delete Speaker1 Speaker2 Speaker3 --yes
   ```

---

For more details, see the [Getting Started Guide](GETTING_STARTED.md) or [Configuration Guide](CONFIGURATION.md).
