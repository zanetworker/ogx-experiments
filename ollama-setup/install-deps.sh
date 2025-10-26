#!/bin/bash
# Script to install dependencies for Llama Stack with Ollama

echo "=== Installing Llama Stack Dependencies ==="
echo "This will install all required packages for the starter distribution"
echo "which includes support for Ollama, FAISS, Llama Guard, and more."
echo ""

# Check if we're in a virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Warning: You are not in a virtual environment."
    echo "   It's recommended to create and activate a virtual environment first:"
    echo "   python -m venv venv"
    echo "   source venv/bin/activate"
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Install dependencies
echo "Fetching dependency list..."
DEPS=$(python -m llama_stack.cli.llama stack list-deps starter 2>/dev/null)

if [ $? -ne 0 ]; then
    echo "❌ Failed to get dependency list. Make sure llama-stack is installed:"
    echo "   pip install llama-stack"
    exit 1
fi

if [ -z "$DEPS" ]; then
    echo "✅ No additional dependencies needed!"
    exit 0
fi

echo "Installing dependencies:"
echo "$DEPS"
echo ""

# Install each dependency
echo "$DEPS" | xargs -L1 pip install

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Dependencies installed successfully!"
    echo ""
    echo "You can now run the stack with:"
    echo "  ./experiments/run-ollama-stack.sh"
else
    echo ""
    echo "❌ Failed to install some dependencies."
    echo "   Please check the error messages above."
    exit 1
fi

