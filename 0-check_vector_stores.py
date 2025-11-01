from llama_stack_client import LlamaStackClient
import os

port = os.environ.get('LLAMA_STACK_PORT', '8321')
client = LlamaStackClient(base_url=f"http://localhost:{port}")

print("Existing vector stores:")
try:
    stores = list(client.vector_stores.list())
    if stores:
        for store in stores:
            print(f"  - ID: {store.id}, Name: {store.name}")
    else:
        print("  (none found)")
except Exception as e:
    print(f"  Error: {e}")
