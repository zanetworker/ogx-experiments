# OGX Experiments

Runnable examples for every major [OGX](https://github.com/ogx-ai/ogx) API surface:
inference, RAG, tool calling, multi-agent orchestration, structured output,
batch processing, and multi-SDK compatibility (OpenAI, Anthropic, Google GenAI).

Each script is self-contained and talks to a local OGX server via the
OpenAI Python SDK. No OGX source checkout required.

## Prerequisites

1. A running [OGX server](https://ogx-ai.github.io/docs/getting_started/quickstart). Quickest options:

```bash
# Install OGX
uv pip install ogx[starter]

# Option A: with Ollama (local, free)
ollama serve && ollama pull llama3.2:latest
uv run ogx stack run starter

# Option B: with OpenAI
OPENAI_API_KEY=sk-... uv run ogx stack run starter

# Option C: with vLLM (self-hosted or any OpenAI-compatible endpoint)
VLLM_URL=http://your-vllm:8000/v1 uv run ogx stack run starter
```

See the [OGX quickstart](https://ogx-ai.github.io/docs/getting_started/quickstart)
and [provider docs](https://ogx-ai.github.io/docs/providers) for all options
including [vLLM](https://ogx-ai.github.io/docs/providers/inference/remote_vllm),
[Ollama](https://ogx-ai.github.io/docs/providers/inference/remote_ollama),
and [passthrough](https://ogx-ai.github.io/docs/providers/inference/remote_passthrough).

2. Install experiment dependencies:

```bash
pip install -r requirements.txt
```

## Run experiments

```bash
# Set your model (provider/model-name format)
export INFERENCE_MODEL=openai/gpt-4o-mini     # or ollama/llama3.2:latest, vllm/your-model

# Run any script
python inference/simple_inference.py
python rag/rag_file_search.py
python tools/function_tools.py
```

## Test runner

```bash
./test-demos.sh                  # run all 18 scripts
./test-demos.sh inference        # run one category
./test-demos.sh rag/rag_file     # match a pattern
./test-demos.sh --dry-run        # list what would run
./test-demos.sh --list           # show categories
```

## Structure

```
inference/          models, streaming, token tracking, structured output, embeddings
rag/                vector stores, file search, hybrid search
tools/              MCP integration, function calling
agents/             agentic architectures, multi-agent orchestration
multi-sdk/          Anthropic Messages API, Gemini Interactions API
batches/            offline batch processing
ogx-dev-setup/      custom distribution config with multi-provider setup
```

Each directory has a README listing its scripts.

## Model naming

OGX prefixes model names with the provider:

| Backend | INFERENCE_MODEL | Requires |
|---------|----------------|----------|
| OpenAI | `openai/gpt-4o-mini` | `OPENAI_API_KEY` |
| Gemini | `gemini/models/gemini-2.5-flash` | `GEMINI_API_KEY` |
| vLLM | `vllm/your-model-name` | `VLLM_URL` + `VLLM_API_TOKEN` |
| Ollama | `ollama/llama3.2:latest` | Ollama running locally |
| Passthrough | `passthrough/model-name` | `PASSTHROUGH_URL` |

All scripts read `INFERENCE_MODEL` from the environment and default to `openai/gpt-4o-mini`.

## Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `OGX_PORT` | `8321` | Server port |
| `INFERENCE_MODEL` | `openai/gpt-4o-mini` | Model for experiments |
| `OPENAI_API_KEY` | (none) | Enables OpenAI models |
| `GEMINI_API_KEY` | (none) | Enables Gemini models |
| `VLLM_URL` | (none) | vLLM endpoint |
| `VLLM_API_TOKEN` | (none) | Bearer token for vLLM auth |
| `OLLAMA_URL` | `http://localhost:11434/v1` | Ollama endpoint |

## Custom server config

The `ogx-dev-setup/` directory has a custom distribution YAML that activates
providers based on env vars, plus helper scripts for token minting and
database cleanup. See [ogx-dev-setup/README.md](ogx-dev-setup/README.md).

## Contributing

Each script should:
- Be self-contained (no shared imports between scripts)
- Follow the `main()` + `if __name__ == "__main__"` pattern
- Read config from env vars (`OGX_PORT`, `INFERENCE_MODEL`)
- Handle connection errors with a helpful message
- Work with any model that supports the required capability
