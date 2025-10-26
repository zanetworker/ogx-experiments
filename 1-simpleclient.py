import os
from termcolor import colored
from llama_stack_client import LlamaStackClient
from llama_stack_client.types import UserMessage

def create_llama_stack_client():
    """Create Llama Stack client"""
    port = os.environ.get('LLAMA_STACK_PORT', '8321')
    base_url = f"http://localhost:{port}"
    client = LlamaStackClient(base_url=base_url)
    return client


# Create Llama Stack client
client = create_llama_stack_client()

# List available models
print(colored("--- Available models: ---", "green"))
try:
    models = client.models.list()
    # Filter for LLM models only (Ollama models)
    llm_models = [m for m in models if m.model_type == 'llm' and m.provider_id == 'ollama']
    for model in llm_models[:10]:  # Show first 10 Ollama LLM models
        print(f"- {model.identifier}")
    if len(llm_models) > 10:
        print(f"... and {len(llm_models) - 10} more Ollama LLM models")
except Exception as e:
    print(f"Error fetching models: {e}")
print()

# Example 1: Non-streaming chat completion
print(colored("--- Non-streaming Response ---", "green"))
# Use Ollama model
model_id = "ollama/llama3.2:3b-instruct-fp16"
print(f"Using model: {model_id}")

try:
    # Use the new chat.completions endpoint (OpenAI-compatible)
    response = client.chat.completions.create(
        model=model_id,
        messages=[
            {"role": "user", "content": "Write a haiku about coding"}
        ],
        stream=False
    )

    # Handle the response (OpenAI-compatible format)
    print(response.choices[0].message.content)
except Exception as e:
    print(f"Error: {e}")
print()

# Example 2: Streaming chat completion
print(colored("--- Streaming Response ---", "green"))
try:
    response_stream = client.chat.completions.create(
        model=model_id,
        messages=[
            {"role": "user", "content": "Write a different haiku about AI"}
        ],
        stream=True
    )

    print("Streaming response:")
    for chunk in response_stream:
        # OpenAI-compatible streaming format
        if chunk.choices and len(chunk.choices) > 0:
            delta = chunk.choices[0].delta
            if hasattr(delta, 'content') and delta.content:
                print(delta.content, end="", flush=True)
    print("\n")
except Exception as e:
    print(f"Error: {e}")

print(colored("✓ All examples completed successfully", "green"))