#!/usr/bin/env python3
"""
Demonstration of Hybrid Search in Llama Stack

Hybrid search combines:
1. Vector Search (semantic similarity using embeddings)
2. Keyword Search (BM25/FTS5 for exact term matching)

Two reranking strategies:
1. RRF (Reciprocal Rank Fusion) - default
2. Weighted - linear combination of scores
"""
import os
from llama_stack_client import LlamaStackClient
from termcolor import cprint

# Initialize Llama Stack client
port = os.environ.get('LLAMA_STACK_PORT', '8321')
client = LlamaStackClient(base_url=f"http://localhost:{port}")

# Use the RedHat AI models vector store we just created
vector_store_id = "vs_38624989-3407-43ce-a2b3-d5d1ae71442d"

cprint("=" * 80, "cyan")
cprint("Hybrid Search Demo - Llama Stack", "cyan")
cprint("=" * 80, "cyan")
print()

# Test query
query = "H100 GPU optimization and performance"

cprint(f"Query: {query}", "yellow")
print()

# ============================================================================
# 1. VECTOR SEARCH ONLY (Semantic Similarity)
# ============================================================================
cprint("1. VECTOR SEARCH (Semantic Similarity)", "cyan")
cprint("-" * 80, "cyan")

vector_results = client.vector_stores.search(
    vector_store_id=vector_store_id,
    query=query,
    search_mode="vector",  # Pure vector search
    max_num_results=3,
)

print(f"Found {len(vector_results.data)} results")
for i, result in enumerate(vector_results.data, 1):
    print(f"\n  [{i}] Score: {result.score:.4f}")
    print(f"      Content: {result.content[:150]}...")
    if hasattr(result, 'metadata') and result.metadata:
        print(f"      File: {result.metadata.get('filename', 'N/A')}")

print()

# ============================================================================
# 2. KEYWORD SEARCH ONLY (BM25/FTS5)
# ============================================================================
cprint("2. KEYWORD SEARCH (BM25 - Exact Term Matching)", "cyan")
cprint("-" * 80, "cyan")

keyword_results = client.vector_stores.search(
    vector_store_id=vector_store_id,
    query=query,
    search_mode="keyword",  # Pure keyword search
    max_num_results=3,
)

print(f"Found {len(keyword_results.data)} results")
for i, result in enumerate(keyword_results.data, 1):
    print(f"\n  [{i}] Score: {result.score:.4f}")
    print(f"      Content: {result.content[:150]}...")
    if hasattr(result, 'metadata') and result.metadata:
        print(f"      File: {result.metadata.get('filename', 'N/A')}")

print()

# ============================================================================
# 3. HYBRID SEARCH - RRF Ranker (Default)
# ============================================================================
cprint("3. HYBRID SEARCH - RRF Ranker (Reciprocal Rank Fusion)", "cyan")
cprint("-" * 80, "cyan")
print("Combines vector + keyword search using RRF algorithm")
print("Higher impact_factor = more weight to top-ranked results")
print()

hybrid_rrf_results = client.vector_stores.search(
    vector_store_id=vector_store_id,
    query=query,
    search_mode="hybrid",
    max_num_results=3,
    # Default RRF ranker with impact_factor=60.0
)

print(f"Found {len(hybrid_rrf_results.data)} results")
for i, result in enumerate(hybrid_rrf_results.data, 1):
    print(f"\n  [{i}] Score: {result.score:.4f}")
    print(f"      Content: {result.content[:150]}...")
    if hasattr(result, 'metadata') and result.metadata:
        print(f"      File: {result.metadata.get('filename', 'N/A')}")

print()

# ============================================================================
# 4. HYBRID SEARCH - RRF with Custom Impact Factor
# ============================================================================
cprint("4. HYBRID SEARCH - RRF with Custom Impact Factor", "cyan")
cprint("-" * 80, "cyan")
print("Using impact_factor=100.0 (higher weight to top results)")
print()

hybrid_rrf_custom = client.vector_stores.search(
    vector_store_id=vector_store_id,
    query=query,
    search_mode="hybrid",
    max_num_results=3,
    ranking_options={
        "ranker": {
            "type": "rrf",
            "impact_factor": 100.0,  # Higher = more weight to top-ranked results
        }
    },
)

print(f"Found {len(hybrid_rrf_custom.data)} results")
for i, result in enumerate(hybrid_rrf_custom.data, 1):
    print(f"\n  [{i}] Score: {result.score:.4f}")
    print(f"      Content: {result.content[:150]}...")
    if hasattr(result, 'metadata') and result.metadata:
        print(f"      File: {result.metadata.get('filename', 'N/A')}")

print()

# ============================================================================
# 5. HYBRID SEARCH - Weighted Ranker (70% Vector, 30% Keyword)
# ============================================================================
cprint("5. HYBRID SEARCH - Weighted Ranker (70% Vector, 30% Keyword)", "cyan")
cprint("-" * 80, "cyan")
print("Linear combination: alpha=0.7 means 70% vector, 30% keyword")
print()

hybrid_weighted = client.vector_stores.search(
    vector_store_id=vector_store_id,
    query=query,
    search_mode="hybrid",
    max_num_results=3,
    ranking_options={
        "ranker": {
            "type": "weighted",
            "alpha": 0.7,  # 70% vector search, 30% keyword search
        }
    },
)

print(f"Found {len(hybrid_weighted.data)} results")
for i, result in enumerate(hybrid_weighted.data, 1):
    print(f"\n  [{i}] Score: {result.score:.4f}")
    print(f"      Content: {result.content[:150]}...")
    if hasattr(result, 'metadata') and result.metadata:
        print(f"      File: {result.metadata.get('filename', 'N/A')}")

print()

# ============================================================================
# 6. HYBRID SEARCH - Weighted Ranker (30% Vector, 70% Keyword)
# ============================================================================
cprint("6. HYBRID SEARCH - Weighted Ranker (30% Vector, 70% Keyword)", "cyan")
cprint("-" * 80, "cyan")
print("Linear combination: alpha=0.3 means 30% vector, 70% keyword")
print()

hybrid_weighted_keyword = client.vector_stores.search(
    vector_store_id=vector_store_id,
    query=query,
    search_mode="hybrid",
    max_num_results=3,
    ranking_options={
        "ranker": {
            "type": "weighted",
            "alpha": 0.3,  # 30% vector search, 70% keyword search
        }
    },
)

print(f"Found {len(hybrid_weighted_keyword.data)} results")
for i, result in enumerate(hybrid_weighted_keyword.data, 1):
    print(f"\n  [{i}] Score: {result.score:.4f}")
    print(f"      Content: {result.content[:150]}...")
    if hasattr(result, 'metadata') and result.metadata:
        print(f"      File: {result.metadata.get('filename', 'N/A')}")

print()

# ============================================================================
# Summary
# ============================================================================
cprint("=" * 80, "cyan")
cprint("SUMMARY: How Hybrid Search Works in Llama Stack", "cyan")
cprint("=" * 80, "cyan")
print()
print("🔍 SEARCH MODES:")
print("  • vector   - Pure semantic similarity using embeddings")
print("  • keyword  - Pure keyword matching using BM25/FTS5")
print("  • hybrid   - Combines both with reranking")
print()
print("🎯 RERANKING STRATEGIES:")
print()
print("  1. RRF (Reciprocal Rank Fusion) - DEFAULT")
print("     • Formula: score = 1 / (impact_factor + rank)")
print("     • impact_factor: Controls weight to top results (default: 60.0)")
print("     • Higher impact_factor = more weight to top-ranked items")
print("     • Good for: General purpose, balanced results")
print()
print("  2. Weighted Ranker")
print("     • Formula: score = alpha * vector_score + (1-alpha) * keyword_score")
print("     • alpha: 0.0 to 1.0 (default: 0.5)")
print("     • alpha=1.0 = 100% vector, 0% keyword")
print("     • alpha=0.0 = 0% vector, 100% keyword")
print("     • Good for: Fine-tuned control over search balance")
print()
print("💡 WHEN TO USE EACH:")
print("  • Vector Search: Semantic queries, concept matching, paraphrases")
print("  • Keyword Search: Exact terms, technical jargon, specific names")
print("  • Hybrid (RRF): Best overall results, balanced approach")
print("  • Hybrid (Weighted): When you know if semantic or keyword is more important")
print()
print("📊 PROVIDER SUPPORT:")
print("  • FAISS: ✅ (using SQLite FTS5 for keyword search)")
print("  • SQLite-Vec: ✅ (using SQLite FTS5 for keyword search)")
print("  • Milvus: ✅ (native hybrid search with BM25)")
print("  • Weaviate: ✅ (native hybrid search)")
print("  • PGVector: ✅ (using PostgreSQL full-text search)")
print()
cprint("=" * 80, "cyan")

