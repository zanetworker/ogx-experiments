#!/usr/bin/env python3
"""Track token usage from OGX Responses API."""

import os
import sys

from openai import OpenAI


def main():
    port = os.environ.get("OGX_PORT", "8321")
    model = os.environ.get("INFERENCE_MODEL", "openai/gpt-4o-mini")
    client = OpenAI(base_url=f"http://localhost:{port}/v1", api_key="unused")

    print(f"Model: {model}\n")

    response = client.responses.create(
        model=model,
        input="What is Kubernetes?",
        stream=False,
    )

    for item in response.output:
        if item.type == "message":
            print(item.content[0].text)

    if response.usage:
        input_tokens = getattr(response.usage, "input_tokens", 0)
        output_tokens = getattr(response.usage, "output_tokens", 0)
        total_tokens = getattr(response.usage, "total_tokens", input_tokens + output_tokens)
        print(f"\nInput tokens:  {input_tokens}")
        print(f"Output tokens: {output_tokens}")
        print(f"Total tokens:  {total_tokens}")
    else:
        print("\nNo usage data returned.")


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
