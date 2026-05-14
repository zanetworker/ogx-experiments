#!/usr/bin/env python3
"""Test embedding functionality with OGX."""

import os
import sys

from openai import OpenAI


def main():
    port = os.environ.get("OGX_PORT", "8321")
    model = os.environ.get("INFERENCE_MODEL", "openai/gpt-4o-mini")
    embedding_model = os.environ.get("EMBEDDING_MODEL", "openai/text-embedding-3-small")
    client = OpenAI(base_url=f"http://localhost:{port}/v1", api_key="unused")

    print(f"Server: http://localhost:{port}/v1")
    print(f"Inference model: {model}")
    print(f"Embedding model: {embedding_model}\n")

    print("Available Models:")
    print("-" * 40)
    models = client.models.list()
    for m in models.data:
        print(f"  {m.id}")

    print(f"\nTesting Embedding ({embedding_model}):")
    print("-" * 40)
    response = client.embeddings.create(
        model=embedding_model,
        input="This is a test sentence",
    )
    embedding = response.data[0].embedding
    print(f"  Dimension: {len(embedding)}")
    print(f"  First 5 values: {embedding[:5]}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        if "Connection" in type(e).__name__ or "connection" in str(e).lower():
            port = os.environ.get("OGX_PORT", "8321")
            print(f"Failed to connect to OGX at http://localhost:{port}.", file=sys.stderr)
            print("Start the server with: ogx run <config>.yaml", file=sys.stderr)
        else:
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(130)
