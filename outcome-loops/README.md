# Outcome Loops: Self-Correcting Agent Quality Gates

Tests how well different models improve low-quality RFEs when given rubric feedback. Runs across all available OGX models, scores with a configurable judge, and logs everything to MLFlow.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Your Code (30 lines)                    │
│                                                             │
│   for iteration in range(max_iterations):                   │
│       output = call_agent(model, messages)     ──────┐      │
│       score  = call_judge(judge_model, output) ──┐   │      │
│       if score >= threshold: break               │   │      │
│       else: inject feedback, loop                │   │      │
└──────────────────────────────────────────────────┼───┼──────┘
                                                   │   │
                    ┌──────────────────────────────┘   │
                    │                                  │
              ┌─────▼─────┐                     ┌──────▼──────┐
              │   OGX     │                     │    OGX      │
              │  :8321    │                     │   :8321     │
              │           │                     │             │
              │ Judge call│                     │ Agent call  │
              └─────┬─────┘                     └──────┬──────┘
                    │                                  │
         ┌──────────┴──────────┐            ┌──────────┴──────────┐
         │  openai/gpt-5-mini  │            │  kimi/kimi-k2-6     │
         │  (OpenAI API)       │            │  gemma/gemma4        │
         │                     │            │  scout/llama-4-scout │
         │  Hosted judge       │            │  nemotron/30b        │
         └─────────────────────┘            │  qwen/qwen35-9b     │
                                            │                     │
                                            │  Self-hosted (vLLM) │
                                            └─────────────────────┘

              All calls go to the same OGX endpoint.
              OGX routes to the right backend by model name.

                    ┌─────────────┐
                    │   MLFlow    │
                    │   :5001     │
                    │             │
                    │ Metrics     │
                    │ Artifacts   │
                    │ Experiments │
                    └─────────────┘
              Every iteration logged: scores, outputs, justifications.
```

## Versions tested

| Component | Version |
|-----------|---------|
| MLFlow | 3.11.1 |
| OpenAI Python SDK | 2.28.0 |
| OGX (Llama Stack) | 0.2.x (running on localhost:8321) |
| Python | 3.11+ |
| Judge models | openai/gpt-4.1-mini, openai/gpt-5-mini |
| Agent models | kimi/kimi-k2-6, gemma/gemma4, scout/llama-4-scout-17b-16e-w4a16, nemotron/nemotron-cascade-2-30b, qwen/qwen35-9b |

## Setup

```bash
pip install mlflow>=3.11 openai>=2.28 pandas

# Start MLFlow UI (separate terminal)
mlflow ui --port 5001 --backend-store-uri sqlite:///outcome_loops.db
```

## Run

```bash
# All models, gpt-5-mini judge, strict rubric (threshold 18/20)
OGX_PORT=8321 JUDGE_MODEL=openai/gpt-5-mini SCORE_THRESHOLD=18 python outcome-loops/run_rfe_multimodel.py

# Specific models only
AGENT_MODELS="kimi/kimi-k2-6,gemma/gemma4" python outcome-loops/run_rfe_multimodel.py

# Lenient judge for comparison
JUDGE_MODEL=openai/gpt-4.1-mini python outcome-loops/run_rfe_multimodel.py
```

## Key finding

Judge quality determines everything. With gpt-4.1-mini as judge, every model passes on iteration 1. With gpt-5-mini, models need 1-3 iterations and some regress on over-revision.

## View results

Open http://localhost:5001, look at the `rfe-multimodel-comparison` or `rfe-strict-rubric` experiment.

See [WALKTHROUGH.md](WALKTHROUGH.md) for a full explanation of every parameter, metric, and artifact.
