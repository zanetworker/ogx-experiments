#!/usr/bin/env python3
"""Multi-Model RFE Improvement: Compare how many iterations each model needs.

Runs the same bad RFEs through every available model and tracks:
- Original score (before)
- Score per iteration (improvement curve)
- Final score (after)
- Iterations needed to reach threshold
- Per-criterion breakdown at each step

Produces a comparison table and MLFlow data for the blog post.

Usage:
    OGX_PORT=8321 python outcome-loops/run_rfe_multimodel.py
    SCORE_THRESHOLD=9 python outcome-loops/run_rfe_multimodel.py
"""

import os
import sys
import json
import time
from datetime import datetime

import mlflow
from openai import OpenAI

OGX_PORT = os.getenv("OGX_PORT", "8321")
OGX_BASE_URL = os.getenv("OGX_BASE_URL", f"http://localhost:{OGX_PORT}/v1")
JUDGE_MODEL = os.getenv("JUDGE_MODEL", "openai/gpt-4.1-mini")
MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "4"))
SCORE_THRESHOLD = int(os.getenv("SCORE_THRESHOLD", "8"))
MLFLOW_DB = os.getenv("MLFLOW_DB", "sqlite:///outcome_loops.db")

client = OpenAI(base_url=OGX_BASE_URL, api_key=os.getenv("OPENAI_API_KEY", "not-needed"))

AGENT_MODELS = [
    "qwen/qwen35-9b",
    "scout/llama-4-scout-17b-16e-w4a16",
    "gemma/gemma4",
    "nemotron/nemotron-cascade-2-30b",
    "kimi/kimi-k2-6",
]

RFE_RUBRIC = """Score this RFE 0-2 on each criterion (/10 total).

1. WHAT (0-2): Clear, specific customer need?
   0=vague/unclear, 1=ambiguous, 2=clear and specific

2. WHY (0-2): Named customers, revenue impact, market data?
   0=no justification or circular reasoning
   1=generic segments, competitive gaps (plausible but no named customers)
   2=named accounts, specific revenue/deal impact, strategic investment with causal chain

3. HOW (0-2): Leaves architecture to engineering?
   0=mandates internal architecture, names specific databases/frameworks/repos
   1=leans into implementation but doesn't fully mandate
   2=describes the need without prescribing architecture

4. NOT_TASK (0-2): Business need, not activity/chore?
   0=reads like a task/ticket ("implement X", "add Y", "migrate Z")
   1=borderline
   2=clear business need framed from customer perspective

5. RIGHT_SIZED (0-2): Maps to ~1 feature?
   0=bundles 3+ independent features
   1=bundles 1-2 separable features
   2=focused single need

Return ONLY valid JSON:
{"what": <0-2>, "why": <0-2>, "how": <0-2>, "not_task": <0-2>, "right_sized": <0-2>, "total": <0-10>, "justification": "<per-criterion feedback>"}
"""

BAD_RFES = [
    {
        "name": "vague_no_evidence",
        "weakness": "Vague WHAT, no WHY",
        "text": """## Summary
We need better GPU support in RHOAI.

## Description
Customers want better GPU things. GPUs are important for AI. We should improve our GPU support to be competitive. Other vendors have good GPU support. We need to catch up.

## Acceptance Criteria
- Better GPU support
- Improved performance
- Customer satisfaction increased"""
    },
    {
        "name": "prescriptive_architecture",
        "weakness": "Prescribes HOW",
        "text": """## Summary
Implement Redis-based session caching for inference endpoints using Envoy ext_proc filter

## Description
We need to add Redis Cluster 7.2 as a session cache between the Envoy gateway and KServe inference pods. The implementation should use the ext_proc filter in Envoy to intercept requests, hash the session ID using consistent hashing (Ketama algorithm), and store conversation state in Redis with a 30-minute TTL.

The Redis deployment should use the Bitnami Helm chart with sentinel mode enabled for HA. Data should be serialized using Protocol Buffers (proto3 schema attached). The ext_proc filter should be written in Go using the go-control-plane library.

## Acceptance Criteria
- Redis Cluster 7.2 deployed via Bitnami Helm chart
- Envoy ext_proc filter written in Go
- Ketama consistent hashing for session distribution
- Proto3 serialization for session data
- 30-minute TTL on all session keys"""
    },
    {
        "name": "task_not_need",
        "weakness": "Task, not business need",
        "text": """## Summary
Migrate model registry database from PostgreSQL 14 to PostgreSQL 16

## Description
We need to upgrade the PostgreSQL version used by the model registry from 14 to 16. PostgreSQL 14 reaches end of life in November 2026. The migration should use pg_upgrade with the --link option for speed. We also need to update the connection pooler from PgBouncer 1.18 to 1.21.

Run pg_dump on the existing database, test the restore on a staging instance, then schedule a maintenance window for the production cutover.

## Acceptance Criteria
- PostgreSQL upgraded from 14 to 16
- PgBouncer upgraded from 1.18 to 1.21
- Migration tested on staging
- Zero data loss during cutover"""
    },
    {
        "name": "bundled_scope",
        "weakness": "Bundles 3+ features",
        "text": """## Summary
End-to-end agent platform with observability, security, and marketplace

## Description
We need to build a complete agent platform that includes:

1. Agent Marketplace: A catalog where users can browse, publish, and install pre-built agents. Includes ratings, reviews, version management, and a billing system for paid agents.

2. Agent Observability: End-to-end tracing for agent runs including every model call, tool invocation, and decision point. Integration with OpenTelemetry, per-run cost tracking, and anomaly detection on agent behavior.

3. Agent Security: Sandboxed execution environment for agents with network isolation, file system restrictions, credential vaulting, and audit logging. Includes a policy engine for defining what agents can and cannot access.

4. Agent Testing Framework: A CI/CD pipeline for testing agents before deployment, including regression tests, performance benchmarks, and safety evaluations.

## Acceptance Criteria
- Agent marketplace with 50+ pre-built agents
- Full OTEL tracing for all agent runs
- Sandboxed execution with policy engine
- Automated testing pipeline with safety checks"""
    },
]

IMPROVE_PROMPT = """You are a senior Product Manager improving an RFE (Request for Enhancement) for Red Hat OpenShift AI.

You will receive a low-quality RFE and feedback from a quality assessor. Rewrite the RFE to fix the identified weaknesses while keeping the core intent.

Rules:
- Describe WHAT the customer needs clearly and specifically
- Add business justification with named customers and business impact
- Do NOT prescribe internal architecture (leave HOW to engineering)
- Frame as a business need, not a task or activity
- Keep it focused on ONE feature (if the original bundles multiple, pick the most important one)

Output ONLY the improved RFE with sections: Summary, Business Justification, Description, Acceptance Criteria."""


def judge_rfe(rfe_text: str) -> dict:
    """Judge an RFE against the rubric."""
    prompt = f"## RFE to evaluate\n{rfe_text}\n\n{RFE_RUBRIC}"
    kwargs = {
        "model": JUDGE_MODEL,
        "messages": [
            {"role": "system", "content": "You are an expert RFE assessor. Return only valid JSON."},
            {"role": "user", "content": prompt},
        ],
    }
    if not any(x in JUDGE_MODEL for x in ["gpt-5", "o3", "o4", "o1"]):
        kwargs["temperature"] = 0.0
    response = client.chat.completions.create(**kwargs)
    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    try:
        result = json.loads(raw)
        if "total" not in result:
            result["total"] = sum(result.get(k, 0) for k in ["what", "why", "how", "not_task", "right_sized"])
        return result
    except json.JSONDecodeError:
        return {"what": 0, "why": 0, "how": 0, "not_task": 0, "right_sized": 0,
                "total": 0, "justification": f"Parse error: {raw[:200]}"}


def run_single(model: str, bad_rfe: dict) -> dict:
    """Run one model on one bad RFE with outcome loop."""
    rfe_text = bad_rfe["text"]
    short_model = model.split("/")[-1]

    with mlflow.start_run(run_name=f"{short_model}--{bad_rfe['name']}"):
        mlflow.log_param("agent_model", model)
        mlflow.log_param("judge_model", JUDGE_MODEL)
        mlflow.log_param("rfe_name", bad_rfe["name"])
        mlflow.log_param("weakness", bad_rfe["weakness"])
        mlflow.log_param("threshold", f"{SCORE_THRESHOLD}/10")
        mlflow.log_param("max_iterations", MAX_ITERATIONS)

        # Score original
        original_eval = judge_rfe(rfe_text)
        original_score = original_eval.get("total", 0)
        original_bd = {k: original_eval.get(k, 0) for k in ["what", "why", "how", "not_task", "right_sized"]}

        print(f"      Original: {original_score}/10 "
              f"(W:{original_bd['what']} Y:{original_bd['why']} H:{original_bd['how']} "
              f"T:{original_bd['not_task']} S:{original_bd['right_sized']})")

        mlflow.log_metric("original_score", original_score)
        for k, v in original_bd.items():
            mlflow.log_metric(f"original_{k}", v)
        mlflow.log_text(rfe_text, "original_rfe.md")

        # Improvement loop
        messages = [
            {"role": "system", "content": IMPROVE_PROMPT},
            {"role": "user", "content": (
                f"Here is a low-quality RFE to improve:\n\n{rfe_text}\n\n"
                f"Quality assessment ({original_score}/10): {original_eval.get('justification', '')}\n\n"
                f"Please rewrite this RFE to fix the weaknesses."
            )},
        ]

        score_history = [original_score]
        score = original_score
        output = rfe_text
        scores_bd = original_bd

        for iteration in range(MAX_ITERATIONS):
            t0 = time.time()
            print(f"      Iter {iteration + 1}: ", end="", flush=True)

            try:
                response = client.chat.completions.create(model=model, messages=messages)
                output = response.choices[0].message.content
            except Exception as e:
                print(f"ERROR: {e}")
                mlflow.log_param("outcome", f"error")
                return {"model": model, "rfe": bad_rfe["name"], "original": original_score,
                        "final": score, "improvement": score - original_score,
                        "iterations": iteration + 1, "outcome": "error",
                        "score_history": score_history}

            agent_time = time.time() - t0
            mlflow.log_text(output, f"improved_iteration_{iteration}.md")
            mlflow.log_metric(f"agent_latency_s_{iteration}", round(agent_time, 1))

            eval_result = judge_rfe(output)
            score = eval_result.get("total", 0)
            justification = eval_result.get("justification", "")
            scores_bd = {k: eval_result.get(k, 0) for k in ["what", "why", "how", "not_task", "right_sized"]}
            score_history.append(score)

            mlflow.log_metric(f"score_iteration_{iteration}", score)
            mlflow.log_metric(f"improvement_iteration_{iteration}", score - original_score)
            for k, v in scores_bd.items():
                mlflow.log_metric(f"{k}_iter_{iteration}", v)
            mlflow.log_text(justification, f"justification_iteration_{iteration}.md")

            print(f"{score}/10 (+{score - original_score}) "
                  f"W:{scores_bd['what']} Y:{scores_bd['why']} H:{scores_bd['how']} "
                  f"T:{scores_bd['not_task']} S:{scores_bd['right_sized']} "
                  f"({agent_time:.1f}s)")

            if score >= SCORE_THRESHOLD:
                mlflow.log_metric("final_score", score)
                mlflow.log_metric("total_improvement", score - original_score)
                mlflow.log_metric("iterations_needed", iteration + 1)
                mlflow.log_param("outcome", "satisfied")
                mlflow.log_param("score_history", json.dumps(score_history))
                mlflow.log_text(output, "final_rfe.md")
                return {"model": model, "rfe": bad_rfe["name"], "original": original_score,
                        "final": score, "improvement": score - original_score,
                        "iterations": iteration + 1, "outcome": "satisfied",
                        "score_history": score_history}

            weak = [f"- {k.upper()}: {v}/2" for k, v in scores_bd.items() if v < 2]
            messages.append({"role": "assistant", "content": output})
            messages.append({
                "role": "user",
                "content": (
                    f"Score: {score}/10. Below {SCORE_THRESHOLD}.\n"
                    f"Weak:\n" + "\n".join(weak) + f"\n\n"
                    f"Feedback: {justification}\n\nRevise again."
                ),
            })

        mlflow.log_metric("final_score", score)
        mlflow.log_metric("total_improvement", score - original_score)
        mlflow.log_metric("iterations_needed", MAX_ITERATIONS)
        mlflow.log_param("outcome", "max_iterations_reached")
        mlflow.log_param("score_history", json.dumps(score_history))
        mlflow.log_text(output, "final_rfe.md")
        return {"model": model, "rfe": bad_rfe["name"], "original": original_score,
                "final": score, "improvement": score - original_score,
                "iterations": MAX_ITERATIONS, "outcome": "max_iterations_reached",
                "score_history": score_history}


def main():
    mlflow.set_tracking_uri(MLFLOW_DB)
    mlflow.set_experiment("rfe-multimodel-comparison")

    print("=" * 70)
    print("MULTI-MODEL RFE IMPROVEMENT COMPARISON")
    print(f"  OGX:       {OGX_BASE_URL}")
    print(f"  Models:    {AGENT_MODELS}")
    print(f"  Judge:     {JUDGE_MODEL}")
    print(f"  Threshold: {SCORE_THRESHOLD}/10")
    print(f"  Max iters: {MAX_ITERATIONS}")
    print(f"  Bad RFEs:  {len(BAD_RFES)}")
    print(f"  Total runs: {len(AGENT_MODELS) * len(BAD_RFES)}")
    print("=" * 70)

    all_results = []

    for model in AGENT_MODELS:
        for bad_rfe in BAD_RFES:
            print(f"\n  [{model}] {bad_rfe['name']} ({bad_rfe['weakness']})")
            result = run_single(model, bad_rfe)
            all_results.append(result)

    # Summary tables
    print(f"\n\n{'=' * 90}")
    print("DETAILED RESULTS")
    print(f"{'=' * 90}")
    print(f"{'Model':<35} {'RFE':<25} {'Before':>7} {'After':>7} {'Delta':>7} {'Iters':>6} {'History'}")
    print("-" * 110)
    for r in all_results:
        delta = f"+{r['improvement']}" if r['improvement'] > 0 else str(r['improvement'])
        hist = " -> ".join(str(s) for s in r['score_history'])
        short = r['model'].split('/')[-1][:30]
        print(f"{short:<35} {r['rfe']:<25} {r['original']:>5}/10 {r['final']:>5}/10 {delta:>6} {r['iterations']:>5}  {hist}")

    # Per-model summary
    print(f"\n{'=' * 70}")
    print("PER-MODEL SUMMARY")
    print(f"{'=' * 70}")
    print(f"{'Model':<35} {'Avg Before':>10} {'Avg After':>10} {'Avg Delta':>10} {'Avg Iters':>10}")
    print("-" * 80)
    for model in AGENT_MODELS:
        model_results = [r for r in all_results if r['model'] == model]
        avg_before = sum(r['original'] for r in model_results) / len(model_results)
        avg_after = sum(r['final'] for r in model_results) / len(model_results)
        avg_delta = avg_after - avg_before
        avg_iters = sum(r['iterations'] for r in model_results) / len(model_results)
        short = model.split('/')[-1][:30]
        print(f"{short:<35} {avg_before:>8.1f}/10 {avg_after:>8.1f}/10 {f'+{avg_delta:.1f}':>9} {avg_iters:>9.1f}")

    print(f"\n\nMLFlow: mlflow ui --port 5001 --backend-store-uri {MLFLOW_DB}")
    print(f"Experiment: rfe-multimodel-comparison")


if __name__ == "__main__":
    main()
