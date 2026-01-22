# Configuration Guide

Detailed documentation for configuring `moves`, including LLM providers, API keys, and tuning options.

## Table of Contents

1. [Basic Configuration](#basic-configuration)
2. [LLM Providers](#llm-providers)
3. [API Keys & Security](#api-keys--security)
4. [Configuration Files](#configuration-files)
5. [Performance Tuning](#performance-tuning)
6. [Advanced Settings](#advanced-settings)

## Basic Configuration

### What You Need to Configure

Two main settings control `moves` behavior:

1. **LLM Model** – Which AI model to use for section generation
2. **API Key** – Authentication for your chosen LLM provider

### Quick Setup (Google Gemini - Recommended)

Google Gemini is free and doesn't require a credit card:

```powershell
# 1. Get free API key from https://aistudio.google.com/app/apikey
# 2. Configure in moves
moves settings set model gemini/gemini-2.5-flash-lite
moves settings set key
# 3. Paste API key when prompted (text hidden)
```

Verify:
```powershell
moves settings list
```

---

## LLM Providers

`moves` uses [LiteLLM](https://docs.litellm.ai/), which supports **100+ models** across multiple providers.

### Recommended Providers

#### 1. Google Gemini (Free) ⭐ Best for Beginners

**Why**: Free tier, no credit card required, good quality, works for English.

**Setup**:
1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with Google account
3. Click "Create API key"
4. Copy key

**Configure**:
```powershell
moves settings set model gemini/gemini-2.5-flash-lite
moves settings set key
# Paste: [your-api-key]
```

**Available Models**:
- `gemini/gemini-2.5-flash-lite` (recommended, fastest)
- `gemini/gemini-2.5-flash`
- `gemini/gemini-1.5-pro`

---

#### 2. OpenAI (Paid) ✓ Reliable

**Why**: Very reliable, excellent model quality, pay-as-you-go.

**Cost**: ~$0.50-$2 per presentation prep (typical usage).

**Setup**:
1. Create account at [OpenAI Platform](https://platform.openai.com/)
2. Add payment method
3. Go to [API Keys](https://platform.openai.com/account/api-keys)
4. Create new key

**Configure**:
```powershell
moves settings set model gpt-4o-mini
moves settings set key
# Paste: [your-api-key]
```

**Available Models**:
- `gpt-4o-mini` (recommended, fast and cheap)
- `gpt-4o`
- `gpt-4-turbo`

---

#### 3. Anthropic Claude (Paid) ✓ High Quality

**Why**: Excellent reasoning, good for complex transcripts.

**Cost**: ~$1-$3 per presentation prep.

**Setup**:
1. Create account at [Anthropic Console](https://console.anthropic.com/)
2. Add payment method
3. Go to API Keys section
4. Create new key

**Configure**:
```powershell
moves settings set model claude-3-5-sonnet
moves settings set key
# Paste: [your-api-key]
```

**Available Models**:
- `claude-3-5-sonnet` (recommended)
- `claude-3-opus`
- `claude-3-haiku`

---

#### 4. Other Providers Supported

LiteLLM supports many more:

| Provider | Model | Cost |
|----------|-------|------|
| Hugging Face | `huggingface/model-name` | Free |
| Groq | `groq/mixtral-8x7b-32768` | Free |
| Together AI | `together_ai/model` | Free/Paid |
| Azure OpenAI | `azure/model` | Paid |
| Replicate | `replicate/model` | Paid |

See [LiteLLM Docs](https://docs.litellm.ai/docs/providers) for full list.

---

## API Keys & Security

### Storing API Keys Securely

`moves` uses **Windows Credential Manager** to store API keys:

- **Never stored as plain text** in config files
- **System-level security** – Windows encrypts them
- **Per-user** – Only accessible by your Windows account

### Setting an API Key

```powershell
moves settings set key
```

**Important**: 
- Text input is **hidden** for security
- Press Enter when done
- Paste (Ctrl+V) works fine

### Viewing Your API Key

To see if a key is set:
```powershell
moves settings list
```

Shows masked format: `gemi****b8fk`

To see full key (use carefully):
```powershell
moves settings list --show
```

### Changing Your API Key

To update with a new key:
```powershell
moves settings set key
# Enter new key
```

Previous key is replaced.

### Removing Your API Key

To remove/reset:
```powershell
moves settings unset key
```

Then you'll need to set it again before using auto-preparation.

### Troubleshooting API Keys

**"Invalid API key"**
- Double-check you copied the full key
- Check that the key hasn't expired
- Verify it's for the correct model provider

**"Access denied"**
- Key might not have required permissions
- Try generating a new key from provider

**"Rate limit exceeded"**
- Too many API calls in short time
- Wait a few minutes
- Consider upgrading your plan

---

## Configuration Files

### Location

All configuration is stored in: `C:\Users\<YourUsername>\.moves\`

```
~/.moves/
├── settings.toml          # LLM model config (plain text)
├── settings.key           # API key (in Credential Manager)
├── ml_models/             # ONNX models (downloaded automatically)
│   ├── all-MiniLM-L6-v2_quint8_avx2/
│   └── nemo-streaming-stt-480ms-int8/
└── speakers/              # Speaker data
    └── <speaker-id>/
        ├── speaker.yaml
        └── sections.md
```

### settings.toml

Contains your LLM model choice. Example:

```toml
model = "gemini/gemini-2.5-flash-lite"
```

You can edit this directly if needed:

```powershell
notepad $env:USERPROFILE\.moves\settings.toml
```

But use the CLI for safety:

```powershell
moves settings set model gemini/gemini-2.5-flash-lite
```

### Credential Manager (API Key)

Your API key is stored in Windows Credential Manager:

**To view manually:**
1. Settings → Manage credentials (search)
2. Select "Windows Credentials"
3. Look for `moves-api-key`

**Via command line:**
```powershell
# View all stored credentials
cmdkey /list
```

---

## Performance Tuning

Configuration options in [config.py](../src/moves_cli/config.py) that affect behavior:

### Similarity Matching Tuning

```python
SEMANTIC_WEIGHT = 0.6           # 60% semantic matching
PHONETIC_WEIGHT = 0.4           # 40% phonetic matching
SIMILARITY_THRESHOLD = 0.7      # Minimum score to auto-advance
```

**Adjust if:**
- **Too many false positives** (advancing too easily)
  - Increase `SIMILARITY_THRESHOLD` (0.8-0.9)
  - Increase `SEMANTIC_WEIGHT` (0.7-0.8)
- **Missing advances** (need to navigate manually)
  - Decrease `SIMILARITY_THRESHOLD` (0.5-0.6)
  - Decrease `SEMANTIC_WEIGHT` (0.4-0.5)

**Note**: Currently requires editing source code and reinstalling.

### Voice Activity Detection (VAD) Tuning

```python
VAD_THRESHOLD = 0.35            # Lower = more sensitive
VAD_MIN_SILENCE = 0.5           # Seconds to end speech
VAD_MIN_SPEECH = 0.1            # Minimum speech length
```

**Adjust if:**
- **Background noise being detected**
  - Increase `VAD_THRESHOLD` (0.5-0.7)
- **Speech not being detected**
  - Decrease `VAD_THRESHOLD` (0.1-0.2)
- **Pauses within phrases cutting segments**
  - Increase `VAD_MIN_SILENCE` (1.0-2.0)

**Note**: These are tuned for typical office/home environments.

### Chunk Generation

```python
WINDOW_SIZE = 12                # Words per chunk (larger = broader matches)
CANDIDATE_RANGE_MIN_OFFSET = -3 # Search 3 slides back
CANDIDATE_RANGE_MAX_OFFSET = 5  # Search 5 slides forward
```

**Adjust if:**
- **Matching too sensitive to exact wording**
  - Increase `WINDOW_SIZE` (15-20)
- **Missing slides that have different wording**
  - Decrease `WINDOW_SIZE` (8-10)

---

## Advanced Settings

### Using Multiple API Keys

If you want to test different providers:

```powershell
# Set key for provider A
moves settings set key
# Paste: provider-a-key

# Prepare speakers
moves speaker prepare MyTalk

# Switch to provider B
moves settings set key
# Paste: provider-b-key

# Prepare same speaker again (regenerates with provider B)
moves speaker prepare MyTalk
```

Both preparations will be saved in the speaker's metadata.

### Custom LLM Prompts

The LLM instruction used during preparation is in:

`src/moves_cli/data/llm_instruction.md`

This file is bundled with `moves` and controls how the LLM generates sections. Modifying this requires:

1. Editing the file in source
2. Rebuilding `moves` from source
3. See [Development Guide](DEVELOPMENT.md) for building

### Offline Preparation (Manual Mode)

If you want to prepare speakers completely offline:

```powershell
moves speaker prepare MyTalk --manual
```

This generates an empty template that you manually edit:

```powershell
notepad $env:USERPROFILE\.moves\speakers\a1b2c\sections.md
```

### Environment Variables

Currently, `moves` doesn't use environment variables for configuration. All settings go through the CLI or config files.

---

## Troubleshooting Configuration

### "Setting model failed"

**Cause**: Invalid model name.

**Solution**: Check supported models at [LiteLLM Docs](https://docs.litellm.ai/docs/providers).

```powershell
# Example: Correct format
moves settings set model gemini/gemini-2.5-flash-lite
# Not: moves settings set model Gemini 2.5 Flash
```

### "LLM API key error during preparation"

**Causes**:
1. Invalid or expired key
2. Model name mismatch with key provider
3. No remaining API quota

**Solutions**:
```powershell
# Verify settings
moves settings list

# Test with different provider
moves settings set model gpt-4o-mini
moves settings set key
# Paste OpenAI key
moves speaker prepare MyTalk
```

### "Models taking too long to download"

**Cause**: First run downloads ~400-500MB of ONNX models.

**Solution**: Wait for completion (5-10 minutes typical). Check progress:

```powershell
dir $env:USERPROFILE\.moves\ml_models
```

### "Credential Manager not available"

**On non-Windows systems**: The tool expects Windows Credential Manager. On macOS/Linux, uses system keyring.

**Solution**: Ensure you're on Windows 10+ or use manual `--manual` mode.

---

## Configuration Examples

### Example 1: Use Google Gemini

```powershell
# One-time setup
moves settings set model gemini/gemini-2.5-flash-lite
moves settings set key
# Paste your free API key from: https://aistudio.google.com/app/apikey

# Ready to use
moves speaker add MyTalk talk.pdf transcript.txt
moves speaker prepare MyTalk
moves present MyTalk
```

### Example 2: Use OpenAI GPT-4o

```powershell
# One-time setup
moves settings set model gpt-4o-mini
moves settings set key
# Paste your paid OpenAI API key

# Ready to use
moves speaker prepare MyTalk --yes
moves present MyTalk
```

### Example 3: Hybrid (Auto + Manual)

```powershell
# Use LLM for initial generation
moves settings set model gemini/gemini-2.5-flash-lite
moves settings set key
moves speaker prepare MyTalk

# Manually fine-tune
notepad $env:USERPROFILE\.moves\speakers\a1b2c\sections.md
# Edit as needed

# Use manually tuned version for presentation
moves present MyTalk
```

### Example 4: Offline (Manual Only)

```powershell
# No LLM needed
moves speaker add MyTalk talk.pdf transcript.txt
moves speaker prepare MyTalk --manual

# Manually create content
notepad $env:USERPROFILE\.moves\speakers\a1b2c\sections.md

# Present without any API keys
moves present MyTalk
```

---

## Best Practices

1. **Use free tier first** – Test with Google Gemini before paying
2. **Re-prepare after LLM changes** – Different models may generate different content
3. **Keep API keys secure** – Never share or commit them
4. **Regular backups** – Copy `~/.moves/speakers/` occasionally
5. **Test audio first** – Verify microphone before presenting

---

For more information, see:
- [Getting Started Guide](GETTING_STARTED.md) – User walkthrough
- [Architecture Guide](ARCHITECTURE.md) – Technical details
- [CLI Reference](CLI_REFERENCE.md) – All commands
