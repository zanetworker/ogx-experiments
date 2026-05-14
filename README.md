# OGX Experiments

Runnable examples for every major OGX API surface: inference, RAG, tool calling,
multi-agent orchestration, structured output, batch processing, and multi-SDK
compatibility (OpenAI, Anthropic, Google GenAI).

Each script is self-contained, uses the OpenAI Python SDK, and talks to a
local OGX server. No framework dependencies beyond `openai` and the standard library.

## Prerequisites

1. Clone [OGX](https://github.com/ogx-ai/ogx) and set up the dev environment:

```bash
git clone https://github.com/ogx-ai/ogx.git
cd ogx
uv venv --python 3.12
uv sync --group dev
uv pip install -e .
```

2. Clone this repo into the OGX checkout:

```bash
git clone https://github.com/zanetworker/ogx-experiments.git experiments
```

3. Install experiment dependencies:

```bash
uv pip install -r experiments/requirements.txt
```

## Start the server

You need a running OGX server. Pick whichever backend you have access to:

### Option A: OpenAI (easiest, needs an API key)

```bash
export OPENAI_API_KEY="sk-..."
uv run ogx stack run starter
```

### Option B: Ollama (local, free, no API key)

```bash
ollama serve                      # start Ollama in another terminal
ollama pull llama3.2:latest       # pull a model
uv run ogx stack run starter
```

### Option C: Custom config with MaaS/vLLM (Red Hat internal)

```bash
cd experiments
source ogx-dev-setup/mint-maas-token.sh          # mint token, set env vars
./ogx-dev-setup/run-ogx.sh                       # start with custom config
```

See [ogx-dev-setup/README.md](ogx-dev-setup/README.md) for MaaS setup,
token minting, provider configuration, and model switching.

## Run experiments

```bash
source .venv/bin/activate

# Set your model (provider/model-name format)
export INFERENCE_MODEL=openai/gpt-4o-mini     # or vllm/kimi-k2-6, ollama/llama3.2:latest

# Run any script
python experiments/inference/simple_inference.py
python experiments/rag/rag_file_search.py
python experiments/tools/function_tools.py
```

## Test runner

```bash
cd experiments

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
ogx-dev-setup/      server config, run scripts, MaaS token minting
```

Each directory has a README listing its scripts.

## Model naming

OGX prefixes model names with the provider:

| Backend | INFERENCE_MODEL | Needs |
|---------|----------------|-------|
| OpenAI | `openai/gpt-4o-mini` | `OPENAI_API_KEY` |
| OpenAI | `openai/gpt-4.1-nano` | `OPENAI_API_KEY` |
| Gemini | `gemini/models/gemini-2.5-flash` | `GEMINI_API_KEY` |
| vLLM/MaaS | `vllm/kimi-k2-6` | `VLLM_URL` + `VLLM_API_TOKEN` |
| Ollama | `ollama/llama3.2:latest` | Ollama running locally |

All experiment scripts read `INFERENCE_MODEL` from the environment and default
to `openai/gpt-4o-mini`.

## Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `OGX_PORT` | `8321` | Server port |
| `INFERENCE_MODEL` | `openai/gpt-4o-mini` | Model for experiments |
| `OPENAI_API_KEY` | (none) | Enables OpenAI models |
| `GEMINI_API_KEY` | (none) | Enables Gemini models |
| `VLLM_URL` | (none) | vLLM/MaaS endpoint |
| `VLLM_API_TOKEN` | (none) | Bearer token for vLLM/MaaS |
| `OLLAMA_URL` | `http://localhost:11434/v1` | Ollama endpoint |

## Contributing

Each script should:
- Be self-contained (no shared imports between scripts)
- Follow the `main()` + `if __name__ == "__main__"` pattern
- Read config from env vars (`OGX_PORT`, `INFERENCE_MODEL`)
- Handle connection errors with a helpful message
- Work with any model that supports the required capability
