# Settings Management System

## Overview

The `SettingsEditor` component manages application-wide configuration through a robust, user-friendly interface. It handles LLM model settings and API keys required for presentation data processing.

## Configuration Architecture

### Storage Location

Settings are persisted in `~/.moves/settings.toml`, a human-readable TOML configuration file.

### Template-Based Design

The system follows a template-driven approach to ensure consistency and support future updates:

**System Template:** `src/moves_cli/data/settings_template.toml`
- Defines all valid configuration keys
- Provides default values
- Includes explanatory comments for each setting
- Maintained as part of the application source code

**User Configuration:** `~/.moves/settings.toml`
- User-specific values override template defaults
- Preserves formatting and comments via `tomlkit`
- Automatically created on first run
- Intelligently merged with template on each access

### Initialization Process

When `SettingsEditor` is instantiated:

1. **Load Template:** Read system template into memory
2. **Extract Defaults:** Parse template defaults as base configuration
3. **Read User File:** Load existing user settings (if present)
4. **Merge Configurations:** User values override template defaults
5. **Persist:** Write merged configuration back to user file

This approach ensures:
- New settings from updates are automatically available
- User customizations are preserved
- Invalid or deprecated keys are filtered out
- File structure and comments remain intact

## Configuration Parameters

### `model`

**Type:** String

**Purpose:** Specifies the LLM used by `section_producer` for transcript segmentation

**Format:** LiteLLM-compatible model identifier

**Examples:**
- `"openai/gpt-4o-mini"`
- `"gemini/gemini-2.0-flash"`
- `"anthropic/claude-3-5-sonnet-20241022"`

**Details:**
The system uses `litellm` as a universal interface to hundreds of LLM providers. The model string follows the format: `provider/model-name`. This abstraction allows seamless switching between different LLM services without code changes.

**Reference:** [LiteLLM Supported Models](https://models.litellm.ai/)

### `key`

**Type:** String

**Purpose:** Stores the API key for the selected LLM provider

**Security Considerations:**
- Stored in plaintext in the TOML file
- File permissions should restrict access to the user
- Different providers require different key formats
- Never commit this file to version control

**Example Values:**
- OpenAI: `"sk-proj-..."`
- Gemini: `"AIza..."`
- Anthropic: `"sk-ant-..."`

## TOML Processing with `tomlkit`

### Why `tomlkit`?

Unlike standard TOML parsers, `tomlkit` preserves the original file's formatting:
- **Comments:** Explanatory text remains in place
- **Whitespace:** Visual structure is maintained
- **Key Order:** Settings appear in the same sequence
- **Manual Editing:** Users can safely edit files by hand

This makes the configuration file both machine-parseable and human-friendly.

### Preservation Mechanism

When writing settings, `SettingsEditor`:

1. Creates a deep copy of the template document structure
2. Updates only the values for keys that exist in the merged configuration
3. Writes the complete document structure with preserved formatting
4. Ensures comments and structure match the template

Result: User file remains clean and readable even after multiple programmatic updates.

## CLI-Based Management

The `moves settings` command provides a safe, validated interface for configuration management.

### `moves settings list`

**Purpose:** Display current configuration

**Behavior:**
- Shows merged configuration (template defaults + user overrides)
- Indicates which values are defaults vs. user-set
- Displays API key in masked format for security

**Example Output:**
```
Current Settings:
  model: openai/gpt-4o-mini
  key: sk-proj-****************************
```

### `moves settings set <KEY> <VALUE>`

**Purpose:** Modify a configuration setting

**Validation:**
- Verifies `KEY` exists in the template (prevents typos)
- Rejects unknown keys to maintain configuration integrity
- Type validation could be added in future versions

**Process:**
1. Check if `KEY` is valid (exists in template)
2. Update in-memory configuration
3. Call `_save()` to persist changes
4. Preserve file structure via `tomlkit`

**Error Handling:**
- Returns `False` if key is invalid
- Raises `RuntimeError` if file write fails

### `moves settings unset <KEY>`

**Purpose:** Reset setting to default value

**Behavior:**
- Reads default value from template
- Overwrites user value with default
- For API keys, effectively clears the stored credential
- Maintains file structure and comments

**Implementation:**
1. Retrieve default value from in-memory template
2. Update configuration with default
3. Write to file via `_save()`
4. File remains properly formatted

## Implementation Details

### File Save Process

The `_save()` method handles all file persistence:

```python
def _save(self) -> bool:
    # 1. Ensure parent directory exists
    self.settings.parent.mkdir(parents=True, exist_ok=True)
    
    # 2. Create fresh template copy
    node = copy.deepcopy(self._template_doc)
    
    # 3. Update values for valid keys
    for key in self._template_defaults.keys():
        if key in self._data:
            node[key] = self._data[key]
    
    # 4. Write with UTF-8 encoding
    with self.settings.open("w", encoding="utf-8") as f:
        f.write(tomlkit.dumps(node))
    
    return True
```

### Error Recovery

If the user file becomes corrupted:
- Initialization catches exceptions during file read
- Falls back to template defaults (`user_data = {}`)
- Automatically repairs the file on next save
- User loses custom settings but system remains functional

This design prioritizes system availability over configuration preservation in error scenarios.
