#!/bin/bash
# Mint a MaaS API token and export env vars for OGX.
# Usage:
#   source ./experiments/ogx-dev-setup/mint-maas-token.sh              # default: kimi-k2-6
#   source ./experiments/ogx-dev-setup/mint-maas-token.sh gemma4       # different model
#   source ./experiments/ogx-dev-setup/mint-maas-token.sh --list       # list available models
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

MODEL=${1:-kimi-k2-6}

# Mint token
echo "Minting MaaS token (${EXPIRY} expiry)..."
SSO_TOKEN=$(oc whoami -t)
MAAS_TOKEN=$(curl -sSk \
    -H "Authorization: Bearer ${SSO_TOKEN}" \
    -H "Content-Type: application/json" \
    -X POST -d "{\"expiration\": \"${EXPIRY}\"}" \
    "${HOST}/maas-api/v1/tokens" | jq -r .token)

if [ -z "$MAAS_TOKEN" ] || [ "$MAAS_TOKEN" = "null" ]; then
    echo "Failed to mint token. Check oc login and cluster access."
    return 1 2>/dev/null || exit 1
fi

# Export MaaS vars
export VLLM_URL="${HOST}/${NAMESPACE}/${MODEL}/v1"
export VLLM_API_TOKEN="$MAAS_TOKEN"
export INFERENCE_MODEL="vllm/${MODEL}"

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
echo "MaaS:   ${MAAS_TOKEN:0:20}..."
echo "Model:  ${MODEL}"
echo "URL:    ${VLLM_URL}"
[ -n "${OPENAI_API_KEY:-}" ]  && echo "OpenAI: configured"
[ -n "${GEMINI_API_KEY:-}" ]  && echo "Gemini: configured"
echo ""
echo "Exported: VLLM_URL, VLLM_API_TOKEN, INFERENCE_MODEL"
echo "Now run:  ./experiments/ogx-dev-setup/run-ogx.sh"
