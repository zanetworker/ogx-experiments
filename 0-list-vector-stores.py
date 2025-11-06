#!/usr/bin/env python3
"""List all vector stores in Llama Stack"""
import os
from openai import OpenAI
from termcolor import cprint

# Initialize OpenAI client for Llama Stack
port = os.environ.get('LLAMA_STACK_PORT', '8321')
client = OpenAI(
    base_url=f"http://localhost:{port}/v1",
    api_key="not-needed"
)

cprint(f"Connected to Llama Stack at http://localhost:{port}", "cyan")
print()

# List vector stores
cprint("=== Vector Stores ===", "cyan")
try:
    vector_stores = client.vector_stores.list()
    
    if not vector_stores.data:
        cprint("No vector stores found", "yellow")
    else:
        for vs in vector_stores.data:
            print(f"\nID: {vs.id}")
            print(f"  Name: {vs.name}")
            print(f"  Created: {vs.created_at}")
            if hasattr(vs, 'file_counts'):
                print(f"  Files: {vs.file_counts.completed} completed, {vs.file_counts.failed} failed, {vs.file_counts.in_progress} in progress")
            if hasattr(vs, 'metadata') and vs.metadata:
                print(f"  Metadata: {vs.metadata}")
                
except Exception as e:
    cprint(f"Error listing vector stores: {e}", "red")
    import traceback
    traceback.print_exc()

