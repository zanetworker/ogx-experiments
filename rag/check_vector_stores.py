from openai import OpenAI
import os

port = os.environ.get('OGX_PORT', '8321')
client = OpenAI(base_url=f"http://localhost:{port}/v1", api_key="unused")

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
