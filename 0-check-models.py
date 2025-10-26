#!/usr/bin/env python3
"""
Quick script to check available models and shields in Llama Stack
"""

import os
from openai import OpenAI
import httpx

llama_stack_url = f"http://0.0.0.0:{os.environ.get('LLAMA_STACK_PORT', '8321')}"

print("=" * 80)
print("Llama Stack Configuration Check")
print("=" * 80)
print(f"\n📍 Llama Stack URL: {llama_stack_url}\n")

# Check models
print("=" * 80)
print("Registered Models:")
print("=" * 80)

try:
    response = httpx.get(f"{llama_stack_url}/v1/models")
    if response.status_code == 200:
        models = response.json()
        if models.get("data"):
            for model in models["data"]:
                model_id = model.get('identifier') or model.get('model_id') or model.get('id', 'Unknown')
                model_type = model.get('model_type', '')
                print(f"  ✓ {model_id} ({model_type})")
        else:
            print("  ⚠️  No models registered!")
    else:
        print(f"  ❌ HTTP {response.status_code}")
except Exception as e:
    print(f"  ❌ Error: {e}")

# Check shields
print("\n" + "=" * 80)
print("Registered Shields:")
print("=" * 80)

try:
    response = httpx.get(f"{llama_stack_url}/v1/shields")
    if response.status_code == 200:
        shields = response.json()
        if shields.get("data"):
            for shield in shields["data"]:
                print(f"  ✓ {shield['identifier']} -> {shield.get('provider_resource_id', 'N/A')}")
        else:
            print("  ⚠️  No shields registered!")
    else:
        print(f"  ❌ HTTP {response.status_code}: {response.text}")
except Exception as e:
    print(f"  ❌ Error: {e}")

print("\n" + "=" * 80)
print("Summary:")
print("=" * 80)
print("""
If models or shields are missing:
1. Verify your run.yaml has the correct configuration
2. Restart Llama Stack with: llama stack run <your-config>.yaml
3. Check if Ollama has the model: ollama list
4. Pull if needed: ollama pull llama-guard3:1b
""")