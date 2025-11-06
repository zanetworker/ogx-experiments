#!/usr/bin/env python3
"""
Setup script to create a vector store for RedHat AI models
and update the .env file with the new vector store ID
"""
import os
from openai import OpenAI
from termcolor import cprint
import re

def update_env_file(env_path, vector_store_id):
    """Update the .env file with the new vector store ID"""
    with open(env_path, 'r') as f:
        content = f.read()
    
    # Replace the VECTOR_DB_ID line
    updated_content = re.sub(
        r'VECTOR_DB_ID=.*',
        f'VECTOR_DB_ID={vector_store_id}',
        content
    )
    
    with open(env_path, 'w') as f:
        f.write(updated_content)
    
    cprint(f"✓ Updated {env_path} with new vector store ID", "green")

def main():
    # Configuration
    port = os.environ.get('LLAMA_STACK_PORT', '8321')
    
    # Initialize OpenAI client for Llama Stack
    client = OpenAI(
        base_url=f"http://localhost:{port}/v1",
        api_key="not-needed"
    )
    
    cprint("=" * 80, "cyan")
    cprint("RedHat AI Models - Vector Store Setup", "cyan")
    cprint("=" * 80, "cyan")
    print()
    
    # Create vector store
    cprint("Creating vector store for RedHat AI models...", "yellow")
    
    vector_store = client.vector_stores.create(
        name="redhat_ai_models",
        metadata={
            "description": "RedHat AI validated models from HuggingFace",
            "organization": "RedHatAI",
            "purpose": "model_recommendation"
        },
        extra_body={
            "embedding_model": "ollama/nomic-embed-text:latest",
            "embedding_dimension": 768,
            "provider_id": "faiss"
        }
    )
    
    vector_store_id = vector_store.id
    
    cprint(f"✓ Created vector store: {vector_store_id}", "green")
    print(f"  Name: {vector_store.name}")
    print(f"  Embedding model: ollama/nomic-embed-text:latest")
    print(f"  Embedding dimension: 768")
    print(f"  Provider: faiss")
    print()
    
    # Update .env file
    env_path = "redhatai_validated_models/.env"
    if os.path.exists(env_path):
        cprint(f"Updating {env_path}...", "yellow")
        update_env_file(env_path, vector_store_id)
    else:
        cprint(f"⚠ Warning: {env_path} not found", "yellow")
        cprint(f"Please manually set VECTOR_DB_ID={vector_store_id} in your .env file", "yellow")
    
    print()
    cprint("=" * 80, "cyan")
    cprint("Next Steps:", "cyan")
    cprint("=" * 80, "cyan")
    print()
    print("1. Ingest RedHat AI model data into the vector store:")
    print("   cd redhatai_validated_models")
    print("   python scripts/ingest_models.py")
    print()
    print("2. Start the MCP server:")
    print("   python src/mcp_server/server.py")
    print()
    print("3. Test the MCP integration:")
    print("   cd ..")
    print("   python 3-mcp-with-responses.py")
    print()
    cprint("=" * 80, "cyan")

if __name__ == "__main__":
    main()

