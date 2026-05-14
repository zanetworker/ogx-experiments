#!/usr/bin/env python3
"""Check existing vector stores in OGX."""

import os
import sys

from openai import OpenAI


def main():
    port = os.environ.get("OGX_PORT", "8321")
    client = OpenAI(base_url=f"http://localhost:{port}/v1", api_key="unused")

    print("Existing vector stores:")
    stores = list(client.vector_stores.list())
    if stores:
        for store in stores:
            print(f"  - ID: {store.id}, Name: {store.name}")
    else:
        print("  (none found)")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as e:
        if "Connection" in type(e).__name__ or "connection" in str(e).lower():
            port = os.environ.get("OGX_PORT", "8321")
            print(f"Error: Cannot connect to OGX at http://localhost:{port}")
            print("Make sure the server is running: uv run ogx run <config>")
            sys.exit(1)
        raise
