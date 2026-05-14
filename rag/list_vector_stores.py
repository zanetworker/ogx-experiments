#!/usr/bin/env python3
"""List all vector stores in OGX with detailed metadata."""

import os
import sys

from openai import OpenAI


def main():
    port = os.environ.get("OGX_PORT", "8321")
    client = OpenAI(base_url=f"http://localhost:{port}/v1", api_key="unused")

    print(f"Connected to OGX at http://localhost:{port}\n")
    print("=== Vector Stores ===")

    vector_stores = client.vector_stores.list()

    if not vector_stores.data:
        print("No vector stores found")
        return

    for vs in vector_stores.data:
        print(f"\nID: {vs.id}")
        print(f"  Name: {vs.name}")
        print(f"  Created: {vs.created_at}")
        if hasattr(vs, "file_counts") and vs.file_counts:
            print(
                f"  Files: {vs.file_counts.completed} completed, "
                f"{vs.file_counts.failed} failed, "
                f"{vs.file_counts.in_progress} in progress"
            )
        if hasattr(vs, "metadata") and vs.metadata:
            print(f"  Metadata: {vs.metadata}")


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
