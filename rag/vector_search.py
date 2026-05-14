#!/usr/bin/env python3
"""
Vector Search Demo with FAISS in OGX

Note: FAISS only supports vector search (semantic similarity).
For hybrid search (vector + keyword), use SQLite-Vec, Milvus, or Weaviate instead.
"""
import os
from openai import OpenAI
from termcolor import cprint

# Initialize OGX client (OpenAI-compatible)
port = os.environ.get('OGX_PORT', '8321')
client = OpenAI(base_url=f"http://localhost:{port}/v1", api_key="unused")

# Use the RedHat AI models vector store
vector_store_id = "vs_38624989-3407-43ce-a2b3-d5d1ae71442d"

cprint("=" * 80, "cyan")
cprint("Vector Search Demo - FAISS Provider", "cyan")
cprint("=" * 80, "cyan")
print()
cprint("Note: FAISS only supports VECTOR search (semantic similarity)", "yellow")
cprint("For HYBRID search, see HYBRID_SEARCH_GUIDE.md", "yellow")
print()

# Test queries
queries = [
    "H100 GPU optimization and performance",
    "code generation models",
    "embedding models for semantic search",
    "low latency inference",
]

for query_num, query in enumerate(queries, 1):
    cprint(f"\n{'=' * 80}", "cyan")
    cprint(f"Query {query_num}: {query}", "cyan")
    cprint("=" * 80, "cyan")
    
    # Vector search
    results = client.vector_stores.search(
        vector_store_id=vector_store_id,
        query=query,
        search_mode="vector",  # Only mode supported by FAISS
        max_num_results=3,
    )
    
    print(f"\nFound {len(results.data)} results:\n")
    
    for i, result in enumerate(results.data, 1):
        print(f"[{i}] Score: {result.score:.4f}")
        print(f"    File: {result.filename}")
        
        # Extract content text
        content_text = ""
        if result.content:
            for content_item in result.content:
                if hasattr(content_item, 'text'):
                    content_text = content_item.text
                    break
        
        # Show first 200 characters
        if content_text:
            lines = content_text.split('\n')
            # Show first few lines
            preview = '\n    '.join(lines[:5])
            print(f"    Content:\n    {preview}")
            if len(lines) > 5:
                print(f"    ... ({len(lines) - 5} more lines)")
        print()

# Summary
cprint("=" * 80, "cyan")
cprint("How Vector Search Works", "cyan")
cprint("=" * 80, "cyan")
print()
print("1. Query Embedding:")
print("   Your query is converted to a 768-dimensional vector using")
print("   the embedding model (ollama/nomic-embed-text:latest)")
print()
print("2. Similarity Search:")
print("   FAISS compares your query vector with all document vectors")
print("   using cosine similarity or L2 distance")
print()
print("3. Ranking:")
print("   Results are ranked by similarity score (higher = more similar)")
print()
print("4. Semantic Understanding:")
print("   Vector search finds conceptually similar content even if")
print("   the exact words don't match")
print()
print("Examples:")
print("  • 'H100 optimization' matches 'optimized for H100 GPUs'")
print("  • 'code generation' matches 'programming' and 'developer tools'")
print("  • 'fast inference' matches 'low latency' and 'high throughput'")
print()
cprint("=" * 80, "cyan")
cprint("Want Hybrid Search?", "cyan")
cprint("=" * 80, "cyan")
print()
print("FAISS doesn't support hybrid search (vector + keyword).")
print()
print("To use hybrid search, switch to one of these providers:")
print("  • SQLite-Vec (inline, easy to use)")
print("  • Milvus (remote, scalable)")
print("  • Weaviate (remote, cloud-native)")
print("  • PGVector (remote, PostgreSQL-based)")
print()
print("See HYBRID_SEARCH_GUIDE.md for detailed instructions.")
print()
cprint("=" * 80, "cyan")

