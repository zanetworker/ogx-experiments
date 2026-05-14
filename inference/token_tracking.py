#!/usr/bin/env python3
import os
from openai import OpenAI

port = os.environ.get('OGX_PORT', '8321')
model = os.environ.get('INFERENCE_MODEL', 'ollama/llama3.2:latest')  # Configurable via INFERENCE_MODEL env var

client = OpenAI(
    base_url=f"http://localhost:{port}/v1",
    api_key="not-needed"
)

response = client.responses.create(
    model=model,
    input="What is Kubernetes?",
    stream=False
)

for item in response.output:
    if item.type == "message":
        print(item.content[0].text)

if response.usage:
    input_tokens = getattr(response.usage, 'input_tokens', 0)
    output_tokens = getattr(response.usage, 'output_tokens', 0)
    total_tokens = getattr(response.usage, 'total_tokens', input_tokens + output_tokens)

    print(f"\nInput tokens:  {input_tokens}")
    print(f"Output tokens: {output_tokens}")
    print(f"Total tokens:  {total_tokens}")

