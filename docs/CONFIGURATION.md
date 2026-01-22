# Configuration Guide

Complete guide to configuring `moves`, including LLM providers, API keys, and performance tuning.

## Table of Contents

1. [Basic Configuration](#basic-configuration)
2. [LLM Providers](#llm-providers)
3. [API Key Security](#api-key-security)
4. [Configuration Files](#configuration-files)
5. [Performance Tuning](#performance-tuning)
6. [Advanced Settings](#advanced-settings)
7. [Troubleshooting](#troubleshooting)

---

## Basic Configuration

### What You Need to Configure

Two settings control section generation:

| Setting | Purpose | Storage |
|---------|---------|---------|
| `model` | LLM model for section generation | `~/.moves/settings.toml` |
| `key` | API key for LLM provider | System keyring (secure) |

### Quick Setup (Google Gemini – Free)

```bash
# 1. Get free API key from https://aistudio.google.com/app/apikey
# 2. Configure moves
moves settings set model gemini/gemini-2.5-flash-lite
moves settings set key
# 3. Paste your API key when prompted
```

Verify configuration:
```bash
moves settings list
```

---

## LLM Providers

`moves` uses [LiteLLM](https://docs.litellm.ai/), supporting 100+ LLM providers.

### Google Gemini ⭐ Recommended (Free)

**Why:** Free tier, no credit card, good quality.

**Setup:**
1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with Google account
3. Click "Create API key"
4. Copy the key

**Configure:**
```bash
moves settings set model gemini/gemini-2.5-flash-lite
moves settings set key
# Paste your API key
```

**Models:**
| Model | Speed | Quality |
|-------|-------|---------|
| `gemini/gemini-2.5-flash-lite` | Fast | Good (recommended) |
| `gemini/gemini-2.5-flash` | Medium | Better |
| `gemini/gemini-1.5-pro` | Slower | Best |

---

### OpenAI (Paid)

**Why:** Reliable, excellent quality, pay-as-you-go.

**Cost:** ~$0.01-$0.10 per preparation (typical).

**Setup:**
1. Create account at [OpenAI Platform](https://platform.openai.com/)
2. Add payment method
3. Go to [API Keys](https://platform.openai.com/account/api-keys)
4. Create new key

**Configure:**
```bash
moves settings set model gpt-4o-mini
moves settings set key
# Paste your OpenAI API key
```

**Models:**
| Model | Speed | Quality | Cost |
|-------|-------|---------|------|
| `gpt-4o-mini` | Fast | Good | Low |
| `gpt-4o` | Medium | Better | Medium |
| `gpt-4-turbo` | Slower | Best | Higher |

---

### Anthropic Claude (Paid)

**Why:** Excellent reasoning, good for complex transcripts.

**Setup:**
1. Create account at [Anthropic Console](https://console.anthropic.com/)
2. Add payment method
3. Create API key

**Configure:**
```bash
moves settings set model claude-3-5-sonnet
moves settings set key
# Paste your Anthropic API key
```

**Models:**
| Model | Speed | Quality |
|-------|-------|---------|
| `claude-3-haiku` | Fast | Good |
| `claude-3-5-sonnet` | Medium | Better |
| `claude-3-opus` | Slower | Best |

---

### Groq (Free Tier)

**Why:** Free tier available, fast inference.

**Setup:**
1. Create account at [Groq Console](https://console.groq.com/)
2. Get API key

**Configure:**
```bash
moves settings set model groq/mixtral-8x7b-32768
moves settings set key
# Paste your Groq API key
```

---

### Other Providers

LiteLLM supports many more providers. See [LiteLLM Providers](https://docs.litellm.ai/docs/providers) for full list.

| Provider | Model Format | Free Tier |
|----------|--------------|-----------|
| Hugging Face | `huggingface/<model>` | Yes |
| Together AI | `together_ai/<model>` | Yes |
| Azure OpenAI | `azure/<deployment>` | No |
| AWS Bedrock | `bedrock/<model>` | No |

---

## API Key Security

### How Keys Are Stored

`moves` stores API keys securely using the system keyring:

| Platform | Storage |
|----------|---------|
| Windows | Windows Credential Manager |
| macOS | Keychain |
| Linux | Secret Service (GNOME Keyring, KWallet, etc.) |

**Keys are:**
- Never stored in plain text files
- Encrypted by the operating system
- Only accessible by your user account

### Managing Keys

**Set a key:**
```bash
moves settings set key
# Input is hidden for security
```

**View key (masked):**
```bash
moves settings list
# Shows: gemi****b8fk
```

**View key (full):**
```bash
moves settings list --show
# Shows: gemiXXXXXXXXXXXXb8fk
```

**Remove key:**
```bash
moves settings unset key
```

### Windows Credential Manager

To view stored credentials manually:
1. Open "Credential Manager" from Start menu
2. Select "Windows Credentials"
3. Look for `moves-cli` entries

---

## Configuration Files

### File Locations

```
~/.moves/
├── settings.toml              # LLM model configuration
├── ml_models/                 # Downloaded ONNX models
│   ├── all-MiniLM-L6-v2_quint8_avx2/
│   ├── nemo-streaming-stt-480ms-int8/
│   └── silero-vad-int8/
└── speakers/                  # Speaker data
    └── <speaker-id>/
        ├── speaker.yaml       # Metadata and hashes
        └── sections.md        # Speech content
```

### settings.toml

Contains your LLM model choice:

```toml
# moves CLI Configuration

# Note: API key is stored securely in system keyring

# LLM model for speaker processing, find models at: https://models.litellm.ai/
model = "gemini/gemini-2.5-flash-lite"
```

Edit directly:
```bash
nano ~/.moves/settings.toml
```

Or use the CLI:
```bash
moves settings set model gemini/gemini-2.5-flash-lite
```

### speaker.yaml

Per-speaker metadata (created automatically):

```yaml
name: MyTalk
speaker_id: a1b2c
source_presentation: /path/to/presentation.pdf
source_transcript: /path/to/transcript.txt
last_processed: '2024-01-15T14:30:00'
presentation_hash: abc123def456
transcript_hash: 789xyz012345
sections_hash: fedcba987654
```

---

## Performance Tuning

Configuration constants are in `src/moves_cli/config.py`. Currently requires source code editing.

### Similarity Matching

```python
SEMANTIC_WEIGHT = 0.6          # Weight for semantic (embedding) matching
PHONETIC_WEIGHT = 0.4          # Weight for phonetic (sound) matching
SIMILARITY_THRESHOLD = 0.7     # Minimum score to auto-advance (0.0-1.0)
```

**Tuning:**
| Issue | Adjustment |
|-------|------------|
| Too many false positives | Increase `SIMILARITY_THRESHOLD` (0.8-0.9) |
| Missing advances | Decrease `SIMILARITY_THRESHOLD` (0.5-0.6) |
| Emphasis on meaning | Increase `SEMANTIC_WEIGHT` |
| Emphasis on pronunciation | Increase `PHONETIC_WEIGHT` |

### Chunk Generation

```python
WINDOW_SIZE = 12                    # Words per matching chunk
CANDIDATE_RANGE_MIN_OFFSET = -3     # Search 3 slides back
CANDIDATE_RANGE_MAX_OFFSET = 5      # Search 5 slides forward
```

**Tuning:**
| Issue | Adjustment |
|-------|------------|
| Too sensitive to exact wording | Increase `WINDOW_SIZE` (15-20) |
| Missing similar content | Decrease `WINDOW_SIZE` (8-10) |
| Slow matching | Decrease offset range |

### Voice Activity Detection (VAD)

```python
VAD_THRESHOLD = 0.35           # Lower = more sensitive (0.1-0.9)
VAD_MIN_SILENCE = 0.5          # Seconds of silence to end segment
VAD_MIN_SPEECH = 0.1           # Minimum speech duration to detect
VAD_WINDOW_SIZE = 512          # Analysis window (~32ms at 16kHz)
VAD_BUFFER_SIZE = 30.0         # Circular buffer in seconds
```

**Tuning:**
| Issue | Adjustment |
|-------|------------|
| Background noise detected | Increase `VAD_THRESHOLD` (0.5-0.7) |
| Speech not detected | Decrease `VAD_THRESHOLD` (0.1-0.2) |
| Pauses cutting phrases | Increase `VAD_MIN_SILENCE` (1.0-2.0) |

---

## Advanced Settings

### Using Multiple LLM Providers

You can switch providers anytime:

```bash
# Use Gemini
moves settings set model gemini/gemini-2.5-flash-lite
moves settings set key
moves speaker prepare MyTalk

# Switch to OpenAI
moves settings set model gpt-4o-mini
moves settings set key
moves speaker prepare MyTalk  # Re-generates with new model
```

### Custom LLM Prompts

The LLM instruction is in `src/moves_cli/data/llm_instruction.md`. To customize:

1. Edit the file in source
2. Rebuild and reinstall moves
3. See [Development Guide](DEVELOPMENT.md)

### Offline Mode

For fully offline operation:

```bash
# Prepare with manual mode (no LLM)
moves speaker prepare MyTalk --manual

# Edit sections.md manually
nano ~/.moves/speakers/a1b2c/sections.md

# Present (fully offline after models downloaded)
moves present MyTalk
```

### Environment Variables

Currently, `moves` doesn't use environment variables. All configuration goes through the CLI or config files.

---

## Troubleshooting

### "LLM model not configured"

**Cause:** No model set.

**Solution:**
```bash
moves settings set model gemini/gemini-2.5-flash-lite
```

### "LLM API key not configured"

**Cause:** No API key set.

**Solution:**
```bash
moves settings set key
# Paste your key
```

### "Invalid API key"

**Causes:**
- Key copied incorrectly
- Key expired or revoked
- Key for wrong provider

**Solutions:**
- Verify the key is complete
- Generate a new key from your provider
- Ensure model and key match (e.g., Gemini key with Gemini model)

### "Rate limit exceeded"

**Cause:** Too many API calls in short time.

**Solutions:**
- Wait a few minutes
- Upgrade your provider plan
- Use `--yes` to batch process (reduces confirmations)

### Models Download Slow

**Cause:** First run downloads ~500MB of ONNX models.

**Solution:** Wait for completion. Check progress:
```bash
ls -la ~/.moves/ml_models/
```

### Keyring Not Available

**Cause:** System keyring not configured.

**Solutions:**
- **Linux:** Install and start `gnome-keyring` or `kwallet`
- **macOS:** Ensure Keychain is unlocked
- **Windows:** Should work out of box

---

## Configuration Examples

### Example 1: Free Setup with Gemini

```bash
# Get API key from https://aistudio.google.com/app/apikey
moves settings set model gemini/gemini-2.5-flash-lite
moves settings set key
# Paste key

# Prepare and present
moves speaker add MyTalk slides.pdf notes.txt
moves speaker prepare MyTalk
moves present MyTalk
```

### Example 2: OpenAI for Better Quality

```bash
moves settings set model gpt-4o
moves settings set key
# Paste OpenAI key

moves speaker prepare MyTalk
```

### Example 3: Fully Offline

```bash
# No LLM configuration needed
moves speaker add MyTalk slides.pdf notes.txt
moves speaker prepare MyTalk --manual

# Edit sections.md manually
nano ~/.moves/speakers/a1b2c/sections.md

# Present (fully offline)
moves present MyTalk
```

### Example 4: Hybrid Approach

```bash
# Use LLM for initial generation
moves settings set model gemini/gemini-2.5-flash-lite
moves settings set key
moves speaker prepare MyTalk

# Fine-tune manually
nano ~/.moves/speakers/a1b2c/sections.md

# Present with custom edits
moves present MyTalk
```

---

## Best Practices

1. **Start with free tier** – Test with Gemini before paying
2. **Re-prepare after model changes** – Different models generate different content
3. **Keep keys secure** – Never share or commit API keys
4. **Backup speaker data** – Periodically copy `~/.moves/speakers/`
5. **Test before presenting** – Do a dry run in a quiet environment

---

For more information:
- [Getting Started](GETTING_STARTED.md) – Step-by-step walkthrough
- [CLI Reference](CLI_REFERENCE.md) – All commands
- [Architecture](ARCHITECTURE.md) – How it works
