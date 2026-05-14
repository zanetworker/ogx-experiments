# Token Tracking with Llama Stack Responses API

This guide shows you how to track token usage and monitor LLM costs using Llama Stack's built-in telemetry.

## 📋 Prerequisites

1. **Llama Stack server running** with telemetry enabled
2. **Python dependencies**: `openai`, `termcolor`

## ✅ Verify Telemetry is Enabled

Check your `ollama-setup/ollama-stack-run.yaml`:

```yaml
telemetry:
  enabled: true
```

✅ **Good news**: Your configuration already has telemetry enabled!

## 🚀 Quick Start

### Option 1: Minimal Example (Recommended to start)

Run the simplest example:

```bash
# Set the correct port and model
export LLAMA_STACK_PORT=8321
export INFERENCE_MODEL="ollama/llama3.2:latest"

python simple-token-tracking.py
```

**What it does:**
- Makes a single inference request
- Displays the response
- Shows token usage (prompt, completion, total)

**Code:**
```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8321/v1", api_key="not-needed")

response = client.responses.create(
    model="ollama/llama3.2:latest",
    input="What is Kubernetes?",
    stream=False
)

# Access token usage (Responses API uses input_tokens/output_tokens)
print(f"Input tokens:      {response.usage.input_tokens}")
print(f"Output tokens:     {response.usage.output_tokens}")
print(f"Total tokens:      {response.usage.total_tokens}")
```

### Option 2: Full Example with Cost Tracking

Run the comprehensive example:

```bash
python token-tracking-example.py
```

**What it does:**
- Makes multiple requests to different models
- Tracks cumulative token usage
- Calculates estimated costs
- Provides detailed summary

## 📊 Understanding Token Metrics

When telemetry is enabled, every response includes usage information:

```python
response.usage.prompt_tokens      # Tokens in your input
response.usage.completion_tokens  # Tokens in model's output
response.usage.total_tokens       # Sum of both
```

### Example Output:

```
======================================================================
Token Usage:
======================================================================
Input tokens:      29
Output tokens:     502
Total tokens:      531

Estimated cost:    $0.000531 (at $0.001/1K tokens)
```

## 💰 Cost Tracking

Calculate costs based on token usage:

```python
# Define your pricing (example rates)
COST_PER_1K_TOKENS = 0.001  # $0.001 per 1K tokens

# Calculate cost
total_tokens = response.usage.total_tokens
cost = (total_tokens / 1000) * COST_PER_1K_TOKENS

print(f"Cost: ${cost:.6f}")
```

## 🔧 Advanced: Production Monitoring

For production environments, use OpenTelemetry with Prometheus and Grafana.

### 1. Update your configuration

Add telemetry provider to `ollama-setup/ollama-stack-run.yaml`:

```yaml
providers:
  # ... your existing providers ...
  telemetry:
  - provider_id: meta-reference
    provider_type: inline::meta-reference
    config:
      service_name: "llama-stack-experiments"
      sinks: ['console', 'otel_trace', 'otel_metric']
      otel_exporter_otlp_endpoint: "http://localhost:4318"

telemetry:
  enabled: true
```

### 2. Start the telemetry stack

From the llama-stack repository (not experiments):

```bash
cd /path/to/llama-stack
./scripts/telemetry/setup_telemetry.sh
```

This launches:
- **Jaeger UI**: http://localhost:16686 (traces)
- **Prometheus**: http://localhost:9090 (metrics)
- **Grafana**: http://localhost:3000 (dashboards - admin/admin)
- **OTEL Collector**: http://localhost:4318 (endpoint)

### 3. Start Llama Stack with telemetry

```bash
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
export OTEL_SERVICE_NAME=llama-stack-experiments
llama stack run ollama-setup/ollama-stack-run.yaml
```

### 4. Query metrics in Prometheus

```promql
# Total tokens used
sum(llama_stack_tokens_total)

# Tokens per model
sum by (model_id) (llama_stack_tokens_total)

# Token usage rate over 5 minutes
rate(llama_stack_tokens_total[5m])

# Breakdown by provider
sum by (provider_id) (llama_stack_tokens_total)
```

## 📈 Available Metrics

Llama Stack automatically tracks these metrics:

| Metric Name | Type | Description |
|-------------|------|-------------|
| `llama_stack_prompt_tokens_total` | Counter | Input tokens |
| `llama_stack_completion_tokens_total` | Counter | Output tokens |
| `llama_stack_tokens_total` | Counter | Total tokens |

Each metric includes labels:
- `model_id`: The model used
- `provider_id`: The provider (ollama, vllm, openai, etc.)

## 🎯 Use Cases

### 1. Simple Cost Tracking

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8321/v1", api_key="unused")

total_cost = 0.0
COST_PER_1K = 0.001

for query in queries:
    response = client.responses.create(
        model="ollama/llama3.2:latest",
        input=query,
        stream=False
    )
    
    tokens = response.usage.total_tokens
    cost = (tokens / 1000) * COST_PER_1K
    total_cost += cost
    
    print(f"Query used {tokens} tokens (${cost:.4f})")

print(f"Total cost: ${total_cost:.4f}")
```

### 2. Budget Alerts

```python
BUDGET_LIMIT = 10.0  # $10 budget
current_cost = 0.0

response = client.responses.create(...)
current_cost += calculate_cost(response.usage.total_tokens)

if current_cost > BUDGET_LIMIT:
    print("⚠️  Budget limit exceeded!")
    # Send alert, stop processing, etc.
```

### 3. Model Comparison

```python
models = [
    "ollama/llama3.2:latest",
    "vllm-text/llama-4-scout-17b-16e-w4a16",
]

for model in models:
    response = client.responses.create(model=model, input=query)
    print(f"{model}: {response.usage.total_tokens} tokens")
```

## 🐛 Troubleshooting

### No usage information in response

**Problem:**
```python
if hasattr(response, 'usage') and response.usage:
    # This is None or missing
```

**Solution:**
1. Verify telemetry is enabled in `run.yaml`:
   ```yaml
   telemetry:
     enabled: true
   ```

2. Restart Llama Stack server

3. Check server logs for telemetry initialization

### Server returns 403 error

**Problem:**
```
openai.PermissionDeniedError: Error code: 403
```

**Solution:**
1. Check if Llama Stack server is running:
   ```bash
   curl http://localhost:8321/health
   ```

2. Verify the port matches your configuration:
   ```bash
   echo $LLAMA_STACK_PORT  # Should be 8321
   ```

3. Restart the server:
   ```bash
   llama stack run ollama-setup/ollama-stack-run.yaml
   ```

## 📚 Additional Resources

- **Telemetry Documentation**: `docs/docs/building_applications/telemetry.mdx`
- **Responses API Guide**: `docs/docs/building_applications/responses_vs_agents.mdx`
- **OpenTelemetry Setup**: `scripts/telemetry/setup_telemetry.sh`

## 💡 Best Practices

1. **Always check for usage data**:
   ```python
   if hasattr(response, 'usage') and response.usage:
       # Safe to access token counts
   ```

2. **Track costs in production**:
   - Use OpenTelemetry for real-time monitoring
   - Set up alerts for unusual usage spikes
   - Monitor token efficiency across models

3. **Optimize token usage**:
   - Use shorter prompts when possible
   - Choose appropriate models for the task
   - Monitor completion token counts

4. **Log token usage**:
   ```python
   import logging
   
   logging.info(f"Request used {response.usage.total_tokens} tokens")
   ```

## 🎉 Summary

✅ **Token tracking is automatic** when telemetry is enabled  
✅ **Access via `response.usage`** in every API response  
✅ **Use for cost tracking** and usage monitoring  
✅ **Scale to production** with OpenTelemetry + Prometheus + Grafana  

Start with `simple-token-tracking.py` and expand from there!

