"""
Shared utilities for RAG experiments with modern Llama Stack API
"""
import os
from typing import List, Dict, Any
from llama_stack_client import LlamaStackClient


def simple_chunk_text(text: str, chunk_size: int = 2048, overlap: int = 200) -> List[str]:
    """
    Simple text chunking by character count
    
    Args:
        text: Text to chunk
        chunk_size: Size of each chunk in characters
        overlap: Overlap between chunks in characters
        
    Returns:
        List of text chunks
    """
    chunks = []
    start = 0
    text_len = len(text)
    
    while start < text_len:
        end = start + chunk_size
        chunk_text = text[start:end]
        if chunk_text.strip():
            chunks.append(chunk_text)
        start = end - overlap if end < text_len else end
    
    return chunks


def create_or_get_vector_store(
    client: LlamaStackClient,
    name: str,
    embedding_model: str = "all-MiniLM-L6-v2",
    description: str = "Vector store"
) -> str:
    """
    Create a new vector store or get existing one by name
    
    Args:
        client: LlamaStackClient instance
        name: Name for the vector store
        embedding_model: Embedding model to use (REQUIRED by vector_stores.create)
        description: Description for metadata
        
    Returns:
        Vector store ID (string starting with "vs_")
    """
    try:
        # Try to create new vector store (embedding_model is REQUIRED)
        vector_store = client.vector_stores.create(
            name=name,
            embedding_model=embedding_model,  # REQUIRED parameter
            metadata={"description": description}
        )
        return vector_store.id
    except Exception as e:
        # If it fails, try to find existing store by name
        error_msg = str(e).lower()
        if "already exists" in error_msg or "duplicate" in error_msg:
            stores = list(client.vector_stores.list())
            for store in stores:
                if store.name == name:
                    return store.id
        # If not found, raise the original error
        raise


def insert_documents_as_chunks(
    client: LlamaStackClient,
    vector_store_id: str,
    documents: List[dict],
    chunk_size: int = 2048,
    chunk_overlap: int = 200
) -> int:
    """
    Chunk documents and insert into vector store using vector_io.insert
    
    Args:
        client: LlamaStackClient instance
        vector_store_id: ID of the vector store
        documents: List of dicts with 'document_id' and 'content' keys
        chunk_size: Size of chunks in characters
        chunk_overlap: Overlap between chunks
        
    Returns:
        Number of chunks inserted
    """
    all_chunks = []
    
    for doc in documents:
        # Chunk the content
        chunks = simple_chunk_text(
            doc['content'],
            chunk_size=chunk_size,
            overlap=chunk_overlap
        )
        
        # Convert to vector_io format
        for idx, chunk_text in enumerate(chunks):
            all_chunks.append({
                "content": chunk_text,
                "metadata": {
                    "document_id": doc['document_id'],  # REQUIRED
                    "chunk_index": idx,
                    **{k: v for k, v in doc.items() if k not in ['document_id', 'content']}
                }
            })
    
    # Insert using vector_io
    client.vector_io.insert(
        vector_db_id=vector_store_id,
        chunks=all_chunks
    )
    
    return len(all_chunks)


def query_with_responses_api(
    openai_client,
    vector_store_id: str,
    query: str,
    model_id: str,
    instructions: str = "Answer based on the retrieved context.",
    max_results: int = 5
) -> str:
    """
    Query using Responses API with file_search
    
    Args:
        openai_client: OpenAI client instance
        vector_store_id: ID of the vector store
        query: Query text
        model_id: Model ID to use
        instructions: System instructions
        max_results: Max number of results to retrieve
        
    Returns:
        Response text from the model
    """
    response = openai_client.responses.create(
        model=model_id,
        input=query,
        instructions=instructions,
        tools=[{
            "type": "file_search",
            "vector_store_ids": [vector_store_id],
            "max_num_results": max_results
        }],
        tool_choice="required",
        stream=False
    )
    
    # Extract response text
    if hasattr(response, 'output'):
        for item in response.output:
            if hasattr(item, 'type') and item.type == "message":
                if hasattr(item, 'content'):
                    for content in item.content:
                        if hasattr(content, 'text'):
                            return content.text
    
    return ""