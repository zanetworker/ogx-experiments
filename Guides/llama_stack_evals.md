# Agentic Tools with Llama Stack Eval/Scoring/Dataset APIs

This demo showcases how to use **Llama Stack's built-in evaluation framework** for testing agentic tool calling with open source HuggingFace models.

## 🎯 What This Demonstrates

### 1. **DatasetIO API** - Dataset Management
- Create evaluation datasets programmatically
- Store test cases with expected outputs
- Iterate over dataset rows for evaluation
- Append results back to datasets

### 2. **Scoring API** - Custom Metrics
- Define custom scoring functions
- Score individual rows or batches
- Get aggregated metrics (accuracy, pass rate, etc.)
- Save scoring results for analysis

### 3. **Eval API** - Automated Evaluations
- Run benchmark evaluations as jobs
- Track job status and progress
- Retrieve evaluation results
- Support for both model and agent candidates

### 4. **Integration with Agentic Tools**
- Function calling with HuggingFace models
- Tool selection accuracy testing
- Performance metrics (latency, throughput)
- Real-world tool calling scenarios

### 5. **Observability**
- Automatic telemetry tracking
- OpenTelemetry export support
- Integration with Llama Stack's built-in monitoring

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Your Application                          │
│  (7-agentic-tools-with-llama-stack-evals.py)                │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   Llama Stack APIs                           │
├─────────────────────────────────────────────────────────────┤
│  DatasetIO API    │  Scoring API   │   Eval API             │
│  - create dataset │  - score rows  │  - run_eval()          │
│  - append rows    │  - score batch │  - job_status()        │
│  - iterrows()     │  - custom fns  │  - job_result()        │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              HuggingFace Models (via Inference API)          │
│  - Llama 3.2, Llama 3.3, etc.                               │
│  - Tool calling support                                      │
│  - Function execution                                        │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

```bash
# 1. Start Llama Stack server
export LLAMA_STACK_PORT=8080
export INFERENCE_MODEL="meta-llama/Llama-3.2-3B-Instruct"

# 2. Install dependencies
pip install openai termcolor httpx
```

### Run the Demo

```bash
python 7-agentic-tools-with-llama-stack-evals.py
```

## 📊 What Gets Evaluated

The demo tests tool calling accuracy across multiple scenarios:

| Test Case | Expected Tool | Description |
|-----------|--------------|-------------|
| "What is 25 * 17 + 42?" | `calculate` | Math calculation |
| "What's the weather in San Francisco?" | `get_weather` | Weather lookup |
| "Search for latest AI news" | `web_search` | Web search |
| "Calculate the square root of 144" | `calculate` | Complex math |
| "What's the temperature in Tokyo?" | `get_weather` | International weather |

## 📈 Metrics Collected

### Accuracy Metrics
- **Tool Selection Accuracy**: % of queries where correct tool was chosen
- **Pass Rate**: % of successful tool calls
- **Error Rate**: % of failed tool calls

### Performance Metrics
- **Average Latency**: Mean response time per query
- **P95 Latency**: 95th percentile response time
- **Throughput**: Queries processed per second

### Quality Metrics
- **Output Correctness**: Does output contain expected information?
- **Tool Parameter Accuracy**: Are tool parameters correctly extracted?

## 🔧 API Usage Examples

### 1. DatasetIO API - Create Dataset

```python
from llama_stack_eval_client import LlamaStackEvalClient

client = LlamaStackEvalClient("http://localhost:8080")

# Create evaluation dataset
dataset_rows = [
    {
        "input_query": "What is 2 + 2?",
        "expected_tool": "calculate",
        "expected_output": "4"
    }
]

client.create_dataset("my_eval_dataset", dataset_rows)
```

### 2. Scoring API - Score Results

```python
# Score individual rows
scoring_result = client.score_rows(
    input_rows=[
        {"expected": "calculate", "actual": "calculate"},
        {"expected": "weather", "actual": "search"}
    ],
    scoring_functions={
        "accuracy": None  # Use default accuracy scorer
    }
)

print(f"Accuracy: {scoring_result['results']['accuracy']['aggregated_results']['accuracy']}")
```

### 3. Eval API - Run Benchmark

```python
# Run evaluation job
job = client.run_eval(
    benchmark_id="tool_calling_benchmark",
    benchmark_config={
        "eval_candidate": {
            "type": "model",
            "model": "meta-llama/Llama-3.2-3B-Instruct",
            "sampling_params": {"temperature": 0.7}
        },
        "scoring_params": {
            "accuracy": {}
        }
    }
)

# Check job status
status = client.get_job_status("tool_calling_benchmark", job["job_id"])
print(f"Status: {status['status']}")

# Get results when complete
results = client.get_job_result("tool_calling_benchmark", job["job_id"])
```

## 📁 Output Files

The demo generates:

1. **`llama_stack_eval_results_TIMESTAMP.json`**
   - Complete evaluation results
   - Per-query metrics
   - Aggregated statistics
   - Model and dataset metadata

Example output:
```json
{
  "dataset_id": "tool_calling_eval_20241028_143022",
  "model_id": "meta-llama/Llama-3.2-3B-Instruct",
  "results": [
    {
      "input_query": "What is 25 * 17 + 42?",
      "expected_tool": "calculate",
      "actual_tool": "calculate",
      "correct": true,
      "latency_ms": 234.5
    }
  ],
  "scoring": {
    "aggregated_results": {
      "accuracy": 0.95,
      "correct": 19,
      "total": 20
    }
  }
}
```

## 🔍 Observability Integration

All evaluation runs are automatically tracked by Llama Stack's telemetry system.

Telemetry data is stored in the Llama Stack database and can be accessed via the Telemetry API:

```bash
# Check telemetry configuration in your run.yaml
grep -A 10 "telemetry:" experiments/ollama-setup/ollama-stack-run.yaml

# Telemetry is automatically enabled for all API calls
# Data includes: traces, spans, metrics for inference, tool calls, and evaluations
```

## 🎓 Advanced Usage

### Custom Scoring Functions

You can implement custom scoring functions for domain-specific metrics:

```python
def score_tool_calling_accuracy(rows, expected_tool_key="expected_tool"):
    """Custom scorer for tool calling accuracy."""
    correct = sum(1 for r in rows if r.get("actual_tool") == r.get(expected_tool_key))
    total = len(rows)
    
    return {
        "score_rows": [
            {"correct": r.get("actual_tool") == r.get(expected_tool_key)}
            for r in rows
        ],
        "aggregated_results": {
            "accuracy": correct / total if total > 0 else 0.0,
            "correct": correct,
            "total": total
        }
    }
```

### Batch Evaluation

For large-scale evaluations:

```python
# Score entire dataset in batch
result = client.score_batch(
    dataset_id="large_eval_dataset",
    scoring_functions={
        "accuracy": None,
        "latency": {"threshold_ms": 500}
    },
    save_results_dataset=True  # Save results as new dataset
)
```

## 🆚 Comparison: Custom vs Llama Stack APIs

| Feature | Custom Eval (Demo 6) | Llama Stack APIs (Demo 7) |
|---------|---------------------|---------------------------|
| Dataset Management | Manual JSON files | DatasetIO API ✅ |
| Scoring | Custom code | Scoring API ✅ |
| Job Management | Manual tracking | Eval API with jobs ✅ |
| Scalability | Limited | Production-ready ✅ |
| Integration | Standalone | Full Llama Stack ecosystem ✅ |
| Observability | Basic logging | Built-in telemetry ✅ |

## 🔗 Related Resources

- **Llama Stack Eval API**: `/llama_stack/apis/eval/eval.py`
- **Scoring API**: `/llama_stack/apis/scoring/scoring.py`
- **DatasetIO API**: `/llama_stack/apis/datasetio/datasetio.py`
- **Telemetry Tools**: `experiments/telemetry/`
- **Basic Tool Calling**: `experiments/3-responses-function-tools.py`

## 💡 Key Takeaways

1. **Use Llama Stack's native APIs** for production evaluations
2. **DatasetIO API** provides robust dataset management
3. **Scoring API** enables custom metrics and aggregations
4. **Eval API** supports automated benchmark runs with job tracking
5. **Built-in telemetry** gives you observability out of the box
6. **Works seamlessly** with open source HuggingFace models

## 🐛 Troubleshooting

### Dataset Creation Fails
```bash
# Check if datasets API is available
curl http://localhost:8080/datasets/list

# Verify DatasetIO is enabled in your Llama Stack config
```

### Scoring Returns Empty Results
```bash
# Ensure scoring functions are registered
curl http://localhost:8080/scoring-functions/list

# Check that input rows have required fields
```

### Eval Job Stuck
```bash
# Check job status
curl http://localhost:8080/eval/benchmarks/{benchmark_id}/jobs/{job_id}

# Cancel if needed
curl -X DELETE http://localhost:8080/eval/benchmarks/{benchmark_id}/jobs/{job_id}
```

## 📚 Next Steps

1. **Extend the dataset** with more complex tool calling scenarios
2. **Implement custom scoring functions** for your domain
3. **Register scoring functions** with Llama Stack
4. **Set up automated benchmarks** using the Eval API
5. **Export telemetry** to your observability platform
6. **Compare different models** using the same evaluation framework

