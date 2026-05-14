#!/bin/bash
# Start OGX server with the dev experiments configuration.
# Supports Ollama (local), vLLM via MaaS (remote), and cloud providers via env vars.

set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REPO_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"
CONFIG_FILE="$SCRIPT_DIR/ogx-dev-run.yaml"

export OGX_PORT=${OGX_PORT:-8321}
export OLLAMA_URL=${OLLAMA_URL:-"http://localhost:11434/v1"}

echo "=== Starting OGX Server ==="
echo "Config:     $CONFIG_FILE"
echo "Port:       $OGX_PORT"
echo "Ollama:     $OLLAMA_URL"
[ -n "${VLLM_URL:-}" ]        && echo "vLLM:       $VLLM_URL"
[ -n "${OPENAI_API_KEY:-}" ]  && echo "OpenAI:     configured"
[ -n "${INFERENCE_MODEL:-}" ] && echo "Model:      $INFERENCE_MODEL"
echo "=============================="

cd "$REPO_ROOT"
exec uv run ogx run "$CONFIG_FILE"
