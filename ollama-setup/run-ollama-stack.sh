#!/bin/bash
# Script to run Llama Stack with Ollama configuration

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CONFIG_FILE="$SCRIPT_DIR/ollama-stack-run.yaml"

# Check if we're in a virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Warning: You are not in a virtual environment."
    echo "   Please activate your virtual environment first:"
    echo "   source /path/to/venv/bin/activate"
    echo ""

    # Only prompt if running interactively
    if [ -t 0 ]; then
        read -p "Continue anyway? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        echo "   Running non-interactively - continuing anyway..."
    fi
fi

# Set default values if not already set
export INFERENCE_MODEL=${INFERENCE_MODEL:-"meta-llama/Llama-3.2-3B-Instruct"}
export LLAMA_STACK_PORT=${LLAMA_STACK_PORT:-8321}
export OLLAMA_URL=${OLLAMA_URL:-"http://0.0.0.0:11434"}
export LOG_LEVEL=${LOG_LEVEL:-"DEBUG"}

echo "=== Running Llama Stack with Ollama ==="
echo "Python: $(which python)"
echo "Config file: $CONFIG_FILE"
echo "INFERENCE_MODEL: $INFERENCE_MODEL"
echo "LLAMA_STACK_PORT: $LLAMA_STACK_PORT"
echo "OLLAMA_URL: $OLLAMA_URL"
echo "LOG_LEVEL: $LOG_LEVEL"
echo "========================================"

# Run the stack
exec python -m llama_stack.cli.llama stack run \
  "$CONFIG_FILE" \
  --port $LLAMA_STACK_PORT

