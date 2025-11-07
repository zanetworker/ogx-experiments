#!/usr/bin/env python3
"""
Test LLM-as-Judge functionality in Llama Stack

This script demonstrates:
1. Listing datasets
2. Registering scoring functions (basic and LLM-as-judge)
3. Listing available scoring functions
"""
import os
import httpx
from llama_stack_client import LlamaStackClient

# Initialize Llama Stack client
port = os.environ.get('LLAMA_STACK_PORT', '8321')
client = LlamaStackClient(base_url=f"http://localhost:{port}")

print("=" * 80)
print("LLM-as-Judge Testing with Llama Stack Client")
print("=" * 80)
print()

# Test 1: List datasets
print("Test 1: List datasets")
print("-" * 80)
try:
    # Note: The beta.datasets API is not yet available in the client
    # Using direct HTTP call as fallback
    response = httpx.get(f"http://localhost:{port}/v1beta/datasets")
    response.raise_for_status()
    datasets = response.json().get('data', [])

    print(f"✅ Found {len(datasets)} datasets\n")
    for dataset in datasets:
        print(f"  📊 {dataset['identifier']}")
        print(f"     Purpose: {dataset['purpose']}")
        if 'source' in dataset and 'rows' in dataset['source']:
            print(f"     Rows: {len(dataset['source']['rows'])}")
        print()
except Exception as e:
    print(f"❌ Error: {e}\n")

# Test 2: Register scoring function (exact match)
print("\nTest 2: Register exact match scoring function")
print("-" * 80)
try:
    client.scoring_functions.register(
        scoring_fn_id="test_exact_match",
        description="Test exact match scoring",
        return_type={"type": "string"},
        provider_id="basic",
        provider_scoring_fn_id="equality"
    )
    print(f"✅ Successfully registered 'test_exact_match'\n")
except Exception as e:
    if "already exists" in str(e).lower() or "409" in str(e):
        print(f"⚠️  Scoring function 'test_exact_match' already exists\n")
    elif "501" in str(e) or "Not implemented" in str(e):
        print(f"⚠️  Basic provider doesn't support registration (uses built-in functions)\n")
    else:
        print(f"❌ Error: {e}\n")

# Test 3: Register LLM-as-judge scoring function
print("Test 3: Register LLM-as-judge scoring function")
print("-" * 80)
try:
    client.scoring_functions.register(
        scoring_fn_id="test_llm_judge_custom",
        description="Custom LLM judge for quality scoring",
        return_type={"type": "string"},
        provider_id="llm-as-judge",
        provider_scoring_fn_id="base",
        params={
            "type": "llm_as_judge",
            "judge_model": "openai/gpt-4o",
            "prompt_template": """Evaluate the quality of this answer on a scale of 1-10.

Question: {question}
Answer: {generated_answer}

Provide your rating as: Score: X

Score: """,
            "judge_score_regexes": [r"Score:\s*(\d+)"],
            "aggregation_functions": ["average"]
        }
    )
    print(f"✅ Successfully registered 'test_llm_judge_custom'\n")
except Exception as e:
    if "already exists" in str(e).lower() or "409" in str(e) or "400" in str(e):
        print(f"⚠️  Scoring function 'test_llm_judge_custom' already exists\n")
    else:
        print(f"❌ Error: {e}\n")

# Test 4: List scoring functions
print("Test 4: List scoring functions")
print("-" * 80)
try:
    scoring_fns = client.scoring_functions.list()
    print(f"✅ Found {len(scoring_fns)} scoring functions\n")

    # Group by provider
    by_provider = {}
    for fn in scoring_fns:
        provider = fn.provider_id or "unknown"
        if provider not in by_provider:
            by_provider[provider] = []
        by_provider[provider].append(fn.identifier)

    for provider, fns in sorted(by_provider.items()):
        print(f"  📦 {provider.upper()}:")
        for fn_id in sorted(fns):
            # Highlight custom functions
            marker = "⭐" if "test_" in fn_id else "  "
            print(f"    {marker} {fn_id}")
        print()

    print("=" * 80)
    print("Summary:")
    print(f"  • Total scoring functions: {len(scoring_fns)}")
    print(f"  • Providers: {', '.join(sorted(by_provider.keys()))}")
    custom_fns = [fn for fn in scoring_fns if 'test_' in fn.identifier]
    if custom_fns:
        print(f"  • Custom functions: {', '.join([fn.identifier for fn in custom_fns])}")
    print("=" * 80)
except Exception as e:
    print(f"❌ Error: {e}\n")

