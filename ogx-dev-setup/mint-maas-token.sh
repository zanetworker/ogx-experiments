#!/bin/bash
# Mint a MaaS API token and export env vars for OGX.
# Usage:
#   source ./experiments/ogx-dev-setup/mint-maas-token.sh              # mint token, all models activated
#   source ./experiments/ogx-dev-setup/mint-maas-token.sh --list       # list available models
#   source ./experiments/ogx-dev-setup/mint-maas-token.sh --model kimi-k2-6  # set default INFERENCE_MODEL
#
# Must be sourced (not executed) so exports persist in your shell.

set -euo pipefail

HOST=https://maas.apps.ocp.cloud.rhai-tmm.dev
NAMESPACE=prelude-maas
EXPIRY=${MAAS_TOKEN_EXPIRY:-72h}

# Check oc login
if ! oc whoami &>/dev/null; then
    echo "Not logged in. Run: oclogingpu"
    return 1 2>/dev/null || exit 1
fi

# List mode
if [ "${1:-}" = "--list" ] || [ "${1:-}" = "-l" ]; then
    echo "Available models in ${NAMESPACE}:"
    oc get llminferenceservices -n "$NAMESPACE" \
        -o custom-columns="NAME:.metadata.name,MODEL:.spec.model.name,READY:.status.conditions[0].status" \
        --no-headers 2>/dev/null | while read -r name model ready; do
        if [ "$ready" = "True" ]; then
            echo "  $model"
        else
            echo "  $model  (not ready)"
        fi
    done
    return 0 2>/dev/null || exit 0
fi

# Parse --model flag
DEFAULT_MODEL="kimi-k2-6"
while [[ $# -gt 0 ]]; do
    case "$1" in
        --model|-m) DEFAULT_MODEL="$2"; shift 2 ;;
        *) DEFAULT_MODEL="$1"; shift ;;
    esac
done

# Mint token
echo "Minting MaaS token (${EXPIRY} expiry)..."
SSO_TOKEN=$(oc whoami -t)
TOKEN=$(curl -sSk \
    -H "Authorization: Bearer ${SSO_TOKEN}" \
    -H "Content-Type: application/json" \
    -X POST -d "{\"expiration\": \"${EXPIRY}\"}" \
    "${HOST}/maas-api/v1/tokens" | jq -r .token)

if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
    echo "Failed to mint token. Check oc login and cluster access."
    return 1 2>/dev/null || exit 1
fi

# Export shared token (activates all MaaS providers in ogx-dev-run.yaml)
export MAAS_TOKEN="$TOKEN"
export MAAS_HOST="$HOST"
export INFERENCE_MODEL="${DEFAULT_MODEL}"

# Also set VLLM vars for the generic vllm provider (backward compat)
export VLLM_API_TOKEN="$TOKEN"

# Load .env if it exists (for OPENAI_API_KEY, GEMINI_API_KEY, etc.)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ENV_FILE="${SCRIPT_DIR}/.env"
if [ -f "$ENV_FILE" ]; then
    set -a
    source "$ENV_FILE"
    set +a
    echo "Loaded:  ${ENV_FILE}"
fi

echo ""
echo "Token:  ${TOKEN:0:20}..."
echo "Models: kimi, gemma, scout, nemotron, qwen (all activated)"
echo "Default: INFERENCE_MODEL=${INFERENCE_MODEL}"
[ -n "${OPENAI_API_KEY:-}" ]  && echo "OpenAI: configured"
[ -n "${GEMINI_API_KEY:-}" ]  && echo "Gemini: configured"
echo ""
echo "Use any model:  INFERENCE_MODEL=kimi/kimi-k2-6 python ..."
echo "                INFERENCE_MODEL=gemma/gemma4 python ..."
echo "                INFERENCE_MODEL=scout/llama-4-scout-17b-16e-w4a16 python ..."
echo ""
echo "Now run:  ./ogx-dev-setup/run-ogx.sh"
