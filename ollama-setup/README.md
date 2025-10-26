# Llama Stack with Ollama Setup

> ✅ **Status**: Migration complete and working!
> 📅 **Last Updated**: 2025-10-21
> 📦 **Configuration Version**: v2

This directory contains everything you need to run Llama Stack with Ollama using the **v2 configuration format**.

**Quick Links**: [Quick Start](#-quick-start) | [Documentation](#-documentation) | [Troubleshooting](TROUBLESHOOTING.md) | [Migration Guide](MIGRATION-GUIDE.md)

## 📁 Files in This Directory

### Configuration
- **`ollama-stack-run.yaml`** - Main configuration file (✅ v2 format)

### Scripts
- **`run-ollama-stack.sh`** - Convenience script to run the stack
- **`install-deps.sh`** - Script to install all required dependencies

### Documentation
- **`README.md`** - This file (overview and quick start)
- **`QUICKSTART.md`** - Quick reference guide with TL;DR commands
- **`README-MIGRATION.md`** - Migration guide from old `llama stack build` workflow
- **`FIXES.md`** - Technical details of configuration fixes
- **`V2-FORMAT-CHANGES.md`** - Complete v2 format reference and migration guide
- **`CHANGELOG.md`** - Version history and breaking changes

## 🚀 Quick Start

```bash
# 1. Install dependencies (one-time)
./experiments/ollama-setup/install-deps.sh

# 2. Set environment variables
export OLLAMA_URL="http://0.0.0.0:11434"
export LLAMA_STACK_PORT=8321

# 3. Run the stack
./experiments/ollama-setup/run-ollama-stack.sh
```

## 📖 Documentation Guide

| If you want to... | Read this |
|-------------------|-----------|
| Get started quickly | [`QUICKSTART.md`](./QUICKSTART.md) |
| Migrate from old `llama stack build` | [`README-MIGRATION.md`](./README-MIGRATION.md) |
| Understand v2 format changes | [`V2-FORMAT-CHANGES.md`](./V2-FORMAT-CHANGES.md) |
| Check version history | [`CHANGELOG.md`](./CHANGELOG.md) |
| Customize the config | Edit [`ollama-stack-run.yaml`](./ollama-stack-run.yaml) |

## 🔧 Configuration

The main configuration is in `ollama-stack-run.yaml`. Key settings:

- **Providers**: Ollama, OpenAI, FAISS, Llama Guard, etc.
- **APIs**: Inference, Vector I/O, Safety, Agents, Eval, etc.
- **Storage**: SQLite backends for persistence
- **Server**: Port 8321 (configurable via env var)

## 🌐 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_URL` | `http://0.0.0.0:11434` | Ollama server URL |
| `LLAMA_STACK_PORT` | `8321` | Port for Llama Stack server |
| `INFERENCE_MODEL` | `meta-llama/Llama-3.2-3B-Instruct` | Default inference model |
| `OPENAI_API_KEY` | - | OpenAI API key (optional) |
| `BRAVE_SEARCH_API_KEY` | - | Brave Search API key (optional) |
| `TAVILY_SEARCH_API_KEY` | - | Tavily Search API key (optional) |

## 🐛 Troubleshooting

### Ollama not accessible
```bash
# Make sure Ollama is running
ollama serve

# Verify it's accessible
curl http://localhost:11434/api/tags
```

### Port already in use
```bash
export LLAMA_STACK_PORT=8322
./run-ollama-stack.sh
```

### Module not found errors
```bash
./install-deps.sh
```

## 📚 Documentation

### Overview
- **[SUMMARY.md](SUMMARY.md)** - 🎯 **Start here!** Complete migration summary and success metrics

### Getting Started
- **[QUICKSTART.md](QUICKSTART.md)** - Quick reference guide for getting started
- **[CONTAINER-GUIDE.md](CONTAINER-GUIDE.md)** - Running in Docker/Podman containers

### Migration & Configuration
- **[MIGRATION-GUIDE.md](MIGRATION-GUIDE.md)** - Complete v1 to v2 migration guide with all fixes
- **[V2-FORMAT-CHANGES.md](V2-FORMAT-CHANGES.md)** - Detailed v2 format reference

### Troubleshooting
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Common errors and solutions

### Reference
- **[CHANGELOG.md](CHANGELOG.md)** - Version history and changes

### External Resources
- [Llama Stack Documentation](https://llama-stack.readthedocs.io/)
- [Ollama Documentation](https://ollama.ai/docs)
- [Available Distributions](../../llama_stack/distributions/)

## 💡 Tips

1. **First time setup**: Run `install-deps.sh` before anything else
2. **Custom models**: Edit the `registered_resources.models` section in the YAML
3. **Add providers**: Check available providers with `llama stack list-providers`
4. **Debug mode**: Set `LOG_LEVEL=DEBUG` for verbose logging

## 🔄 What Changed?

### From Old Workflow
The `llama stack build` command no longer exists. You can now:
- ✅ Run directly without a build step
- ✅ Use environment variables for configuration
- ✅ Skip the `--image-type` and `--image-name` flags

See [`README-MIGRATION.md`](./README-MIGRATION.md) for full details.

### Configuration v2 Format
The configuration file now uses v2 format with:
- ✅ Centralized storage configuration
- ✅ Backend references instead of direct database paths
- ✅ Conditional provider activation
- ✅ Proper schema validation

See [`V2-FORMAT-CHANGES.md`](./V2-FORMAT-CHANGES.md) for complete details.

## 📋 What's New in v2

1. **Centralized Storage** - All databases defined in one place
2. **Reusable Backends** - Multiple providers share the same storage
3. **Conditional Providers** - Only enable providers when API keys are set
4. **Better Validation** - Schema-compliant configuration
5. **Environment Variables** - Full support for env var substitution

## 🎯 Provider Status

### Always Enabled ✅
- Ollama (inference)
- FAISS (vector storage)
- Llama Guard (safety)
- Meta Reference (agents, eval)
- Hugging Face (datasets)
- LocalFS (datasets, files)
- Basic & LLM-as-Judge (scoring)
- RAG Runtime & MCP (tools)

### Conditionally Enabled 🔑
- OpenAI (requires `OPENAI_API_KEY`)
- Braintrust (requires `OPENAI_API_KEY`)
- Brave Search (requires `BRAVE_SEARCH_API_KEY`)
- Tavily Search (requires `TAVILY_SEARCH_API_KEY`)

