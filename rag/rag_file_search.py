#!/usr/bin/env python3
"""RAG demo: create a vector store, upload files, and query with file_search."""

import os
import sys
import time
from io import BytesIO

from openai import OpenAI


def wait_for_file_attachment(client, vector_store_id: str, file_id: str, timeout: int = 60):
    """Poll until a file is processed in the vector store."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        file_status = client.vector_stores.files.retrieve(
            vector_store_id=vector_store_id,
            file_id=file_id,
        )
        if file_status.status == "completed":
            return file_status
        if file_status.status == "failed":
            raise RuntimeError(f"File processing failed: {file_status.last_error}")
        time.sleep(0.5)
    raise TimeoutError(f"File processing timed out after {timeout}s")


def main():
    port = os.environ.get("OGX_PORT", "8321")
    embedding_model = os.environ.get("EMBEDDING_MODEL", "ollama/nomic-embed-text:latest")
    embedding_dim = int(os.environ.get("EMBEDDING_DIMENSION", "768"))
    inference_model = os.environ.get("INFERENCE_MODEL", "openai/gpt-4o-mini")

    client = OpenAI(base_url=f"http://localhost:{port}/v1", api_key="unused")
    print(f"Connected to OGX at http://localhost:{port}")

    # Step 1: Create a vector store
    print("\n[Step 1] Creating vector store...")
    vector_store_name = f"rag-demo-{int(time.time())}"
    vector_store = client.vector_stores.create(
        name=vector_store_name,
        extra_body={
            "embedding_model": embedding_model,
            "embedding_dimension": embedding_dim,
        },
    )
    print(f"  Created vector store: {vector_store.id}")

    # Step 2: Upload files and attach to vector store
    print("\n[Step 2] Uploading files...")
    documents = [
        {
            "name": "ogx_overview.txt",
            "content": (
                "OGX is a comprehensive API server for building AI applications. "
                "It provides unified APIs for inference, RAG, agents, tools, safety, and telemetry. "
                "The server supports multiple providers including Ollama, vLLM, Fireworks, Together, and more. "
                "OGX enables developers to build production-ready AI applications with ease."
            ),
        },
        {
            "name": "vector_stores.txt",
            "content": (
                "Vector stores in OGX support multiple backends including FAISS, "
                "SQLite-Vec, Milvus, Weaviate, PGVector, Qdrant, and ChromaDB. "
                "Files can be uploaded and automatically chunked and embedded. "
                "The file_search tool enables RAG queries against vector stores. "
                "Search modes include vector, keyword, and hybrid search."
            ),
        },
        {
            "name": "responses_api.txt",
            "content": (
                "The Responses API is the recommended way to interact with OGX. "
                "It supports tools like file_search for RAG, web_search, and custom functions. "
                "The API is compatible with OpenAI's format for easy migration. "
                "Streaming is supported for real-time responses."
            ),
        },
    ]

    file_ids = []
    for doc in documents:
        file_buffer = BytesIO(doc["content"].encode("utf-8"))
        file_buffer.name = doc["name"]

        file_response = client.files.create(file=file_buffer, purpose="assistants")
        file_ids.append(file_response.id)
        print(f"  Uploaded: {doc['name']} ({file_response.id})")

        client.vector_stores.files.create(
            vector_store_id=vector_store.id,
            file_id=file_response.id,
        )
        wait_for_file_attachment(client, vector_store.id, file_response.id)
        print(f"    Attached and processed")

    vs_status = client.vector_stores.retrieve(vector_store_id=vector_store.id)
    print(f"\n  Vector store ready: {vs_status.file_counts.completed} files processed")

    # Step 3: Query with RAG using Responses API
    print("\n[Step 3] Querying with RAG...")
    queries = [
        "What is OGX and what does it provide?",
        "What vector store backends are supported?",
        "How do I use the Responses API?",
    ]

    for query in queries:
        print(f"\n{'=' * 60}")
        print(f"Query: {query}")
        print("=" * 60)

        response = client.responses.create(
            model=inference_model,
            input=query,
            tools=[
                {
                    "type": "file_search",
                    "vector_store_ids": [vector_store.id],
                }
            ],
            stream=False,
        )

        for item in response.output:
            if not hasattr(item, "type"):
                continue
            if item.type == "file_search_call":
                print(f"\n[File Search] Status: {item.status}")
            elif item.type == "message":
                print("\nAssistant:")
                for content in item.content:
                    if hasattr(content, "text"):
                        print(content.text)

    # Cleanup
    print("\n[Cleanup] Deleting resources...")
    for file_id in file_ids:
        try:
            client.vector_stores.files.delete(
                vector_store_id=vector_store.id,
                file_id=file_id,
            )
        except Exception:
            pass

    try:
        client.vector_stores.delete(vector_store_id=vector_store.id)
        print("  Cleaned up vector store and files")
    except Exception as e:
        print(f"  Cleanup warning: {e}")

    print("\nRAG demo completed successfully!")


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
