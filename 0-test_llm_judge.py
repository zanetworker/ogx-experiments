#!/usr/bin/env python3
import httpx
import json

base_url = "http://localhost:8321"
client = httpx.Client(timeout=60.0)

# Test 1: List datasets
print("Test 1: List datasets")
try:
    response = client.get(f"{base_url}/v1beta/datasets")
    print(f"✅ Status: {response.status_code}")
    print(f"Response: {response.json()}\n")
except Exception as e:
    print(f"❌ Error: {e}\n")

# Test 2: Register scoring function (exact match)
print("Test 2: Register exact match scoring function")
try:
    response = client.post(
        f"{base_url}/v1/scoring-functions",
        json={
            "scoring_fn_id": "test_exact_match",
            "description": "Test exact match",
            "return_type": "string",
            "provider_id": "basic",
            "provider_scoring_fn_id": "exact_match"
        }
    )
    print(f"✅ Status: {response.status_code}")
    if response.status_code != 409:
        print(f"Response: {response.json()}\n")
    else:
        print("Already exists\n")
except Exception as e:
    print(f"❌ Error: {e}\n")

# Test 3: Register LLM-as-judge scoring function
print("Test 3: Register LLM-as-judge scoring function")
try:
    response = client.post(
        f"{base_url}/v1/scoring-functions",
        json={
            "scoring_fn_id": "test_llm_judge",
            "description": "Test LLM judge",
            "return_type": "float",
            "provider_id": "llm-as-judge",
            "provider_scoring_fn_id": "llm-as-judge-base",
            "params": {
                "type": "llm_as_judge",
                "judge_model": "openai/gpt-4o",
                "prompt_template": "Rate this: {generated_answer}\nScore: ",
                "judge_score_regexes": [r"Score: (\d+)"],
                "aggregation_functions": ["average"]
            }
        }
    )
    print(f"✅ Status: {response.status_code}")
    if response.status_code == 409:
        print("Already exists\n")
    else:
        print(f"Response: {response.text}\n")
except Exception as e:
    print(f"❌ Error: {e}\n")

# Test 4: List scoring functions
print("Test 4: List scoring functions")
try:
    response = client.get(f"{base_url}/v1/scoring-functions")
    print(f"✅ Status: {response.status_code}")
    data = response.json()
    print(f"Found {len(data.get('data', []))} scoring functions")
    for fn in data.get('data', []):
        print(f"  - {fn.get('identifier')}")
except Exception as e:
    print(f"❌ Error: {e}\n")

