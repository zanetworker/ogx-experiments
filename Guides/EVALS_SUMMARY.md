# Llama Stack Evaluation Framework - Quick Summary

## The 4 APIs and How They Connect

```
┌──────────────────────────────────────────────────────────────────────┐
│                    LLAMA STACK EVALUATION FLOW                       │
└──────────────────────────────────────────────────────────────────────┘

1. DATASETS API (/beta/datasets)
   ↓
   Purpose: Store test cases
   Example: {"question": "What is 2+2?", "answer": "4"}
   
2. SCORING FUNCTIONS API (/v1/scoring_functions)
   ↓
   Purpose: Define how to score outputs
   Example: exact_match, llm-as-judge, regex_parser
   
3. BENCHMARKS API (/alpha/eval/benchmarks)
   ↓
   Purpose: Link dataset + scoring functions
   Example: Benchmark "math_eval" = dataset "math_questions" + scoring "exact_match"
   
4. EVAL API (/alpha/eval/benchmarks/{id}/jobs)
   ↓
   Purpose: Run model on benchmark, get scores
   Example: Run GPT-4o on "math_eval" → 95% accuracy
```

---

## Key Concepts

### Dataset
- **What**: Collection of test cases
- **Schema**: Defined by "purpose" (eval/question-answer, eval/messages-answer, etc.)
- **Source**: Rows, URI, HuggingFace, local file
- **Example**:
  ```json
  {
    "dataset_id": "tool_calling_eval",
    "purpose": "eval/question-answer",
    "rows": [
      {"question": "What is 2+2?", "answer": "4"},
      {"question": "Capital of France?", "answer": "Paris"}
    ]
  }
  ```

### Scoring Function
- **What**: Algorithm to evaluate model outputs
- **Types**:
  - **exact_match**: String equality (provider: basic)
  - **subset_of**: Check if expected ⊆ actual (provider: basic)
  - **llm-as-judge**: Use LLM to judge (provider: llm-as-judge)
  - **regex_parser**: Extract with regex (provider: basic)
- **Example**:
  ```json
  {
    "scoring_fn_id": "exact_match",
    "provider_id": "basic",
    "provider_scoring_fn_id": "exact_match"
  }
  ```

### Benchmark
- **What**: Named evaluation task = Dataset + Scoring Functions
- **Reusable**: Run same benchmark on different models
- **Example**:
  ```json
  {
    "benchmark_id": "tool_calling_accuracy",
    "dataset_id": "tool_calling_eval",
    "scoring_functions": ["exact_match"]
  }
  ```

### Eval Job
- **What**: Async task that runs model on benchmark
- **Config**: Model, sampling params, num_examples
- **Output**: Per-row scores + aggregated metrics
- **Example**:
  ```json
  {
    "benchmark_id": "tool_calling_accuracy",
    "benchmark_config": {
      "eval_candidate": {
        "type": "model",
        "model": "openai/gpt-4o",
        "sampling_params": {"temperature": 0.0}
      }
    }
  }
  ```

---

## Complete Flow Example

```python
from llama_stack_client import LlamaStackClient

client = LlamaStackClient(base_url="http://localhost:8321")

# 1. Register dataset
dataset = client.beta.datasets.register(
    dataset_id="my_eval",
    purpose="eval/question-answer",
    source={
        "type": "rows",
        "rows": [
            {"question": "What is 2+2?", "answer": "4"},
            {"question": "Capital of France?", "answer": "Paris"}
        ]
    }
)

# 2. Register scoring function
client.scoring_functions.register(
    scoring_fn_id="exact_match",
    provider_id="basic",
    provider_scoring_fn_id="exact_match"
)

# 3. Register benchmark
client.alpha.benchmarks.register(
    benchmark_id="my_benchmark",
    dataset_id="my_eval",
    scoring_functions=["exact_match"]
)

# 4. Run evaluation
job = client.alpha.eval.run_eval(
    benchmark_id="my_benchmark",
    benchmark_config={
        "eval_candidate": {
            "type": "model",
            "model": "openai/gpt-4o"
        }
    }
)

# 5. Get results
result = client.alpha.eval.get_job_result(
    benchmark_id="my_benchmark",
    job_id=job.job_id
)
print(result.aggregated_results)  # {"accuracy": 1.0}
```

---

## Dataset Purposes (Schemas)

| Purpose | Schema | Use Case |
|---------|--------|----------|
| `eval/question-answer` | `{question, answer}` | Simple Q&A |
| `eval/messages-answer` | `{messages[], answer}` | Multi-turn conversations |
| `post-training/messages` | `{messages[]}` | Fine-tuning data |

---

## Scoring Function Types

| Type | Provider | Description | Example |
|------|----------|-------------|---------|
| `exact_match` | basic | String equality | "Paris" == "Paris" → 1.0 |
| `subset_of` | basic | Expected ⊆ Actual | "A,B" ⊆ "A,B,C" → 1.0 |
| `llm_as_judge` | llm-as-judge | LLM judges quality | "Rate 1-10: ..." → 8.5 |
| `regex_parser_multiple_choice_answer` | basic | Extract MC answer | "Answer: (B)" → "B" |

---

## Eval Candidate Types

### Model Candidate
```python
{
    "type": "model",
    "model": "openai/gpt-4o",
    "sampling_params": {
        "temperature": 0.0,
        "max_tokens": 512
    },
    "system_message": "You are a helpful assistant."
}
```

### Agent Candidate
```python
{
    "type": "agent",
    "config": {
        "model": "meta-llama/Llama-3.3-70B-Instruct",
        "instructions": "You are a helpful assistant.",
        "toolgroups": ["builtin::websearch"],
        "tool_choice": "auto"
    }
}
```

---

## API Endpoints Reference

### Datasets API
```
POST   /beta/datasets              - Register dataset
GET    /beta/datasets              - List datasets
GET    /beta/datasets/{id}         - Get dataset
DELETE /beta/datasets/{id}         - Delete dataset
```

### Scoring Functions API
```
POST   /v1/scoring_functions       - Register scoring function
GET    /v1/scoring_functions       - List scoring functions
POST   /v1/scoring/score           - Score rows
POST   /v1/scoring/score-batch     - Score dataset
```

### Benchmarks API
```
POST   /alpha/eval/benchmarks      - Register benchmark
GET    /alpha/eval/benchmarks      - List benchmarks
GET    /alpha/eval/benchmarks/{id} - Get benchmark
```

### Eval API
```
POST   /alpha/eval/benchmarks/{id}/jobs              - Run eval job
GET    /alpha/eval/benchmarks/{id}/jobs/{job_id}    - Get job status
GET    /alpha/eval/benchmarks/{id}/jobs/{job_id}/result - Get results
POST   /alpha/eval/benchmarks/{id}/evaluations      - Evaluate rows (sync)
```

---

## Providers in Your Stack

From `experiments/ollama-setup/ollama-stack-run.yaml`:

```yaml
providers:
  eval:
  - provider_id: meta-reference
    provider_type: inline::meta-reference
  
  datasetio:
  - provider_id: huggingface
    provider_type: remote::huggingface
  - provider_id: localfs
    provider_type: inline::localfs
  
  scoring:
  - provider_id: basic
    provider_type: inline::basic
  - provider_id: llm-as-judge
    provider_type: inline::llm-as-judge
```

---

## Working Demo

**File**: `experiments/7-agentic-tools-with-llama-stack-evals.py`

**What it does**:
1. ✅ Registers tool calling evaluation dataset (5 test cases)
2. ✅ Registers exact_match scoring function
3. ✅ Creates benchmark linking dataset + scoring
4. ✅ Runs GPT-4o with tool calling on each test case
5. ✅ Scores results (100% accuracy in last run)
6. ✅ Saves results to JSON

**Run it**:
```bash
cd experiments
LLAMA_STACK_PORT=8321 INFERENCE_MODEL="openai/gpt-4o" python 7-agentic-tools-with-llama-stack-evals.py
```

**Output**:
```
📊 Evaluation Metrics:
   Accuracy: 100.0%
   Correct: 5/5
   Avg Latency: 1485ms

💾 Results saved to: experiments/llama_stack_eval_results_20251105_180526.json
```

---

## Key Differences: Custom Code vs Llama Stack

| Aspect | Custom Code | Llama Stack Eval |
|--------|-------------|------------------|
| **Dataset** | Manual CSV/JSON | Datasets API with versioning |
| **Scoring** | Custom functions | Registered scoring functions |
| **Reusability** | Hard to reuse | Benchmarks are reusable |
| **Async** | Manual threading | Built-in job system |
| **Telemetry** | Manual logging | Automatic tracking |
| **Standards** | Custom formats | Standard schemas |

---

## Pre-registered Benchmarks

Llama Stack includes reference benchmarks:

| Benchmark ID | Dataset | Scoring | Description |
|--------------|---------|---------|-------------|
| `meta-reference::mmmu` | MMMU | regex_parser | Multi-modal understanding |
| `meta-reference::simpleqa` | SimpleQA | llm-as-judge | Factual Q&A |
| `meta-reference::ifeval` | IFEval | basic | Instruction following |

---

## Next Steps

1. **Run demo**: See `experiments/7-agentic-tools-with-llama-stack-evals.py`
2. **Read full docs**: See `experiments/@llama_stack_evals.md`
3. **List resources**: `curl http://localhost:8321/beta/datasets | jq`
4. **Try LLM-as-judge**: Register and use LLM-based scoring
5. **Create custom benchmarks**: Define your own evaluation tasks

---

## References

- **Full Documentation**: `experiments/@llama_stack_evals.md`
- **Official Docs**: https://docs.llamastack.ai/advanced_apis/evaluation
- **Colab Notebook**: https://colab.research.google.com/drive/10CHyykee9j2OigaIcRv47BKG9mrNm0tJ
- **API Reference**: https://docs.llamastack.ai/references/evals_reference/

