#!/usr/bin/env python3
"""Vector search demo against an existing OGX vector store using FAISS."""

import os
import sys

from openai import OpenAI


def main():
    port = os.environ.get("OGX_PORT", "8321")
    vector_store_id = os.environ.get("VECTOR_STORE_ID", "")
    client = OpenAI(base_url=f"http://localhost:{port}/v1", api_key="unused")

    if not vector_store_id:
        stores = list(client.vector_stores.list())
        if not stores:
            print("No vector stores found. Create one first with rag_file_search.py")
            sys.exit(1)
        vector_store_id = stores[0].id
        print(f"Using first available vector store: {vector_store_id}")

    queries = [
        "H100 GPU optimization and performance",
        "code generation models",
        "embedding models for semantic search",
        "low latency inference",
    ]

    for query_num, query in enumerate(queries, 1):
        print(f"\n{'=' * 60}")
        print(f"Query {query_num}: {query}")
        print("=" * 60)

        results = client.vector_stores.search(
            vector_store_id=vector_store_id,
            query=query,
            search_mode="vector",
            max_num_results=3,
        )

        print(f"\nFound {len(results.data)} results:\n")

        for i, result in enumerate(results.data, 1):
            print(f"[{i}] Score: {result.score:.4f}")
            print(f"    File: {result.filename}")

            content_text = ""
            if result.content:
                for content_item in result.content:
                    if hasattr(content_item, "text"):
                        content_text = content_item.text
                        break

            if content_text:
                lines = content_text.split("\n")
                preview = "\n    ".join(lines[:5])
                print(f"    Content:\n    {preview}")
                if len(lines) > 5:
                    print(f"    ... ({len(lines) - 5} more lines)")
            print()


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
