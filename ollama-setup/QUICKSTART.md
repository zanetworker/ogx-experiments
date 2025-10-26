# Llama Stack with Ollama - Quick Start

## TL;DR

```bash
# 1. Install dependencies (one-time)
./experiments/ollama-setup/install-deps.sh

# 2. Set environment variables
export OLLAMA_URL="http://0.0.0.0:11434"
export LLAMA_STACK_PORT=8321

# 3. Run the stack
./experiments/ollama-setup/run-ollama-stack.sh
```

## What Changed?

**The `llama stack build` command no longer exists!** 

You can now run the stack directly without a build step.

## Step-by-Step Guide

### 1. Install Dependencies (First Time Only)

```bash
./experiments/ollama-setup/install-deps.sh
```

Or manually:
```bash
python -m llama_stack.cli.llama stack list-deps starter | xargs pip install
```

### 2. Configure Environment Variables

```bash
# Required
export OLLAMA_URL="http://0.0.0.0:11434"

# Optional (defaults provided)
export LLAMA_STACK_PORT=8321
export INFERENCE_MODEL="meta-llama/Llama-3.2-3B-Instruct"
export LOG_LEVEL="DEBUG"

# Optional API keys (if using these providers)
export OPENAI_API_KEY="your-key"
export BRAVE_SEARCH_API_KEY="your-key"
export TAVILY_SEARCH_API_KEY="your-key"
```

### 3. Run the Stack

**Option A: Using the script (easiest)**
```bash
./experiments/ollama-setup/run-ollama-stack.sh
```

**Option B: Direct command**
```bash
python -m llama_stack.cli.llama stack run \
  experiments/ollama-setup/ollama-stack-run.yaml \
  --port $LLAMA_STACK_PORT
```

**Option C: Using the starter distribution**
```bash
python -m llama_stack.cli.llama stack run starter --port 8321
```

## Verify It's Working

Once the stack is running, you should see:
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://['::', '0.0.0.0']:8321 (Press CTRL+C to quit)
```

Test with curl:
```bash
curl http://localhost:8321/health
```

## Configuration Files

- **`experiments/ollama-setup/ollama-stack-run.yaml`** - Main configuration file (updated to v2 format)
- **`experiments/ollama-stack-build.yaml`** - Build config (only needed for Docker builds)
- **`experiments/ollama-setup/run-ollama-stack.sh`** - Convenience script to run the stack
- **`experiments/ollama-setup/install-deps.sh`** - Script to install dependencies

## Key Differences from Old Workflow

| Old Workflow | New Workflow |
|--------------|--------------|
| `llama stack build` | ❌ No longer exists |
| `--image-type venv` | ❌ Deprecated |
| `--image-name myenv` | ❌ Deprecated |
| Build then run | ✅ Just run directly |
| Separate build.yaml | ✅ Only need run.yaml |

## Common Issues

### "llama: command not found"
```bash
# Use the full Python module path
python -m llama_stack.cli.llama stack run ...
```

### "Module not found"
```bash
# Install dependencies
./experiments/ollama-setup/install-deps.sh
```

### "Port already in use"
```bash
# Use a different port
export LLAMA_STACK_PORT=8322
./experiments/ollama-setup/run-ollama-stack.sh
```

### Ollama not accessible
```bash
# Make sure Ollama is running
ollama serve

# Check the URL is correct
export OLLAMA_URL="http://localhost:11434"  # or http://0.0.0.0:11434
```

## Next Steps

- Read the full migration guide: `experiments/README-MIGRATION.md`
- Customize your run.yaml configuration
- Add more providers or models
- Build a Docker image for production deployment

## Useful Commands

```bash
# List available distributions
python -m llama_stack.cli.llama stack list

# List dependencies
python -m llama_stack.cli.llama stack list-deps starter

# List available providers
python -m llama_stack.cli.llama stack list-providers

# List available APIs
python -m llama_stack.cli.llama stack list-apis
```

## Need Help?

Check the detailed migration guide:
```bash
cat experiments/ollama-setup/README-MIGRATION.md
```

