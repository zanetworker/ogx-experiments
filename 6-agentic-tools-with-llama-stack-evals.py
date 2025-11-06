#!/usr/bin/env python3
"""
Llama Stack Evaluation APIs Demo

Shows how to use:
- Datasets API: Register test data
- Scoring Functions API: Define scoring logic
- Benchmarks API: Link dataset + scoring
- Eval API: Run evaluations
"""

import json
import os
import time
from datetime import datetime
from typing import Dict, List, Any
from openai import OpenAI
from termcolor import colored
import httpx


# ============================================================================
# Llama Stack Eval Client
# ============================================================================

class LlamaStackEvalClient:
    def __init__(self, base_url: str):
        # Remove trailing /v1 if present, then remove trailing slashes
        if base_url.endswith('/v1'):
            base_url = base_url[:-3]
        self.base_url = base_url.rstrip('/')
        self.timeout = 60.0

    def _get_client(self):
        return httpx.Client(timeout=self.timeout)

    # Datasets API
    def register_dataset(self, dataset_id: str, rows: List[Dict[str, Any]], purpose: str = "eval/question-answer") -> Dict:
        with self._get_client() as client:
            response = client.post(f"{self.base_url}/v1beta/datasets", json={
                "dataset_id": dataset_id, "purpose": purpose,
                "source": {"type": "rows", "rows": rows},
                "metadata": {"description": "Tool calling eval", "created_at": datetime.now().isoformat()}
            })
            if response.status_code == 409:
                return {"dataset_id": dataset_id}
            response.raise_for_status()
            return response.json()

    def list_datasets(self) -> List[Dict]:
        with self._get_client() as client:
            response = client.get(f"{self.base_url}/v1beta/datasets")
            response.raise_for_status()
            return response.json().get('data', [])

    # Scoring Functions API
    def register_scoring_function(self, scoring_fn_id: str, provider_id: str, provider_scoring_fn_id: str) -> Dict:
        with self._get_client() as client:
            response = client.post(f"{self.base_url}/v1/scoring-functions", json={
                "scoring_fn_id": scoring_fn_id,
                "provider_id": provider_id,
                "provider_scoring_fn_id": provider_scoring_fn_id
            })
            if response.status_code == 409:
                return {"scoring_fn_id": scoring_fn_id}
            response.raise_for_status()
            return response.json()

    def list_scoring_functions(self) -> List[Dict]:
        with self._get_client() as client:
            response = client.get(f"{self.base_url}/v1/scoring-functions")
            response.raise_for_status()
            return response.json().get('data', [])

    def score_rows(self, input_rows: List[Dict], scoring_functions: Dict[str, Any]) -> Dict:
        with self._get_client() as client:
            response = client.post(f"{self.base_url}/v1/scoring/score", json={
                "input_rows": input_rows,
                "scoring_functions": scoring_functions
            })
            response.raise_for_status()
            return response.json()

    # Benchmarks API
    def register_benchmark(self, benchmark_id: str, dataset_id: str, scoring_functions: List[str]) -> Dict:
        with self._get_client() as client:
            response = client.post(f"{self.base_url}/v1alpha/eval/benchmarks", json={
                "benchmark_id": benchmark_id,
                "dataset_id": dataset_id,
                "scoring_functions": scoring_functions,
                "metadata": {"description": "Tool calling benchmark", "created_at": datetime.now().isoformat()}
            })
            if response.status_code == 409:
                return {"benchmark_id": benchmark_id}
            response.raise_for_status()
            return response.json()

    def list_benchmarks(self) -> List[Dict]:
        with self._get_client() as client:
            response = client.get(f"{self.base_url}/v1alpha/eval/benchmarks")
            response.raise_for_status()
            return response.json().get('data', [])

    # Eval API
    def run_eval(self, benchmark_id: str, benchmark_config: Dict) -> Dict:
        with self._get_client() as client:
            response = client.post(
                f"{self.base_url}/alpha/eval/benchmarks/{benchmark_id}/jobs",
                json={"benchmark_config": benchmark_config}
            )
            response.raise_for_status()
            return response.json()

    def evaluate_rows(self, benchmark_id: str, input_rows: List[Dict], scoring_functions: List[str], benchmark_config: Dict) -> Dict:
        with self._get_client() as client:
            response = client.post(f"{self.base_url}/alpha/eval/benchmarks/{benchmark_id}/evaluations", json={
                "input_rows": input_rows,
                "scoring_functions": scoring_functions,
                "benchmark_config": benchmark_config
            })
            response.raise_for_status()
            return response.json()

    def get_job_status(self, benchmark_id: str, job_id: str) -> Dict:
        with self._get_client() as client:
            response = client.get(f"{self.base_url}/alpha/eval/benchmarks/{benchmark_id}/jobs/{job_id}")
            response.raise_for_status()
            return response.json()

    def get_job_result(self, benchmark_id: str, job_id: str) -> Dict:
        response = self.client.get(f"{self.base_url}/alpha/eval/benchmarks/{benchmark_id}/jobs/{job_id}/result")
        response.raise_for_status()
        return response.json()


# ============================================================================
# Test Data & Tools
# ============================================================================

def create_tool_calling_dataset() -> List[Dict[str, Any]]:
    """Dataset for tool calling evaluation (eval/question-answer format)."""
    return [
        {"question": "What is 25 * 17 + 42?", "answer": "calculate", "expected_tool": "calculate"},
        {"question": "What's the weather in San Francisco?", "answer": "get_weather", "expected_tool": "get_weather"},
        {"question": "Search for latest AI news", "answer": "web_search", "expected_tool": "web_search"},
        {"question": "Calculate sqrt(144)", "answer": "calculate", "expected_tool": "calculate"},
        {"question": "Temperature in Tokyo?", "answer": "get_weather", "expected_tool": "get_weather"}
    ]


def get_tools():
    """Tool definitions for evaluation."""
    return [
        {
            "type": "function",
            "name": "calculate",
            "description": "Perform mathematical calculations",
            "parameters": {
                "type": "object",
                "properties": {"expression": {"type": "string", "description": "Math expression"}},
                "required": ["expression"]
            }
        },
        {
            "type": "function",
            "name": "get_weather",
            "description": "Get current weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "City name"},
                    "units": {"type": "string", "enum": ["celsius", "fahrenheit"]}
                },
                "required": ["location"]
            }
        },
        {
            "type": "function",
            "name": "web_search",
            "description": "Search the web",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "Search query"}},
                "required": ["query"]
            }
        }
    ]


# ============================================================================
# Custom Scoring
# ============================================================================

def score_tool_calling_accuracy(rows: List[Dict], expected_tool_key: str = "expected_tool") -> Dict:
    """Custom scoring function for tool calling accuracy."""
    correct = 0
    total = len(rows)
    score_rows = []

    for row in rows:
        expected = row.get(expected_tool_key)
        actual = row.get("actual_tool", expected)  # Extract from model response
        is_correct = (expected == actual)
        if is_correct:
            correct += 1
        score_rows.append({
            "expected_tool": expected,
            "actual_tool": actual,
            "correct": is_correct,
            "score": 1.0 if is_correct else 0.0
        })

    accuracy = correct / total if total > 0 else 0.0
    return {
        "score_rows": score_rows,
        "aggregated_results": {"accuracy": accuracy, "correct": correct, "total": total}
    }


# ============================================================================
# Main Demo
# ============================================================================

def main():
    print(colored("="*80, "yellow"))
    print(colored("Llama Stack Evaluation APIs Demo", "yellow", attrs=["bold"]))
    print(colored("="*80, "yellow"))

    llama_stack_url = f"http://localhost:{os.environ.get('LLAMA_STACK_PORT', '8321')}"
    model_id = os.environ.get("INFERENCE_MODEL", "openai/gpt-4o")

    print(f"\nConfig: {llama_stack_url} | Model: {model_id}\n")

    openai_client = OpenAI(base_url=f"{llama_stack_url}/v1", api_key="not-needed")
    eval_client = LlamaStackEvalClient(llama_stack_url)

    # List existing resources
    print(colored("STEP 0: List Resources", "cyan", attrs=["bold"]))
    try:
        datasets = eval_client.list_datasets()
        scoring_fns = eval_client.list_scoring_functions()
        benchmarks = eval_client.list_benchmarks()
        print(f"Datasets: {len(datasets)} | Scoring Functions: {len(scoring_fns)} | Benchmarks: {len(benchmarks)}\n")
    except Exception as e:
        print(f"Could not list resources: {e}\n")

    # Register dataset
    print(colored("STEP 1: Register Dataset", "cyan", attrs=["bold"]))
    dataset_id = f"tool_calling_eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    dataset_rows = create_tool_calling_dataset()
    print(f"Dataset: {dataset_id} ({len(dataset_rows)} rows)")

    try:
        eval_client.register_dataset(dataset_id, dataset_rows, purpose="eval/question-answer")
        print(colored("✅ Registered\n", "green"))
    except Exception as e:
        print(colored(f"⚠️  {e}\n", "yellow"))

    # Register scoring functions
    print(colored("STEP 2: Use Scoring Functions", "cyan", attrs=["bold"]))

    # Use built-in scoring functions (already registered)
    scoring_fn_exact = "basic::equality"  # Built-in exact match
    scoring_fn_judge = "llm-as-judge::base"  # Built-in LLM-as-judge

    print(colored(f"✅ Using: {scoring_fn_exact} (exact match)", "green"))
    print(colored(f"✅ Using: {scoring_fn_judge} (llm-as-judge)", "green"))
    print()

    # Register benchmark
    print(colored("STEP 3: Register Benchmark", "cyan", attrs=["bold"]))
    benchmark_id = f"tool_calling_benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        eval_client.register_benchmark(benchmark_id, dataset_id, [scoring_fn_exact, scoring_fn_judge])
        print(colored("✅ Registered\n", "green"))
    except Exception as e:
        print(colored(f"⚠️  {e}\n", "yellow"))

    # Run inference
    print(colored("STEP 4: Run Inference", "cyan", attrs=["bold"]))
    tools = get_tools()
    results = []

    for i, row in enumerate(dataset_rows, 1):
        print(f"[{i}/{len(dataset_rows)}] {row['question'][:50]}...")

        try:
            start_time = time.time()
            response = openai_client.responses.create(
                model=model_id,
                input=row['question'],
                instructions="Use the appropriate tool.",
                tools=tools,
                tool_choice="auto",
                stream=False
            )
            latency_ms = (time.time() - start_time) * 1000

            actual_tool = None
            if hasattr(response, 'output'):
                for item in response.output:
                    if hasattr(item, 'type') and item.type == "function_call":
                        actual_tool = item.name
                        break

            is_correct = (actual_tool == row['expected_tool'])
            results.append({
                **row,
                "actual_tool": actual_tool,
                "correct": is_correct,
                "latency_ms": latency_ms
            })
            status = "✅" if is_correct else "❌"
            print(f"  {status} Expected: {row['expected_tool']}, Got: {actual_tool} ({latency_ms:.0f}ms)")
        except Exception as e:
            print(colored(f"  ❌ Error: {e}", "red"))
            results.append({**row, "actual_tool": None, "correct": False, "error": str(e)})

    # Score results
    print(f"\n{colored('STEP 5: Score Results', 'cyan', attrs=['bold'])}")

    # 5a. Custom exact match scoring
    scoring_result = score_tool_calling_accuracy(results)
    accuracy_pct = scoring_result['aggregated_results']['accuracy'] * 100
    avg_latency = sum(r.get('latency_ms', 0) for r in results) / len(results)

    print(f"Exact Match Accuracy: {colored(f'{accuracy_pct:.1f}%', 'yellow')} ({scoring_result['aggregated_results']['correct']}/{scoring_result['aggregated_results']['total']})")
    print(f"Avg Latency: {avg_latency:.0f}ms")

    # 5b. LLM-as-judge scoring (using default params)
    print(f"\nRunning LLM-as-judge scoring...")
    try:
        # Prepare rows - LLM-as-judge expects specific column names
        judge_rows = []
        for r in results:
            judge_rows.append({
                "input_query": r['question'],
                "expected_answer": r['expected_tool'],
                "generated_answer": r.get('actual_tool', 'none')
            })

        # Score with LLM-as-judge (use None to use default params)
        judge_response = eval_client.score_rows(
            input_rows=judge_rows,
            scoring_functions={
                scoring_fn_judge: None  # Use default LLM-as-judge params
            }
        )

        # Extract and display results
        if 'results' in judge_response and scoring_fn_judge in judge_response['results']:
            result = judge_response['results'][scoring_fn_judge]
            if 'aggregated_results' in result:
                print(f"LLM-as-Judge Results: {result['aggregated_results']}")
                scoring_result['llm_judge'] = {
                    "aggregated_results": result['aggregated_results'],
                    "score_rows": result.get('score_rows', [])
                }
    except Exception as e:
        print(colored(f"⚠️  LLM-as-judge scoring failed: {e}", "yellow"))

    # Save results
    output_file = f"llama_stack_eval_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump({
            "dataset_id": dataset_id,
            "benchmark_id": benchmark_id,
            "model_id": model_id,
            "results": results,
            "scoring": scoring_result,
            "timestamp": datetime.now().isoformat()
        }, f, indent=2)

    print(f"\n{colored('✅ Complete!', 'green', attrs=['bold'])}")
    print(f"Results: {output_file}")
    print(f"\nArchitecture: Dataset → Scoring Function → Benchmark → Eval Job → Results")
    print(f"Next: curl http://localhost:8321/beta/datasets")


if __name__ == "__main__":
    main()

