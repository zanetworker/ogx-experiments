# OGX Dev Setup

Personal dev configuration for running OGX with Ollama, MaaS (vLLM), and cloud providers.

Last updated: 2026-05-13

## Files

| File | Purpose |
|------|---------|
| `ogx-dev-run.yaml` | Distribution config (Ollama + vLLM + OpenAI + Gemini + search tools + RAG) |
| `run-ogx.sh` | Start the OGX server |
| `clean-and-restart.sh` | Wipe databases and restart (for schema migration issues) |
| `mint-maas-token.sh` | Mint a MaaS API token and export VLLM env vars (must be sourced) |

## Prerequisites

- Python 3.12 (required by OGX pre-commit hooks)
- [uv](https://docs.astral.sh/uv/) package manager
- Ollama running locally (optional, for local models)

One-time setup from the repo root:

```bash
uv venv --python 3.12
uv sync --group dev
uv pip install -e .
```

## Quick Start

### Local only (Ollama)

```bash
ollama serve  # in another terminal, if not already running

./experiments/ogx-dev-setup/run-ogx.sh
```

### With MaaS (TMM cluster vLLM models)

```bash
# Login to the cluster
oclogingpu

# List available models
source ./experiments/ogx-dev-setup/mint-maas-token.sh --list

# Mint token and export env vars (default: kimi-k2-6)
source ./experiments/ogx-dev-setup/mint-maas-token.sh

# Or for a different model:
source ./experiments/ogx-dev-setup/mint-maas-token.sh gemma4

# Clean stale DBs (needed after switching models or first run)
./experiments/ogx-dev-setup/clean-and-restart.sh

# Or start without cleaning
./experiments/ogx-dev-setup/run-ogx.sh
```

Note: `oc whoami -t` does NOT work for inference. The script mints a token via `/maas-api/v1/tokens`.
Must be **sourced** (not executed) so env vars persist in your shell.

### With cloud providers

```bash
export OPENAI_API_KEY="sk-..."      # enables OpenAI models
export GEMINI_API_KEY="..."         # enables Gemini models
export ANTHROPIC_API_KEY="..."      # enables Anthropic models

./experiments/ogx-dev-setup/run-ogx.sh
```

Providers only activate when their env var is set. No API key = provider is skipped silently.

## Verify

```bash
# Health check
curl http://localhost:8321/v1/health

# List models (OpenAI-compatible)
curl http://localhost:8321/v1/models | python3 -m json.tool

# Test chat completion
curl http://localhost:8321/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "vllm/kimi-k2-6",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 50
  }'

# Test with the Responses API
curl http://localhost:8321/v1/responses \
  -H "Content-Type: application/json" \
  -d '{
    "model": "vllm/kimi-k2-6",
    "input": "Explain containers in one sentence"
  }'
```

Or from Python:

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8321/v1", api_key="unused")
response = client.chat.completions.create(
    model="vllm/kimi-k2-6",
    messages=[{"role": "user", "content": "Hello"}],
)
print(response.choices[0].message.content)
```

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `OGX_PORT` | `8321` | Server port |
| `OLLAMA_URL` | `http://localhost:11434/v1` | Ollama endpoint |
| `VLLM_URL` | (none) | vLLM/MaaS endpoint. Provider activates only when set. |
| `VLLM_API_TOKEN` | `fake` | Bearer token for vLLM/MaaS auth |
| `VLLM_MAX_TOKENS` | `4096` | Max output tokens for vLLM |
| `VLLM_TLS_VERIFY` | `true` | TLS verification for vLLM endpoint |
| `OPENAI_API_KEY` | (none) | OpenAI provider. Activates when set. |
| `GEMINI_API_KEY` | (none) | Gemini provider. Activates when set. |
| `ANTHROPIC_API_KEY` | (none) | Anthropic provider (not in this config but available in starter). |
| `BRAVE_SEARCH_API_KEY` | (none) | Brave web search tool |
| `TAVILY_SEARCH_API_KEY` | (none) | Tavily web search tool |
| `INFERENCE_MODEL` | (none) | Default model for experiment scripts |
| `FILES_STORAGE_DIR` | `~/.ogx/.../files` | File storage directory |
| `SQLITE_STORE_DIR` | `~/.ogx/.../` | Database directory |

## APIs Available

| API | Endpoint | What it does |
|-----|----------|-------------|
| Chat Completions | `POST /v1/chat/completions` | Standard OpenAI chat (any client) |
| Responses | `POST /v1/responses` | Agentic orchestration: tool calling, MCP, file search |
| Embeddings | `POST /v1/embeddings` | Text embeddings (via Ollama or sentence-transformers) |
| Models | `GET /v1/models` | List registered models |
| Files | `POST /v1/files` | Upload files for RAG |
| Vector Stores | `POST /v1/vector_stores` | Managed document storage and search |
| Batches | `POST /v1/batches` | Offline batch processing |
| Messages | `POST /v1/messages` | Anthropic SDK compatibility |
| Interactions | `POST /v1alpha/interactions` | Gemini SDK compatibility |
| Health | `GET /v1/health` | Server health check |

## Switching Models and Providers

OGX registers models with a `{provider}/{model}` naming convention. The provider prefix
tells OGX which backend to route the request to.

### Model naming by provider

| Provider | INFERENCE_MODEL example | What happens |
|----------|------------------------|-------------|
| OpenAI | `openai/gpt-4o-mini` | OGX forwards to OpenAI API (needs `OPENAI_API_KEY`) |
| OpenAI | `openai/gpt-4.1-nano` | Cheapest/fastest OpenAI model |
| Gemini | `gemini/models/gemini-2.5-flash` | OGX forwards to Google (needs `GEMINI_API_KEY`) |
| vLLM/MaaS | `vllm/kimi-k2-6` | OGX forwards to `VLLM_URL` with `VLLM_API_TOKEN` |
| Ollama | `ollama/llama3.2:latest` | OGX forwards to local Ollama |

### How to switch

Just change the `INFERENCE_MODEL` env var. The server doesn't need to restart:

```bash
# Use OpenAI
INFERENCE_MODEL=openai/gpt-4o-mini python inference/structured_output.py

# Use MaaS (must have sourced mint-maas-token.sh first)
INFERENCE_MODEL=vllm/kimi-k2-6 python inference/structured_output.py

# Use Ollama (must have ollama running with the model pulled)
INFERENCE_MODEL=ollama/llama3.2:latest python inference/token_tracking.py
```

### How provider activation works in the config

The `ogx-dev-run.yaml` uses conditional provider IDs. A provider only activates
when its env var is set and non-empty:

```yaml
# This provider only registers if VLLM_URL is set:
- provider_id: ${env.VLLM_URL:+vllm}     # empty VLLM_URL = provider skipped

# This provider only registers if OPENAI_API_KEY is set:
- provider_id: ${env.OPENAI_API_KEY:+openai}

# Ollama always registers (has a default URL):
- provider_id: ollama
```

To see which models are registered after startup:

```bash
curl -s http://localhost:8321/v1/models | python3 -c "
import sys, json
for m in json.load(sys.stdin)['data']:
    print(m['id'])
" | head -20
```

### Switching MaaS models

MaaS uses path-based routing, so each model needs a different `VLLM_URL`.
The `mint-maas-token.sh` script handles this:

```bash
source mint-maas-token.sh kimi-k2-6    # sets VLLM_URL to .../kimi-k2-6/v1
source mint-maas-token.sh gemma4        # sets VLLM_URL to .../gemma4/v1
```

After switching, clean the DB (the old model is cached) and restart:

```bash
./clean-and-restart.sh
```

### Using multiple providers simultaneously

All providers with set env vars are active at the same time. You can use
different models in the same session without restarting:

```python
from openai import OpenAI
client = OpenAI(base_url="http://localhost:8321/v1", api_key="unused")

# One request to OpenAI
r1 = client.chat.completions.create(model="openai/gpt-4o-mini", messages=[...])

# Next request to MaaS/vLLM
r2 = client.chat.completions.create(model="vllm/kimi-k2-6", messages=[...])
```

The limitation is that only one vLLM model is available at a time (since
`VLLM_URL` points to one model's path). For multiple vLLM models simultaneously,
you'd need multiple providers in the config (one per model) or use the
`remote::passthrough` provider with BDR routing.

## MaaS Models on TMM Cluster

Available models in `prelude-maas` namespace (as of 2026-05-13):

| Model | model_name | Type |
|-------|-----------|------|
| Kimi K2.6 | `kimi-k2-6` | LLM |
| Gemma 4 | `gemma4` | LLM |
| Llama 4 Scout | `llama-4-scout-17b-16e-w4a16` | LLM |
| Nemotron Cascade 2 | `nemotron-cascade-2-30b` | LLM |
| Qwen 3.5 9B | `qwen35-9b` | LLM |
| Llama 3.2 3B | `llama-32-3b` | LLM |
| Granite Vision | `granite-vision-32-2b` | Vision |
| Qwen 2.5 VL | `qwen25-vl-7b-instruct-fp8` | Vision |

To use a different model, change the `VLLM_URL` path:

```bash
export VLLM_URL="https://maas.apps.ocp.cloud.rhai-tmm.dev/prelude-maas/gemma4/v1"
```

Each model needs its own `base_url` because MaaS uses path-based routing.

## Troubleshooting

**Port already in use:**
```bash
lsof -ti :8321 | xargs kill -9
```

**Schema migration errors (stale DBs):**
```bash
./experiments/ogx-dev-setup/clean-and-restart.sh
```

**vLLM model not appearing in /v1/models:**
The vLLM provider auto-discovers models from the remote endpoint. If the model isn't listed, verify:
```bash
curl -sk "${VLLM_URL}/models" -H "Authorization: Bearer ${VLLM_API_TOKEN}"
```

**MaaS token expired (401):**
Re-mint via the token endpoint. Tokens last 72h by default.

**Python version mismatch:**
OGX requires Python 3.12. Check with `python3.12 --version`. The `.venv` created by `uv venv --python 3.12` is independent of pyenv.
