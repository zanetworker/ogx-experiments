#!/usr/bin/env python3
"""Hybrid search demo: compare vector, keyword, and hybrid search modes in OGX."""

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


def print_search_results(results, title: str):
    """Print search results in a formatted way."""
    print(f"\n{title}")
    print("-" * 60)
    print(f"Found {len(results.data)} results")
    for i, result in enumerate(results.data, 1):
        if isinstance(result.content, str):
            text = result.content
        elif isinstance(result.content, list) and len(result.content) > 0:
            text = result.content[0].text if hasattr(result.content[0], "text") else str(result.content[0])
        else:
            text = str(result.content)
        content_preview = text[:100] + "..." if len(text) > 100 else text
        print(f"\n  [{i}] Score: {result.score:.4f}")
        print(f"      Content: {content_preview}")


def main():
    port = os.environ.get("OGX_PORT", "8321")
    embedding_model = os.environ.get("EMBEDDING_MODEL", "ollama/nomic-embed-text:latest")
    embedding_dim = int(os.environ.get("EMBEDDING_DIMENSION", "768"))

    client = OpenAI(base_url=f"http://localhost:{port}/v1", api_key="unused")

    print("=" * 60)
    print("Hybrid Search Demo - OGX")
    print("=" * 60)

    # Step 1: Create a vector store
    print("\n[Step 1] Creating vector store...")
    vector_store_name = f"hybrid-search-demo-{int(time.time())}"
    vector_store = client.vector_stores.create(
        name=vector_store_name,
        extra_body={
            "embedding_model": embedding_model,
            "embedding_dimension": embedding_dim,
        },
    )
    vector_store_id = vector_store.id
    print(f"  Created vector store: {vector_store_id}")

    # Step 2: Upload sample documents
    print("\n[Step 2] Uploading documents...")
    documents = [
        {
            "name": "gpu_optimization.txt",
            "content": (
                "H100 GPU Optimization Guide\n"
                "The NVIDIA H100 GPU delivers exceptional performance for AI workloads. "
                "Key optimization techniques include tensor core utilization, memory bandwidth "
                "optimization, and efficient batch processing. The H100 features 80GB of HBM3 "
                "memory with 3.35 TB/s bandwidth, making it ideal for large language models."
            ),
        },
        {
            "name": "ml_training.txt",
            "content": (
                "Machine Learning Training Best Practices\n"
                "Training neural networks efficiently requires careful attention to hardware "
                "utilization. Modern accelerators like GPUs provide massive parallelism for "
                "matrix operations. Techniques like mixed precision training and gradient "
                "checkpointing can significantly improve training throughput and reduce memory."
            ),
        },
        {
            "name": "inference_scaling.txt",
            "content": (
                "Scaling AI Inference in Production\n"
                "Deploying AI models at scale requires balancing latency and throughput. "
                "Key considerations include batching strategies, model optimization through "
                "quantization, and efficient hardware utilization. Cloud providers offer "
                "specialized instances with GPU acceleration for inference workloads."
            ),
        },
        {
            "name": "ogx_overview.txt",
            "content": (
                "OGX Framework Overview\n"
                "OGX provides unified APIs for building AI applications. "
                "It supports multiple inference providers including Ollama, vLLM, and cloud "
                "services. The framework includes RAG capabilities with vector stores, "
                "agent tools, and safety features for production deployments."
            ),
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
        print(f"  {doc['name']}")

    print(f"\n  Vector store ready with {len(file_ids)} documents")

    # Step 3: Compare search modes
    print("\n[Step 3] Comparing search modes...")
    query = "H100 GPU optimization and performance"
    print(f'\nQuery: "{query}"')

    vector_results = client.vector_stores.search(
        vector_store_id=vector_store_id,
        query=query,
        search_mode="vector",
        max_num_results=3,
    )
    print_search_results(vector_results, "1. VECTOR SEARCH (Semantic Similarity)")

    keyword_results = client.vector_stores.search(
        vector_store_id=vector_store_id,
        query=query,
        search_mode="keyword",
        max_num_results=3,
    )
    print_search_results(keyword_results, "2. KEYWORD SEARCH (BM25 - Exact Terms)")

    hybrid_results = client.vector_stores.search(
        vector_store_id=vector_store_id,
        query=query,
        search_mode="hybrid",
        max_num_results=3,
    )
    print_search_results(hybrid_results, "3. HYBRID SEARCH (RRF Reranking)")

    # Step 4: Additional query examples
    print("\n\n[Step 4] Additional query examples...")

    semantic_query = "How do I make my AI models run faster?"
    print(f'\nSemantic Query: "{semantic_query}"')
    semantic_vector = client.vector_stores.search(
        vector_store_id=vector_store_id,
        query=semantic_query,
        search_mode="vector",
        max_num_results=2,
    )
    print_search_results(semantic_vector, "Vector Search Results")

    keyword_query = "OGX RAG"
    print(f'\nKeyword Query: "{keyword_query}"')
    keyword_exact = client.vector_stores.search(
        vector_store_id=vector_store_id,
        query=keyword_query,
        search_mode="keyword",
        max_num_results=2,
    )
    print_search_results(keyword_exact, "Keyword Search Results")

    # Cleanup
    print("\n[Cleanup] Deleting resources...")
    try:
        for file_id in file_ids:
            client.vector_stores.files.delete(
                vector_store_id=vector_store_id,
                file_id=file_id,
            )
        client.vector_stores.delete(vector_store_id=vector_store_id)
        print("  Cleaned up vector store and files")
    except Exception as e:
        print(f"  Cleanup warning: {e}")

    print("\nHybrid search demo completed!")


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
