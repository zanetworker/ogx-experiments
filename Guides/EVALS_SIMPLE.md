# Simple Evaluation Guide

## Quick Start

```bash
# Run simple evaluation demo
LLAMA_STACK_PORT=8321 INFERENCE_MODEL="openai/gpt-4o" python 8-simple-evals-with-ragas.py
```

---

## What This Shows

### 1. Tool Calling Evaluation
- Tests if model calls the right tool
- Calculates accuracy
- **Result**: 100% accuracy (3/3 correct)

### 2. RAG Evaluation
- Tests answer quality
- Checks if answers are grounded in context
- **Metrics**: Accuracy, Groundedness

---

## The Two Approaches

### Approach 1: Llama Stack Eval APIs (Production)

**Use when**: Building production evaluation pipelines

**Components**:
```
Dataset → Scoring Function → Benchmark → Eval Job → Results
```

**Example**: See `7-agentic-tools-with-llama-stack-evals.py`

**Pros**:
- ✅ Reusable benchmarks
- ✅ Async evaluation jobs
- ✅ Built-in telemetry
- ✅ Standard schemas

**Cons**:
- ❌ More setup required
- ❌ Learning curve

---

### Approach 2: Simple Custom Scoring (Quick Tests)

**Use when**: Quick experiments, prototyping

**Example**: See `8-simple-evals-with-ragas.py`

**Pros**:
- ✅ Simple and fast
- ✅ Easy to understand
- ✅ Flexible

**Cons**:
- ❌ Not reusable
- ❌ Manual tracking
- ❌ No standardization

---

## RAGAS Metrics Explained

RAGAS provides 4 key metrics for RAG evaluation:

### 1. Faithfulness
**Question**: Is the answer grounded in the retrieved context?

**Example**:
- Context: "Paris is the capital of France"
- Answer: "Paris is the capital" → ✅ Faithful
- Answer: "London is the capital" → ❌ Not faithful

### 2. Answer Relevancy
**Question**: Does the answer address the question?

**Example**:
- Question: "What is the capital of France?"
- Answer: "Paris" → ✅ Relevant
- Answer: "France is a country in Europe" → ❌ Not relevant

### 3. Context Precision
**Question**: Are the retrieved contexts relevant to the question?

**Example**:
- Question: "What is PyTorch?"
- Context 1: "PyTorch is a deep learning framework" → ✅ Relevant
- Context 2: "Python is a programming language" → ❌ Not relevant

### 4. Context Recall
**Question**: Did we retrieve all relevant contexts?

**Example**:
- Question: "What is PyTorch?"
- Retrieved: "PyTorch is a framework" → ⚠️ Partial (missing "developed by Meta")
- Retrieved: "PyTorch is a framework developed by Meta" → ✅ Complete

---

## When to Use What

| Scenario | Use This |
|----------|----------|
| Quick prototype | Simple custom scoring |
| Production pipeline | Llama Stack Eval APIs |
| RAG evaluation | RAGAS metrics |
| Tool calling eval | Exact match scoring |
| LLM output quality | LLM-as-judge |

---

## Code Examples

### Simple Tool Calling Eval

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8321/v1", api_key="not-needed")

# Test case
test = {"question": "What is 2+2?", "expected_tool": "calculate"}

# Run inference
response = client.responses.create(
    model="openai/gpt-4o",
    input=test['question'],
    tools=[{"type": "function", "name": "calculate", ...}]
)

# Check result
actual_tool = response.output[0].name  # Extract tool called
correct = (actual_tool == test['expected_tool'])
print(f"Accuracy: {correct}")
```

### Simple RAG Eval

```python
# Test case
test = {
    "question": "What is the capital of France?",
    "answer": "The capital of France is Paris.",
    "ground_truth": "Paris"
}

# Simple metric
correct = test['ground_truth'].lower() in test['answer'].lower()
print(f"Accuracy: {correct}")
```

### RAGAS Eval (Python 3.9+)

```python
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy
from datasets import Dataset

data = {
    "question": ["What is the capital of France?"],
    "answer": ["Paris"],
    "contexts": [["Paris is the capital of France."]],
    "ground_truth": ["Paris"]
}

dataset = Dataset.from_dict(data)
result = evaluate(dataset, metrics=[faithfulness, answer_relevancy])
print(result)
```

---

## Files Overview

| File | Purpose | Complexity |
|------|---------|------------|
| `8-simple-evals-with-ragas.py` | Simple examples | ⭐ Easy |
| `7-agentic-tools-with-llama-stack-evals.py` | Full Llama Stack APIs | ⭐⭐⭐ Advanced |
| `@llama_stack_evals.md` | Complete documentation | 📚 Reference |
| `EVALS_SUMMARY.md` | Quick reference | 📋 Cheatsheet |

---

## Next Steps

1. **Run the simple demo**: `python 8-simple-evals-with-ragas.py`
2. **Try RAGAS** (if Python 3.9+): `pip install ragas datasets`
3. **Explore Llama Stack APIs**: See `@llama_stack_evals.md`
4. **Build custom metrics**: Modify `8-simple-evals-with-ragas.py`

---

## Common Patterns

### Pattern 1: Exact Match
```python
score = 1.0 if expected == actual else 0.0
```

### Pattern 2: Contains Check
```python
score = 1.0 if expected in actual else 0.0
```

### Pattern 3: Similarity
```python
from difflib import SequenceMatcher
score = SequenceMatcher(None, expected, actual).ratio()
```

### Pattern 4: LLM-as-Judge
```python
prompt = f"Rate this answer from 1-10: {answer}"
response = llm.generate(prompt)
score = extract_score(response)
```

---

## Troubleshooting

### RAGAS not working?
- **Check Python version**: RAGAS requires Python 3.9+
- **Install**: `pip install ragas datasets`
- **Alternative**: Use manual RAG evaluation (shown in demo)

### Llama Stack connection refused?
- **Check server**: `lsof -ti:8321`
- **Start server**: `llama stack run experiments/ollama-setup/ollama-stack-run.yaml`
- **Check port**: `LLAMA_STACK_PORT=8321`

### Tool calling not working?
- **Check tool format**: Use Llama Stack format (not OpenAI format)
- **Example**: `{"type": "function", "name": "...", "parameters": {...}}`

---

## Resources

- **RAGAS Docs**: https://docs.ragas.io/
- **Llama Stack Eval Docs**: https://docs.llamastack.ai/advanced_apis/evaluation
- **Full Documentation**: See `@llama_stack_evals.md`
- **Quick Reference**: See `EVALS_SUMMARY.md`

