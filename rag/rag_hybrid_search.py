#!/usr/bin/env python3
"""
Hybrid Search Demo with OGX

This example demonstrates the three search modes available in OGX:
1. Vector Search - Semantic similarity using embeddings
2. Keyword Search - BM25/FTS5 for exact term matching
3. Hybrid Search - Combines both with RRF reranking

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


def print_search_results(results, title: str):
    """Print search results in a formatted way."""
    cprint(f"\n{title}", "cyan")
    cprint("-" * 60, "cyan")
    print(f"Found {len(results.data)} results")
    for i, result in enumerate(results.data, 1):
        print(f"\n  [{i}] Score: {result.score:.4f}")
        # Extract text from content (can be string or list of DataContent objects)
        if isinstance(result.content, str):
            text = result.content
        elif isinstance(result.content, list) and len(result.content) > 0:
            text = result.content[0].text if hasattr(result.content[0], "text") else str(result.content[0])
        else:
            text = str(result.content)
        content_preview = text[:100] + "..." if len(text) > 100 else text
        print(f"      Content: {content_preview}")


def main():
    # Configuration from environment
    port = os.environ.get("OGX_PORT", "8321")
    embedding_model = os.environ.get("EMBEDDING_MODEL", "ollama/nomic-embed-text:latest")
    embedding_dim = int(os.environ.get("EMBEDDING_DIMENSION", "768"))

    # Initialize OGX client (OpenAI-compatible)
    client = OpenAI(base_url=f"http://localhost:{port}/v1", api_key="unused")

    cprint("=" * 60, "cyan")
    cprint("Hybrid Search Demo - OGX", "cyan")
    cprint("=" * 60, "cyan")

    # =========================================================================
    # Step 1: Create a Vector Store
    # =========================================================================
    cprint("\n[Step 1] Creating vector store...", "cyan")

    vector_store_name = f"hybrid-search-demo-{int(time.time())}"
    vector_store = client.vector_stores.create(
        name=vector_store_name,
        extra_body={
            "embedding_model": embedding_model,
            "embedding_dimension": embedding_dim,
        },
    )
    vector_store_id = vector_store.id
    cprint(f"✓ Created vector store: {vector_store_id}", "green")

    # =========================================================================
    # Step 2: Upload Sample Documents
    # =========================================================================
    cprint("\n[Step 2] Uploading documents...", "cyan")

    # Documents designed to show difference between vector and keyword search
    documents = [
        {
            "name": "gpu_optimization.txt",
            "content": """H100 GPU Optimization Guide
The NVIDIA H100 GPU delivers exceptional performance for AI workloads.
Key optimization techniques include tensor core utilization, memory bandwidth
optimization, and efficient batch processing. The H100 features 80GB of HBM3
memory with 3.35 TB/s bandwidth, making it ideal for large language models.""",
        },
        {
            "name": "ml_training.txt",
            "content": """Machine Learning Training Best Practices
Training neural networks efficiently requires careful attention to hardware
utilization. Modern accelerators like GPUs provide massive parallelism for
matrix operations. Techniques like mixed precision training and gradient
checkpointing can significantly improve training throughput and reduce memory.""",
        },
        {
            "name": "inference_scaling.txt",
            "content": """Scaling AI Inference in Production
Deploying AI models at scale requires balancing latency and throughput.
Key considerations include batching strategies, model optimization through
quantization, and efficient hardware utilization. Cloud providers offer
specialized instances with GPU acceleration for inference workloads.""",
        },
        {
            "name": "ogx_overview.txt",
            "content": """OGX Framework Overview
OGX provides unified APIs for building AI applications.
It supports multiple inference providers including Ollama, vLLM, and cloud
services. The framework includes RAG capabilities with vector stores,
agent tools, and safety features for production deployments.""",
        },
    ]

    file_ids = []
    for doc in documents:
        file_buffer = BytesIO(doc["content"].encode("utf-8"))
        file_buffer.name = doc["name"]

        file_response = client.files.create(file=file_buffer, purpose="assistants")
        file_ids.append(file_response.id)

        client.vector_stores.files.create(
            vector_store_id=vector_store_id,
            file_id=file_response.id,
        )
        wait_for_file_attachment(client, vector_store_id, file_response.id)
        cprint(f"  ✓ {doc['name']}", "green")

    cprint(f"\n✓ Vector store ready with {len(file_ids)} documents", "green")

    # =========================================================================
    # Step 3: Compare Search Modes
    # =========================================================================
    cprint("\n[Step 3] Comparing search modes...", "cyan")

    # Query that benefits from both semantic and keyword matching
    query = "H100 GPU optimization and performance"
    cprint(f"\nQuery: \"{query}\"", "yellow")

    # --- Vector Search (Semantic Similarity) ---
    vector_results = client.vector_stores.search(
        vector_store_id=vector_store_id,
        query=query,
        search_mode="vector",
        max_num_results=3,
    )
    print_search_results(vector_results, "1. VECTOR SEARCH (Semantic Similarity)")

    # --- Keyword Search (BM25/FTS5) ---
    keyword_results = client.vector_stores.search(
        vector_store_id=vector_store_id,
        query=query,
        search_mode="keyword",
        max_num_results=3,
    )
    print_search_results(keyword_results, "2. KEYWORD SEARCH (BM25 - Exact Terms)")

    # --- Hybrid Search (RRF Reranking) ---
    hybrid_results = client.vector_stores.search(
        vector_store_id=vector_store_id,
        query=query,
        search_mode="hybrid",
        max_num_results=3,
    )
    print_search_results(hybrid_results, "3. HYBRID SEARCH (RRF Reranking)")

    # =========================================================================
    # Step 4: Try Different Queries
    # =========================================================================
    cprint("\n\n[Step 4] Additional query examples...", "cyan")

    # Semantic query - should favor vector search
    semantic_query = "How do I make my AI models run faster?"
    cprint(f"\nSemantic Query: \"{semantic_query}\"", "yellow")

    semantic_vector = client.vector_stores.search(
        vector_store_id=vector_store_id,
        query=semantic_query,
        search_mode="vector",
        max_num_results=2,
    )
    print_search_results(semantic_vector, "Vector Search Results")

    # Keyword query - should favor keyword search
    keyword_query = "OGX RAG"
    cprint(f"\nKeyword Query: \"{keyword_query}\"", "yellow")

    keyword_exact = client.vector_stores.search(
        vector_store_id=vector_store_id,
        query=keyword_query,
        search_mode="keyword",
        max_num_results=2,
    )
    print_search_results(keyword_exact, "Keyword Search Results")

    # =========================================================================
    # Summary
    # =========================================================================
    cprint("\n" + "=" * 60, "cyan")
    cprint("SUMMARY: Search Modes in OGX", "cyan")
    cprint("=" * 60, "cyan")
    print()
    print("🔍 SEARCH MODES:")
    print("  • vector  - Semantic similarity using embeddings")
    print("  • keyword - Exact term matching using BM25/FTS5")
    print("  • hybrid  - Combines both with RRF reranking")
    print()
    print("💡 WHEN TO USE EACH:")
    print("  • Vector:  Concept matching, paraphrases, semantic queries")
    print("  • Keyword: Exact terms, technical jargon, specific names")
    print("  • Hybrid:  Best overall results, balanced approach")
    print()

    # =========================================================================
    # Cleanup
    # =========================================================================
    cprint("[Cleanup] Deleting resources...", "cyan")
    try:
        for file_id in file_ids:
            client.vector_stores.files.delete(
                vector_store_id=vector_store_id,
                file_id=file_id,
            )
        client.vector_stores.delete(vector_store_id=vector_store_id)
        cprint("✓ Cleaned up vector store and files", "green")
    except Exception as e:
        cprint(f"⚠ Cleanup warning: {e}", "yellow")

    cprint("\n✓ Hybrid search demo completed!", "green")


if __name__ == "__main__":
    main()

