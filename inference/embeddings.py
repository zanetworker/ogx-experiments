#!/usr/bin/env python3
"""Test embedding functionality with OGX"""
import os
from openai import OpenAI

# Initialize OpenAI client for OGX
port = os.environ.get('OGX_PORT', '8321')
client = OpenAI(
    base_url=f"http://localhost:{port}/v1",
    api_key="not-needed"
)

print(f"Connected to OGX at http://localhost:{port}")

# List available models
print("\n=== Available Models ===")
try:
    models = client.models.list()
    for model in models.data:
        print(f"  - {model.id} (type: {getattr(model, 'model_type', 'unknown')})")
except Exception as e:
    print(f"Error listing models: {e}")

# Test embedding
print("\n=== Testing Embedding ===")
embedding_model = "ollama/nomic-embed-text:latest"  # Configurable: any embedding model registered with OGX
print(f"Using model: {embedding_model}")

try:
    response = client.embeddings.create(
        model=embedding_model,
        input="This is a test sentence"
    )
    print(f"✓ Embedding successful!")
    print(f"  Dimension: {len(response.data[0].embedding)}")
    print(f"  First 5 values: {response.data[0].embedding[:5]}")
except Exception as e:
    print(f"✗ Embedding failed: {e}")
    import traceback
    traceback.print_exc()

