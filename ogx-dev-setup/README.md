# OGX Dev Setup

Custom distribution config for running OGX with multiple inference backends:
Ollama (local), vLLM/MaaS (remote cluster), and cloud providers (OpenAI, Gemini).

Use this instead of the built-in `starter` distribution when you need a
tailored provider set, MaaS token auth, or a persistent local config.

## Files

| File | Purpose |
|------|---------|
| `ogx-dev-run.yaml` | Distribution config (Ollama + vLLM + OpenAI + Gemini + embeddings + RAG + search tools) |
| `run-ogx.sh` | Start the OGX server with this config |
| `clean-and-restart.sh` | Wipe databases and restart (fixes schema migration errors) |
| `mint-maas-token.sh` | Mint a MaaS API token and export vLLM env vars (must be sourced) |
| `.env.example` | Template for API keys (copy to `.env`, which is gitignored) |

## Prerequisites

- Python 3.12
- [uv](https://docs.astral.sh/uv/) package manager
- OGX installed in editable mode (see the root [README](../README.md))

## Quick Start

### Option A: Cloud providers only (OpenAI, Gemini)

```bash
cp .env.example .env
# Edit .env: add your OPENAI_API_KEY, GEMINI_API_KEY, etc.

./run-ogx.sh
```

### Option B: Local inference with Ollama

```bash
ollama serve                      # in another terminal
ollama pull llama3.2:latest       # pull a model

./run-ogx.sh
```

Ollama is always enabled. Models are auto-discovered.

### Option C: vLLM via MaaS gateway (Red Hat internal)

```bash
# Login to the OpenShift cluster
oclogingpu

# List available models on the cluster
source mint-maas-token.sh --list

# Mint a token for a specific model (default: kimi-k2-6)
source mint-maas-token.sh
source mint-maas-token.sh gemma4       # or pick a different model

# Start the server (clean DBs on first run or after model switch)
./clean-and-restart.sh
```

The script must be **sourced** (not executed) so the env vars persist in your shell.

`oc whoami -t` does NOT work for MaaS inference. The script mints a
dedicated API token via `/maas-api/v1/tokens` (72h expiry by default).

## Verify

```bash
# Health check
curl http://localhost:8321/v1/health

# List registered models
curl -s http://localhost:8321/v1/models | python3 -c "
import sys, json
for m in json.load(sys.stdin)['data']:
    print(m['id'])
" | head -20

# Test chat completion (substitute your model)
curl http://localhost:8321/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai/gpt-4o-mini",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 50
  }'
```

## Switching Models and Providers

OGX prefixes model names with the provider. The prefix determines which
backend handles the request:

| Backend | INFERENCE_MODEL | Requires |
|---------|----------------|----------|
| OpenAI | `openai/gpt-4o-mini` | `OPENAI_API_KEY` |
| Gemini | `gemini/models/gemini-2.5-flash` | `GEMINI_API_KEY` |
| vLLM/MaaS | `vllm/kimi-k2-6` | `VLLM_URL` + `VLLM_API_TOKEN` |
| Ollama | `ollama/llama3.2:latest` | Ollama running locally |

Switch between providers by changing `INFERENCE_MODEL`. No server restart needed:

```bash
INFERENCE_MODEL=openai/gpt-4o-mini python ../inference/structured_output.py
INFERENCE_MODEL=vllm/kimi-k2-6 python ../inference/structured_output.py
INFERENCE_MODEL=ollama/llama3.2:latest python ../inference/token_tracking.py
```

### How provider activation works

The config uses conditional provider IDs. A provider only registers when its
env var is set and non-empty:

```yaml
- provider_id: ${env.VLLM_URL:+vllm}          # skipped if VLLM_URL is empty
- provider_id: ${env.OPENAI_API_KEY:+openai}   # skipped if no API key
- provider_id: ollama                           # always active (has default URL)
```

### Using multiple providers at once

All active providers coexist. You can route different requests to different
backends in the same session:

```python
from openai import OpenAI
client = OpenAI(base_url="http://localhost:8321/v1", api_key="unused")

r1 = client.chat.completions.create(model="openai/gpt-4o-mini", messages=[...])
r2 = client.chat.completions.create(model="ollama/llama3.2:latest", messages=[...])
```

### Switching MaaS models

MaaS uses path-based routing: each model has its own URL path. The
`mint-maas-token.sh` script sets `VLLM_URL` to the correct path:

```bash
source mint-maas-token.sh kimi-k2-6    # VLLM_URL=.../kimi-k2-6/v1
source mint-maas-token.sh gemma4        # VLLM_URL=.../gemma4/v1
./clean-and-restart.sh                  # clean cached model from DB
```

Only one vLLM model is available at a time with this setup. For multiple
vLLM models, configure one provider per model in the YAML or use the
`remote::passthrough` provider.

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `OGX_PORT` | `8321` | Server port |
| `OLLAMA_URL` | `http://localhost:11434/v1` | Ollama endpoint |
| `VLLM_URL` | (none) | vLLM/MaaS endpoint. Activates provider when set. |
| `VLLM_API_TOKEN` | `fake` | Bearer token for vLLM/MaaS auth |
| `VLLM_MAX_TOKENS` | `4096` | Max output tokens for vLLM |
| `VLLM_TLS_VERIFY` | `true` | TLS verification for vLLM endpoint |
| `OPENAI_API_KEY` | (none) | Activates OpenAI provider |
| `GEMINI_API_KEY` | (none) | Activates Gemini provider |
| `BRAVE_SEARCH_API_KEY` | (none) | Activates Brave web search tool |
| `TAVILY_SEARCH_API_KEY` | (none) | Activates Tavily web search tool |
| `INFERENCE_MODEL` | (none) | Default model for experiment scripts |
| `FILES_STORAGE_DIR` | `~/.ogx/.../files` | File storage directory |
| `SQLITE_STORE_DIR` | `~/.ogx/.../` | SQLite database directory |

## APIs

| Endpoint | SDK | What it does |
|----------|-----|-------------|
| `POST /v1/chat/completions` | OpenAI | Standard chat (any OpenAI-compatible client) |
| `POST /v1/responses` | OpenAI | Agentic orchestration: tool calling, MCP, file search |
| `POST /v1/embeddings` | OpenAI | Text embeddings |
| `GET /v1/models` | OpenAI | List registered models |
| `POST /v1/files` | OpenAI | Upload files for RAG |
| `POST /v1/vector_stores` | OpenAI | Document storage and search |
| `POST /v1/batches` | OpenAI | Offline batch processing |
| `POST /v1/messages` | Anthropic | Anthropic Messages API compatibility |
| `POST /v1alpha/interactions` | Google GenAI | Gemini Interactions API compatibility |
| `GET /v1/health` | curl | Server health check |

## MaaS Models (Red Hat Internal)

Available on the TMM GPU cluster in the `prelude-maas` namespace:

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

Run `source mint-maas-token.sh --list` for the current list.

## Troubleshooting

**Port already in use:**
```bash
lsof -ti :8321 | xargs kill -9
```

**Schema migration errors (stale DBs):**
```bash
./clean-and-restart.sh
```

**vLLM model not appearing in /v1/models:**
```bash
curl -sk "${VLLM_URL}/models" -H "Authorization: Bearer ${VLLM_API_TOKEN}"
```

**MaaS token expired (401):**
Re-source `mint-maas-token.sh` to mint a new one.

**Python version mismatch:**
OGX requires 3.12. The `.venv` from `uv venv --python 3.12` is independent of pyenv.
