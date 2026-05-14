#!/usr/bin/env python3
"""Test inference using OGX Responses API with streaming and non-streaming modes."""

import os
import sys

from openai import OpenAI


def main():
    port = os.environ.get("OGX_PORT", "8321")
    model = os.environ.get("INFERENCE_MODEL", "openai/gpt-4o-mini")
    client = OpenAI(base_url=f"http://localhost:{port}/v1", api_key="unused")

    print(f"Model: {model}\n")

    print("--- Non-streaming ---")
    response = client.responses.create(
        model=model,
        input="Explain microservices in two sentences.",
        stream=False,
    )
    for item in response.output:
        if item.type == "message":
            print(item.content[0].text)
    print()

    print("--- Streaming ---")
    stream = client.responses.create(
        model=model,
        input="What are the benefits of containerization? Be brief.",
        stream=True,
    )
    for event in stream:
        if event.type == "response.output_text.delta":
            print(event.delta, end="", flush=True)
    print("\n")


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
