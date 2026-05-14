# OGX Experiments

Personal dev/test scripts exercising OGX features through the OpenAI-compatible API.

## Quick start

This repo lives inside the OGX (llama-stack) checkout at `experiments/`.

```bash
# 1. Setup OGX (once, from the llama-stack repo root)
cd /path/to/llama-stack
uv venv --python 3.12 && uv sync --group dev && uv pip install -e .

# 2. Install experiment dependencies
pip install -r experiments/requirements.txt

# 3. Activate the venv
source .venv/bin/activate

# 4. Start server with MaaS
cd experiments
source ogx-dev-setup/mint-maas-token.sh
./ogx-dev-setup/run-ogx.sh

# 5. Run a script (in another terminal, from experiments/)
source ../.venv/bin/activate
INFERENCE_MODEL=vllm/kimi-k2-6 python inference/token_tracking.py

# Or with OpenAI
INFERENCE_MODEL=openai/gpt-4o-mini python inference/structured_output.py
```

## Structure

```
experiments/
  test-demos.sh            # test runner
  requirements.txt

  inference/               # basic inference, models, embeddings, structured output
    check_models.py
    simple_inference.py
    token_tracking.py
    structured_output.py
    embeddings.py
    TOKEN_TRACKING_README.md

  rag/                     # vector stores, file search, hybrid search
    check_vector_stores.py
    list_vector_stores.py
    vector_search.py
    rag_file_search.py
    rag_hybrid_search.py
    HYBRID_SEARCH_GUIDE.md

  tools/                   # MCP, function calling
    mcp_responses.py
    mcp_streaming.py
    function_tools.py
    tools_tutorial.md

  agents/                  # multi-step, multi-agent patterns
    architectures.py
    multi_agent.py

  multi-sdk/               # Anthropic + Gemini SDK compatibility
    anthropic_messages.py
    gemini_interactions.py

  batches/                 # offline batch processing
    batch_processing.py

  ogx-dev-setup/           # server config, scripts, docs
    ogx-dev-run.yaml
    run-ogx.sh
    clean-and-restart.sh
    mint-maas-token.sh
    .env.example
    README.md
```

## Test runner

```bash
./experiments/test-demos.sh                  # run all
./experiments/test-demos.sh inference        # one category
./experiments/test-demos.sh rag/rag_file     # match pattern
./experiments/test-demos.sh --dry-run        # list only
./experiments/test-demos.sh --list           # show categories
```

## Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `OGX_PORT` | `8321` | Server port |
| `INFERENCE_MODEL` | `openai/gpt-4o-mini` | Model for experiments |
| `VLLM_URL` | (none) | vLLM/MaaS endpoint |
| `VLLM_API_TOKEN` | (none) | MaaS bearer token |
| `OPENAI_API_KEY` | (none) | OpenAI provider |

See `ogx-dev-setup/README.md` for full env var reference and MaaS setup.
