# Hybrid Search in Llama Stack

## Overview

Hybrid search combines **vector search** (semantic similarity) with **keyword search** (exact term matching) to provide more comprehensive and accurate results.

## How It Works

### 1. Vector Search (Semantic Similarity)
- Uses embedding models to convert text into high-dimensional vectors
- Finds semantically similar content even if exact words don't match
- Great for: concept matching, paraphrases, understanding intent

### 2. Keyword Search (BM25/FTS5)
- Traditional full-text search using algorithms like BM25
- Finds exact term matches and technical jargon
- Great for: specific names, technical terms, exact phrases

### 3. Hybrid Search (Combined)
- Runs both vector and keyword search
- Combines results using a reranking algorithm
- Gets the best of both worlds

## Reranking Strategies

### RRF (Reciprocal Rank Fusion) - DEFAULT

**Formula:** `score = 1 / (impact_factor + rank)`

**Parameters:**
- `impact_factor`: Controls weight given to top-ranked results (default: 60.0)
- Higher values = more weight to top-ranked items

**Example:**
```python
search_response = client.vector_stores.search(
    vector_store_id=vector_store_id,
    query="neural networks in Python",
    search_mode="hybrid",
    max_num_results=5,
    ranking_options={
        "ranker": "rrf:100.0"  # impact_factor=100.0
    },
)
```

**When to use:**
- General purpose hybrid search
- Balanced results from both search methods
- Don't know which search method is more important

### Weighted Ranker

**Formula:** `score = alpha * vector_score + (1-alpha) * keyword_score`

**Parameters:**
- `alpha`: Weight between 0.0 and 1.0 (default: 0.5)
  - `alpha=1.0` → 100% vector, 0% keyword
  - `alpha=0.5` → 50% vector, 50% keyword
  - `alpha=0.0` → 0% vector, 100% keyword

**Example:**
```python
search_response = client.vector_stores.search(
    vector_store_id=vector_store_id,
    query="neural networks in Python",
    search_mode="hybrid",
    max_num_results=5,
    ranking_options={
        "ranker": "weighted:0.7"  # 70% vector, 30% keyword
    },
)
```

**When to use:**
- You know semantic or keyword search is more important
- Fine-tuned control over search balance
- Domain-specific requirements

## Provider Support

| Provider | Vector | Keyword | Hybrid | Notes |
|----------|--------|---------|--------|-------|
| **FAISS** | ✅ | ❌ | ❌ | Pure vector similarity only |
| **SQLite-Vec** | ✅ | ✅ | ✅ | Uses SQLite FTS5 for keyword search |
| **Milvus** | ✅ | ✅ | ✅ | Native BM25 support |
| **Weaviate** | ✅ | ✅ | ✅ | Native hybrid search |
| **PGVector** | ✅ | ✅ | ✅ | PostgreSQL full-text search |

### Important Note About FAISS

**FAISS only supports vector search!** It does not support:
- Keyword search (`search_mode="keyword"`)
- Hybrid search (`search_mode="hybrid"`)

If you need hybrid search, use one of these providers instead:
- **SQLite-Vec** (inline, disk-based, good for frequent writes)
- **Milvus** (remote, scalable, production-ready)
- **Weaviate** (remote, cloud-native)
- **PGVector** (remote, PostgreSQL-based)

## Usage Examples

### Vector Search Only (Works with FAISS)

```python
from llama_stack_client import LlamaStackClient

client = LlamaStackClient(base_url="http://localhost:8321")

# Pure vector search
results = client.vector_stores.search(
    vector_store_id="vs_123",
    query="H100 GPU optimization",
    search_mode="vector",  # Default
    max_num_results=5,
)

for result in results.data:
    print(f"Score: {result.score}")
    print(f"Content: {result.content[0].text[:200]}...")
```

### Hybrid Search (Requires SQLite-Vec, Milvus, Weaviate, or PGVector)

```python
# Basic hybrid search with default RRF ranker
results = client.vector_stores.search(
    vector_store_id="vs_123",
    query="H100 GPU optimization",
    search_mode="hybrid",
    max_num_results=5,
)

# Hybrid search with custom RRF impact factor
results = client.vector_stores.search(
    vector_store_id="vs_123",
    query="H100 GPU optimization",
    search_mode="hybrid",
    max_num_results=5,
    ranking_options={
        "ranker": "rrf:100.0"  # Higher weight to top results
    },
)

# Hybrid search with weighted ranker (70% vector, 30% keyword)
results = client.vector_stores.search(
    vector_store_id="vs_123",
    query="H100 GPU optimization",
    search_mode="hybrid",
    max_num_results=5,
    ranking_options={
        "ranker": "weighted:0.7"  # alpha=0.7
    },
)
```

### Keyword Search Only (Requires SQLite-Vec, Milvus, Weaviate, or PGVector)

```python
# Pure keyword search (BM25)
results = client.vector_stores.search(
    vector_store_id="vs_123",
    query="H100 GPU optimization",
    search_mode="keyword",
    max_num_results=5,
)
```

## When to Use Each Search Mode

### Use Vector Search When:
- Looking for conceptually similar content
- Query uses different words than the documents
- Understanding semantic meaning is important
- Handling paraphrases or synonyms

**Example:** "machine learning algorithms" should match "ML techniques"

### Use Keyword Search When:
- Looking for exact terms or phrases
- Searching for technical jargon or specific names
- Need precise term matching
- Documents use consistent terminology

**Example:** "NVIDIA H100" should match exactly "NVIDIA H100"

### Use Hybrid Search When:
- Want the best of both worlds
- Don't know if semantic or exact matching is more important
- Dealing with diverse query types
- Need robust search across different content types

**Example:** "best models for H100 GPU" benefits from both semantic understanding and exact term matching

## Switching from FAISS to SQLite-Vec for Hybrid Search

If you're currently using FAISS and want hybrid search, here's how to switch to SQLite-Vec:

### 1. Update your Llama Stack configuration

```yaml
# In your stack run YAML file
vector_io:
  - provider_id: sqlite-vec
    provider_type: inline::sqlite-vec
    config:
      db_path: ~/.llama/vector_stores/sqlite_vec.db
```

### 2. Create a new vector store with SQLite-Vec

```python
from llama_stack_client import LlamaStackClient

client = LlamaStackClient(base_url="http://localhost:8321")

# Create vector store with SQLite-Vec provider
vector_store = client.vector_stores.create(
    name="my_hybrid_search_store",
    metadata={"description": "Supports hybrid search"},
    extra_body={
        "embedding_model": "ollama/nomic-embed-text:latest",
        "embedding_dimension": 768,
        "provider_id": "sqlite-vec",  # Use SQLite-Vec instead of FAISS
    }
)
```

### 3. Ingest your data

```python
# Upload and attach files (same as before)
file_response = client.files.create(
    file=open("document.txt", "rb"),
    purpose="assistants"
)

client.vector_stores.files.create(
    vector_store_id=vector_store.id,
    file_id=file_response.id
)
```

### 4. Use hybrid search

```python
# Now you can use hybrid search!
results = client.vector_stores.search(
    vector_store_id=vector_store.id,
    query="your query here",
    search_mode="hybrid",
    max_num_results=5,
)
```

## Performance Considerations

### FAISS
- **Fastest** for pure vector search
- In-memory, optimized for speed
- GPU acceleration available
- Best for: read-heavy workloads, datasets that fit in memory

### SQLite-Vec
- **Good balance** of speed and features
- Disk-based storage (larger datasets)
- Supports all search modes
- Best for: frequent writes, hybrid search needs

### Milvus/Weaviate
- **Production-ready** distributed systems
- Horizontal scaling
- Advanced features (filtering, multi-tenancy)
- Best for: large-scale production deployments

## Summary

| Feature | FAISS | SQLite-Vec | Milvus | Weaviate |
|---------|-------|------------|--------|----------|
| Vector Search | ✅ | ✅ | ✅ | ✅ |
| Keyword Search | ❌ | ✅ | ✅ | ✅ |
| Hybrid Search | ❌ | ✅ | ✅ | ✅ |
| Speed | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Scalability | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Ease of Use | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| Deployment | Inline | Inline | Remote | Remote |

**Recommendation:**
- **Development/Testing:** FAISS (if vector-only) or SQLite-Vec (if hybrid needed)
- **Production (small-medium):** SQLite-Vec
- **Production (large-scale):** Milvus or Weaviate

