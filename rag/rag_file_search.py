#!/usr/bin/env python3
"""
Simple RAG Example with OGX

This example demonstrates a basic RAG (Retrieval Augmented Generation) workflow:
1. Create a vector store
2. Upload files and attach them to the vector store
3. Query using the Responses API with file_search tool

Based on the official OGX integration tests.
"""

import os
import time
from io import BytesIO
from termcolor import cprint
from openai import OpenAI


def wait_for_file_attachment(client, vector_store_id: str, file_id: str, timeout: int = 60):
    """Wait for a file to be attached and processed in the vector store."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        file_status = client.vector_stores.files.retrieve(
            vector_store_id=vector_store_id,
            file_id=file_id,
        )
        if file_status.status == "completed":
            return file_status
        elif file_status.status == "failed":
            raise RuntimeError(f"File processing failed: {file_status.last_error}")
        time.sleep(0.5)
    raise TimeoutError(f"File processing timed out after {timeout}s")


def main():
    # Configuration from environment
    port = os.environ.get("OGX_PORT", "8321")
    embedding_model = os.environ.get("EMBEDDING_MODEL", "ollama/nomic-embed-text:latest")
    embedding_dim = int(os.environ.get("EMBEDDING_DIMENSION", "768"))
    inference_model = os.environ.get("INFERENCE_MODEL", "openai/gpt-4o-mini")

    # Initialize OGX client (OpenAI-compatible)
    client = OpenAI(base_url=f"http://localhost:{port}/v1", api_key="unused")
    cprint(f"Connected to OGX at http://localhost:{port}", "cyan")

    # =========================================================================
    # Step 1: Create a Vector Store
    # =========================================================================
    cprint("\n[Step 1] Creating vector store...", "cyan")

    vector_store_name = f"rag-demo-{int(time.time())}"
    vector_store = client.vector_stores.create(
        name=vector_store_name,
        extra_body={
            "embedding_model": embedding_model,
            "embedding_dimension": embedding_dim,
        },
    )
    cprint(f"✓ Created vector store: {vector_store.id}", "green")

    # =========================================================================
    # Step 2: Upload Files and Attach to Vector Store
    # =========================================================================
    cprint("\n[Step 2] Uploading files...", "cyan")

    # Sample documents for RAG
    documents = [
        {
            "name": "ogx_overview.txt",
            "content": """OGX is a comprehensive API server for building AI applications.
It provides unified APIs for inference, RAG, agents, tools, safety, and telemetry.
The server supports multiple providers including Ollama, vLLM, Fireworks, Together, and more.
OGX enables developers to build production-ready AI applications with ease.""",
        },
        {
            "name": "vector_stores.txt",
            "content": """Vector stores in OGX support multiple backends including FAISS,
SQLite-Vec, Milvus, Weaviate, PGVector, Qdrant, and ChromaDB.
Files can be uploaded and automatically chunked and embedded.
The file_search tool enables RAG queries against vector stores.
Search modes include vector, keyword, and hybrid search.""",
        },
        {
            "name": "responses_api.txt",
            "content": """The Responses API is the recommended way to interact with OGX.
It supports tools like file_search for RAG, web_search, and custom functions.
The API is compatible with OpenAI's format for easy migration.
Streaming is supported for real-time responses.""",
        },
    ]

    file_ids = []
    for doc in documents:
        # Upload file
        file_buffer = BytesIO(doc["content"].encode("utf-8"))
        file_buffer.name = doc["name"]

        file_response = client.files.create(
            file=file_buffer,
            purpose="assistants",
        )
        file_ids.append(file_response.id)
        cprint(f"  ✓ Uploaded: {doc['name']} ({file_response.id})", "green")

        # Attach to vector store
        client.vector_stores.files.create(
            vector_store_id=vector_store.id,
            file_id=file_response.id,
        )

        # Wait for processing
        wait_for_file_attachment(client, vector_store.id, file_response.id)
        cprint(f"    ✓ Attached and processed", "green")

    # Verify vector store status
    vs_status = client.vector_stores.retrieve(vector_store_id=vector_store.id)
    cprint(f"\n✓ Vector store ready: {vs_status.file_counts.completed} files processed", "green")

    # =========================================================================
    # Step 3: Query with RAG using Responses API
    # =========================================================================
    cprint("\n[Step 3] Querying with RAG...", "cyan")

    queries = [
        "What is OGX and what does it provide?",
        "What vector store backends are supported?",
        "How do I use the Responses API?",
    ]

    for query in queries:
        cprint(f"\n{'='*60}", "cyan")
        cprint(f"Query: {query}", "yellow")
        cprint(f"{'='*60}", "cyan")

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

        # Display results
        for item in response.output:
            if hasattr(item, "type"):
                if item.type == "file_search_call":
                    cprint(f"\n[File Search] Status: {item.status}", "blue")
                elif item.type == "message":
                    cprint("\nAssistant:", "green")
                    for content in item.content:
                        if hasattr(content, "text"):
                            print(content.text)

    # =========================================================================
    # Cleanup (optional)
    # =========================================================================
    cprint("\n[Cleanup] Deleting resources...", "cyan")

    # Delete files from vector store
    for file_id in file_ids:
        try:
            client.vector_stores.files.delete(
                vector_store_id=vector_store.id,
                file_id=file_id,
            )
        except Exception:
            pass

    # Delete vector store
    try:
        client.vector_stores.delete(vector_store_id=vector_store.id)
        cprint("✓ Cleaned up vector store and files", "green")
    except Exception as e:
        cprint(f"⚠ Cleanup warning: {e}", "yellow")

    cprint("\n✓ RAG demo completed successfully!", "green")


if __name__ == "__main__":
    main()

