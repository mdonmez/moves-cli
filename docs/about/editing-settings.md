# Editing Settings

Application configuration in `moves` is managed by the `SettingsEditor`, a component designed for robust and user-friendly interaction with the system's settings. This is particularly important for configuring the Large Language Model (LLM) required for data processing.

## Configuration Strategy

Settings are stored in `~/.moves/settings.toml`, a human-readable TOML file. The system's design philosophy is to never modify the application's source code for configuration. Instead, it relies on a template file (`src/data/settings_template.toml`) that defines the default values and structure, including comments explaining each setting.

On its first run, the `SettingsEditor` copies this template to the user's data directory. On subsequent runs, it intelligently merges the template defaults with the user's file; user-defined values always take precedence. This ensures that new settings can be introduced in future updates without overwriting existing user configurations.

The `tomlkit` library is used for all TOML parsing and writing. Unlike other libraries, `tomlkit` is designed to preserve the original file's formatting, including comments, whitespace, and key order, making the configuration file easy for users to manage both via the CLI and manually.

## Key Settings

- **`model`:** Defines the LLM used by the `section_producer`. `moves` leverages `litellm` to act as a unified interface to hundreds of LLM providers. The value must be a `litellm`-compatible model string (e.g., `openai/gpt-4o-mini`).
- **`key`:** Stores the API key for the selected model's provider.

## CLI-Based Management

The `moves settings` subcommand provides a safe and structured interface for modifying these settings.

- **`moves settings list`:** Reads and displays the current, merged configuration, showing either the user-set value or the system default.
- **`moves settings set <KEY> <VALUE>`:** Modifies a setting. Before writing to the file, the `SettingsEditor` validates that the provided `<KEY>` exists in the template, preventing users from adding arbitrary or misspelled keys.
- **`moves settings unset <KEY>`:** Resets a specific key to its default value. The `SettingsEditor` achieves this by reading the default value from its in-memory copy of the template and writing that back into the user's `settings.toml` file, or removing the key if it's not in the template. This provides a reliable way to revert to a known-good state.
