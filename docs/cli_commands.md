# CLI Reference Guide

The `moves` command-line interface provides comprehensive tools for managing voice-controlled presentations. This guide documents all commands, their options, and practical usage examples.

## Quick Start Guide

Get `moves` running in three simple steps:

### 1. Configure Your AI Model

Set up the LLM for processing presentation data.

> **Note:** Browse compatible models at [LiteLLM Supported Models](https://models.litellm.ai/).

```bash
# Configure the model
moves settings set model openai/gpt-4o-mini

# Configure your API key
moves settings set key YOUR_API_KEY
```

### 2. Add and Process a Speaker

Create a speaker profile with presentation and transcript files (both must be PDF format).

```bash
# Add speaker profile
moves speaker add "Speaker Name" ./presentation.pdf ./transcript.pdf

# Process data for AI-powered control
moves speaker process "Speaker Name"
```

### 3. Launch Presentation Control

Start the voice-controlled presentation session.

```bash
moves presentation control "Speaker Name"
```

Open your presentation in fullscreen mode, and `moves` will handle slide transitions based on your speech.

## Command Structure

All `moves` commands follow a consistent hierarchical structure:

```
moves [GLOBAL_OPTIONS] <COMMAND> <ACTION> [ARGUMENTS] [OPTIONS]
```

**Available Commands:**

| Command        | Purpose                                          |
| :------------- | :----------------------------------------------- |
| `speaker`      | Manage speaker profiles, files, and processing   |
| `presentation` | Control live voice-activated presentation flow   |
| `settings`     | Configure LLM model and API key                  |

**Global Options:**

| Option      | Description                           |
| :---------- | :------------------------------------ |
| `--help`    | Display help information for commands |
| `--version` | Show application version              |

## `speaker` Command

Manages speaker profiles, associated files, and AI data processing.

### Available Actions

| Action    | Purpose                                          |
| :-------- | :----------------------------------------------- |
| `add`     | Create a new speaker profile                     |
| `edit`    | Update file paths for an existing speaker        |
| `list`    | Display all registered speakers                  |
| `show`    | View detailed information for a specific speaker |
| `process` | Process speaker data for AI navigation           |
| `delete`  | Remove speaker profiles and their data           |

### `speaker add`

Creates a new speaker profile with associated presentation and transcript files.

**Syntax:**

```bash
moves speaker add <NAME> <SOURCE_PRESENTATION> <SOURCE_TRANSCRIPT>
```

**Arguments:**

| Argument              | Type     | Description                       |
| :-------------------- | :------- | :-------------------------------- |
| `name`                | Required | Speaker's name                    |
| `source_presentation` | Required | Path to presentation PDF file     |
| `source_transcript`   | Required | Path to transcript PDF file       |

**Example:**

```bash
moves speaker add "John Doe" ./presentation.pdf ./transcript.pdf
```

**Output:**
```
Speaker 'John Doe' (john-doe-a1b2c) added.
    ID -> john-doe-a1b2c
    Presentation -> /path/to/presentation.pdf
    Transcript -> /path/to/transcript.pdf
```

### `speaker edit`

Updates presentation or transcript file paths for an existing speaker profile.

**Syntax:**

```bash
moves speaker edit <SPEAKER> [OPTIONS]
```

**Arguments:**

| Argument  | Type     | Description                        |
| :-------- | :------- | :--------------------------------- |
| `speaker` | Required | Speaker name or unique ID          |

**Options:**

| Option                 | Description                      |
| :--------------------- | :------------------------------- |
| `-p`, `--presentation` | New presentation PDF file path   |
| `-t`, `--transcript`   | New transcript PDF file path     |

**Examples:**

```bash
# Update presentation file
moves speaker edit "John Doe" --presentation ./new_presentation.pdf

# Update transcript file
moves speaker edit "John Doe" --transcript ./new_transcript.pdf

# Update both files using short options
moves speaker edit "John Doe" -p ./new_slides.pdf -t ./new_speech.pdf

# Edit by speaker ID
moves speaker edit john-doe-a1b2c --presentation ./updated.pdf
```

### `speaker list`

Displays all registered speaker profiles.

**Syntax:**

```bash
moves speaker list
```

**Example Output:**
```
Registered Speakers:
  1. John Doe (john-doe-a1b2c) - Ready
  2. Jane Smith (jane-smith-x7y8z) - Pending Processing
```

### `speaker show`

Displays detailed information about a specific speaker profile.

**Syntax:**

```bash
moves speaker show <SPEAKER>
```

**Arguments:**

| Argument  | Type     | Description               |
| :-------- | :------- | :------------------------ |
| `speaker` | Required | Speaker name or unique ID |

**Examples:**

```bash
# Show details by name
moves speaker show "John Doe"

# Show details by ID
moves speaker show john-doe-a1b2c
```

**Example Output:**
```
Speaker: John Doe
ID: john-doe-a1b2c
Status: Ready
Presentation: /home/user/slides/presentation.pdf
Transcript: /home/user/docs/transcript.pdf
Sections: 25
```

### `speaker process`

Processes speaker data using the configured LLM to enable AI-powered presentation control. This step uses the LLM to segment the transcript and align it with presentation slides.

**Syntax:**

```bash
moves speaker process [SPEAKERS]... [OPTIONS]
```

**Arguments:**

| Argument   | Type     | Description                                    |
| :--------- | :------- | :--------------------------------------------- |
| `speakers` | Optional | Space-separated list of speaker names or IDs  |

**Options:**

| Option        | Description                  |
| :------------ | :--------------------------- |
| `-a`, `--all` | Process all speaker profiles |

**Examples:**

```bash
# Process a single speaker
moves speaker process "John Doe"

# Process multiple speakers
moves speaker process "John Doe" "Jane Smith"

# Process by speaker ID
moves speaker process john-doe-a1b2c

# Process all registered speakers
moves speaker process --all
```

**Notes:**
- Requires valid LLM configuration (`moves settings set model` and `moves settings set key`)
- Processing time depends on presentation size and LLM response time
- Re-running this command updates the speaker's processed data

### `speaker delete`

Permanently removes speaker profiles and all associated data.

**Syntax:**

```bash
moves speaker delete [SPEAKERS]... [OPTIONS]
```

**Arguments:**

| Argument   | Type     | Description                                   |
| :--------- | :------- | :-------------------------------------------- |
| `speakers` | Optional | Space-separated list of speaker names or IDs |

**Options:**

| Option        | Description                  |
| :------------ | :--------------------------- |
| `-a`, `--all` | Delete all speaker profiles  |

**Examples:**

```bash
# Delete a single speaker
moves speaker delete "John Doe"

# Delete multiple speakers
moves speaker delete "John Doe" "Jane Smith"

# Delete by speaker ID
moves speaker delete john-doe-a1b2c

# Delete all speakers
moves speaker delete --all
```

**Warning:** This operation is irreversible and removes all speaker data including processed sections.

## `presentation` Command

Controls live presentations with voice-activated navigation.

### `presentation control`

Starts a voice-controlled presentation session using processed speaker data.

**Syntax:**

```bash
moves presentation control <SPEAKER>
```

**Arguments:**

| Argument  | Type     | Description               |
| :-------- | :------- | :------------------------ |
| `speaker` | Required | Speaker name or unique ID |

**Example:**

```bash
moves presentation control "John Doe"
```

**Prerequisites:**
- Speaker profile must exist
- Speaker data must be processed (`moves speaker process`)
- Presentation file should be open in fullscreen mode

**Session Controls:**

| Input                | Action                                  |
| :------------------- | :-------------------------------------- |
| **Voice**            | Speak naturally to trigger navigation   |
| **→** (Right Arrow)  | Manually advance to next section        |
| **←** (Left Arrow)   | Manually return to previous section     |
| **Insert**           | Pause/resume automatic voice navigation |
| **Ctrl+C**           | Exit control session                    |

**How It Works:**
1. System loads speech recognition models (initial delay on first run)
2. Begins continuous audio capture from default microphone
3. Transcribes speech in real-time
4. Matches spoken words against processed presentation content
5. Automatically sends keyboard commands to advance slides
6. Maintains synchronization between speech and slide position

## `settings` Command

Configures system-wide LLM model and API key settings.

### Available Actions

| Action  | Purpose                                 |
| :------ | :-------------------------------------- |
| `list`  | Display current configuration values    |
| `set`   | Update a configuration setting          |
| `unset` | Reset a setting to its default value    |

### `settings list`

Displays current LLM model and API key configuration.

**Syntax:**

```bash
moves settings list
```

**Example Output:**
```
Current Settings:
  model: openai/gpt-4o-mini
  key: sk-proj-****************************
```

### `settings set`

Updates a configuration setting with a new value.

**Syntax:**

```bash
moves settings set <KEY> <VALUE>
```

**Arguments:**

| Argument | Type     | Description                          |
| :------- | :------- | :----------------------------------- |
| `key`    | Required | Setting name (`model` or `key`)      |
| `value`  | Required | New value for the setting            |

**Valid Keys:**

| Key     | Description                                          | Example Value                 |
| :------ | :--------------------------------------------------- | :---------------------------- |
| `model` | LLM model identifier (LiteLLM-compatible format)     | `openai/gpt-4o-mini`          |
| `key`   | API key for the selected LLM provider                | `sk-proj-...`                 |

**Examples:**

```bash
# Configure OpenAI model
moves settings set model openai/gpt-4o-mini

# Configure Google Gemini model
moves settings set model gemini/gemini-2.0-flash

# Configure Anthropic Claude model
moves settings set model anthropic/claude-3-5-sonnet-20241022

# Set API key
moves settings set key YOUR_API_KEY_HERE
```

**Supported Model Formats:**
- OpenAI: `openai/gpt-4o-mini`, `openai/gpt-4o`
- Google: `gemini/gemini-2.0-flash`, `gemini/gemini-1.5-pro`
- Anthropic: `anthropic/claude-3-5-sonnet-20241022`
- For complete list, visit: [LiteLLM Supported Models](https://models.litellm.ai/)

### `settings unset`

Resets a configuration setting to its default value or clears it.

**Syntax:**

```bash
moves settings unset <KEY>
```

**Arguments:**

| Argument | Type     | Description                          |
| :------- | :------- | :----------------------------------- |
| `key`    | Required | Setting name to reset (`model` or `key`) |

**Examples:**

```bash
# Reset model to default
moves settings unset model

# Clear stored API key
moves settings unset key
```

**Behavior:**
- Reads default value from system template
- Overwrites user configuration with default
- For `key`, removes the stored API key entirely

## Common Workflows

### Complete Setup from Scratch

```bash
# 1. Configure LLM model and API key
moves settings set model openai/gpt-4o-mini
moves settings set key sk-your-api-key-here

# 2. Create speaker profile
moves speaker add "Conference Speaker" ./keynote.pdf ./speech_notes.pdf

# 3. Process speaker data
moves speaker process "Conference Speaker"

# 4. Launch presentation control
moves presentation control "Conference Speaker"
```

### Managing Multiple Speakers

```bash
# Add multiple speaker profiles
moves speaker add "Speaker A" ./presentation_A.pdf ./transcript_A.pdf
moves speaker add "Speaker B" ./presentation_B.pdf ./transcript_B.pdf

# View all speakers
moves speaker list

# Process all speakers simultaneously
moves speaker process --all

# View detailed information for specific speaker
moves speaker show "Speaker A"

# Control presentation for specific speaker
moves presentation control "Speaker A"
```

### Updating Existing Speaker Data

```bash
# Update presentation file
moves speaker edit "John Doe" --presentation ./updated_slides.pdf

# Update both files
moves speaker edit "John Doe" -p ./new_slides.pdf -t ./new_transcript.pdf

# Re-process after updates
moves speaker process "John Doe"
```

### Troubleshooting

```bash
# Verify current configuration
moves settings list

# Check speaker profile details
moves speaker show "Your Speaker Name"

# Re-process if data appears out of sync
moves speaker process "Your Speaker Name"

# Switch to different LLM model
moves settings set model gemini/gemini-2.0-flash
moves settings set key YOUR_GEMINI_API_KEY
moves speaker process --all
```

### Working with Speaker IDs

When multiple speakers share the same name, use unique IDs for precise identification:

```bash
# List shows both name and ID
moves speaker list
# Output:
#   1. John Doe (john-doe-a1b2c)
#   2. John Doe (john-doe-x7y8z)

# Use ID for specific operations
moves speaker show john-doe-a1b2c
moves speaker process john-doe-x7y8z
moves presentation control john-doe-a1b2c
```
