# RAG

| Script | What it tests |
|--------|--------------|
| `check_vector_stores.py` | List vector stores |
| `list_vector_stores.py` | List vector stores with pagination |
| `vector_search.py` | Semantic search against a FAISS store |
| `rag_file_search.py` | End-to-end RAG: create vector store, upload files, query with file_search |
| `rag_hybrid_search.py` | Compare vector, keyword, and hybrid search modes |

Requires an embedding model (sentence-transformers or Ollama with nomic-embed-text).
