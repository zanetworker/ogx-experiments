# Outcome Loops: Full Walkthrough

A complete explanation of how the experiment works, what each piece does, and how to read the results in MLFlow.

## What happens when you run the experiment

```
python outcome-loops/run_rfe_multimodel.py
```

The script does this for each model x bad-RFE combination:

1. **Scores the original bad RFE** by calling the judge model
2. **Asks the agent model to rewrite it**, passing the judge's feedback
3. **Scores the rewritten version** with the same judge
4. **If score >= threshold**, logs "satisfied" and moves on
5. **If score < threshold**, injects the judge's feedback and asks the agent to revise again
6. Repeats up to `MAX_ITERATIONS` times

## The code, line by line

### Configuration

```python
OGX_PORT = os.getenv("OGX_PORT", "8321")
OGX_BASE_URL = f"http://localhost:{OGX_PORT}/v1"
AGENT_MODEL = os.getenv("AGENT_MODEL", "kimi/kimi-k2-6")
JUDGE_MODEL = os.getenv("JUDGE_MODEL", "openai/gpt-4.1-mini")
MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "4"))
SCORE_THRESHOLD = int(os.getenv("SCORE_THRESHOLD", "8"))
```

- **OGX_BASE_URL**: Where OGX is running. All model calls go here.
- **AGENT_MODEL**: The model that writes/rewrites the RFE. This is what you are evaluating.
- **JUDGE_MODEL**: The model that scores the RFE. This is your evaluator. Should be a strong model.
- **MAX_ITERATIONS**: How many revision attempts before giving up.
- **SCORE_THRESHOLD**: Minimum score to pass. Out of 10 for the basic rubric, out of 20 for the strict rubric.

### The OpenAI client

```python
client = OpenAI(base_url=OGX_BASE_URL, api_key=os.getenv("OPENAI_API_KEY", "not-needed"))
```

One client, pointed at OGX. Every model call goes through this. OGX routes to the right backend based on the model name:
- `kimi/kimi-k2-6` routes to vLLM on your cluster
- `openai/gpt-5-mini` routes to OpenAI's API
- `gemma/gemma4` routes to vLLM on your cluster

### The judge function

```python
def judge_rfe(rfe_text: str) -> dict:
    prompt = f"## RFE to evaluate\n{rfe_text}\n\n{RFE_RUBRIC}"
    response = client.chat.completions.create(
        model=JUDGE_MODEL,
        messages=[
            {"role": "system", "content": "Expert RFE assessor. Return only valid JSON."},
            {"role": "user", "content": prompt},
        ],
    )
```

This sends the RFE text + the rubric to the judge model and asks for a JSON response with per-criterion scores. The rubric defines 5 criteria (basic) or 10 criteria (strict), each scored 0-2.

**What the judge returns:**

```json
{
  "what": 2,
  "why": 0,
  "how": 0,
  "not_task": 0,
  "right_sized": 2,
  "total": 4,
  "justification": "The RFE clearly identifies the need (WHAT: 2/2) but provides no customer evidence (WHY: 0/2), mandates Redis and Envoy internals (HOW: 0/2), reads as a task rather than a business need (NOT_TASK: 0/2), and is well-scoped (RIGHT_SIZED: 2/2)."
}
```

### The improvement loop

```python
messages = [
    {"role": "system", "content": IMPROVE_PROMPT},
    {"role": "user", "content": f"RFE to improve:\n\n{rfe_text}\n\nScore: {orig_score}/20\nFeedback: {justification}\n\nRewrite it."},
]

for iteration in range(MAX_ITERATIONS):
    response = client.chat.completions.create(model=model, messages=messages)
    output = response.choices[0].message.content

    eval_result = judge_rfe(output)
    score = eval_result.get("total", 0)

    if score >= SCORE_THRESHOLD:
        break  # passed

    # Inject feedback for next revision
    messages.append({"role": "assistant", "content": output})
    messages.append({"role": "user", "content": f"Score {score}/20. Weak:\n{weak_areas}\nRevise."})
```

Key things happening:
1. The agent gets the bad RFE + the judge's feedback in the first message
2. The agent rewrites it
3. The judge scores the rewrite
4. If it passes, we stop
5. If not, the agent's output and the judge's feedback are appended to the conversation, and the agent tries again

**Why the conversation grows:** Each iteration adds the previous output + feedback to `messages`. This is how the agent "remembers" what it tried and what the judge said. But it also means context grows ~500-1000 tokens per iteration. Small models (Qwen 3.5 9B) run out of context by iteration 3.

## What gets logged to MLFlow

### Parameters (set once per run)

**Where to find:** Click any run, look at the **Overview** tab, scroll to the **Parameters** section.

**What they are for:** Parameters describe the *setup* of the run. They do not change across iterations. Use them to filter and compare runs (for example, show me all runs where `agent_model = gemma/gemma4`).

| Parameter | What it is | Why it is useful | Example |
|-----------|-----------|-----------------|---------|
| `agent_model` | Which model rewrote the RFE | Filter runs by model to compare performance | `kimi/kimi-k2-6` |
| `judge_model` | Which model scored it | Track whether judge choice affects outcomes | `openai/gpt-5-mini` |
| `rfe_name` | Which bad RFE was used | Filter to see how all models handled the same task | `task_not_need` |
| `weakness` | What was wrong with the original | Quick context without reading the artifact | `Task, not business need` |
| `threshold` | Score needed to pass | Compare runs at different strictness levels | `18/20` |
| `max_iterations` | Max revision attempts | Check if runs hit the cap | `4` |
| `outcome` | Final result: did it pass? | The most important parameter. Filter by `satisfied` vs `max_iterations` vs `error` | `satisfied` |
| `score_history` | Score at each iteration as JSON | See the full improvement curve at a glance without clicking into individual metrics | `[14, 20]` |

### Metrics (numbers, chartable)

**Where to find:** Click any run, look at the **Overview** tab, **Metrics** section. Also visible as columns in the experiment list view (you can add/remove columns).

**What they are for:** Metrics are numbers you can chart, sort, and compare across runs. MLFlow lets you plot metrics over time or compare them across runs in the experiment view.

| Metric | What it is | Why it is useful | Example |
|--------|-----------|-----------------|---------|
| `original_score` | Judge's score of the bad RFE *before* improvement | Baseline. All models start from the same score on the same RFE. If originals differ across runs for the same RFE, the judge is inconsistent. | `14` |
| `score_iter_0` | Judge's score after iteration 1 | How much did the first rewrite improve things? This is the most important metric. If this already passes, the loop added value in one call. | `20` |
| `score_iter_1` | Judge's score after iteration 2 | Did revision help or hurt? Compare to `score_iter_0`. If lower, the model regressed. | `18` |
| `latency_s_0` | Seconds for iteration 1 (agent + judge combined) | Cost and speed comparison across models. Kimi K2 takes 35s, Gemma 4 takes 5s. | `37.3` |
| `final_score` | Last score recorded | The outcome. Sort by this to find the best and worst runs. | `20` |
| `iterations_needed` | How many iterations to reach the threshold | The key question for the blog: which models self-correct faster? | `1` |
| `improvement` | `final_score - original_score` | Net quality gain from the outcome loop. The number that justifies the pattern. | `6` |
| Per-criterion: `what_iter_0`, `why_iter_0`, etc. | Individual rubric criterion scores per iteration | Diagnose *which* criteria the model struggles with. If `how` is always 1 while everything else is 2, the model keeps prescribing architecture. | `2` |

### Artifacts (files, readable)

**Where to find:** Click any run, click the **Artifacts** tab. You see a file list on the left. Click any file to read its contents on the right.

**What they are for:** Artifacts are the actual text. Metrics tell you the scores, artifacts tell you *why*. This is where you validate whether the judge is right and whether the model's revision actually improved things.

| Artifact | What it contains | Why it is useful |
|----------|-----------------|-----------------|
| `original.md` | The bad RFE text, exactly as input | Read this first to understand the starting point |
| `rfe_iter_0.md` | The agent's first rewrite | Compare to `original.md` to see what the model changed. Did it actually fix the weakness? |
| `rfe_iter_1.md` | The agent's second rewrite (if iteration 2 happened) | Compare to `rfe_iter_0.md`. Did revision help or introduce new problems? |
| `just_iter_0.md` | The judge's justification for iteration 1's score | **This is the most valuable artifact.** Read it to understand *why* the judge gave the score it gave. If you disagree with the justification, your rubric or judge needs calibration. |
| `just_iter_1.md` | The judge's justification for iteration 2's score | Compare to `just_iter_0.md`. Did the judge catch different issues, or the same ones? |
| `final_rfe.md` | The last version produced | The output you would actually use. If `outcome = satisfied`, this is the RFE that passed the rubric. |

**How to use artifacts for judge calibration:** Read 10-20 `just_iter_0.md` files across different runs. Ask yourself: do I agree with the judge's scores? If the judge gives 2/2 on "customer_voice" when the model invented fictional customer quotes, your rubric's definition of customer voice is too loose. Tighten it. If the judge gives 0/2 on "how" when the RFE only mentions well-known platform components (which is acceptable per your rubric), the judge is too strict. Add exceptions to the rubric. The artifacts are your feedback loop on the feedback loop.

## Reading the MLFlow UI

### The experiment list view

**Where:** Open MLFlow (http://localhost:5001), click the experiment name in the left sidebar (`rfe-strict-rubric`, `rfe-multimodel-comparison`, etc.).

**What you see:** A table of all runs with metrics as columns. Each row is one model x RFE combination.

**How to use it:**
- **Sort by `iterations_needed`** to find which model-RFE combinations needed the most work
- **Sort by `improvement`** to find the biggest quality jumps
- **Sort by `latency_s_0`** to find the fastest models
- **Filter by `outcome`** (click the filter icon) to show only runs that hit `max_iterations` (the failures worth investigating)
- **Add columns** by clicking the column selector to show per-criterion scores like `what_iter_0`, `how_iter_0`
- **Compare runs** by selecting 2+ rows and clicking "Compare" to see metrics side by side

### A single run (what you see in the screenshots)

**Overview tab:**
- **Metrics section**: `original_score: 14`, `score_iter_0: 20`, `final_score: 20`, `iterations_needed: 1`, `latency_s_0: 37.3`
- **Parameters section**: `agent_model: kimi/kimi-k2-6`, `judge_model: openai/gpt-4.1-mini`, `rfe_name: task_not_need`, `threshold: 18/20`, `outcome: satisfied`

This tells you: Kimi K2 took a bad RFE (scored 14/20), rewrote it in one iteration (37.3 seconds), and the judge gave the rewrite 20/20.

**Artifacts tab:**
Three files for a 1-iteration run:
- `original.md`: The bad RFE that started as a PostgreSQL migration task
- `rfe_iter_0.md`: Kimi K2's rewrite, reframed as a business need for database continuity
- `just_iter_0.md`: The judge's explanation of why it scored 20/20

Click any artifact to read the full text in the MLFlow UI. This is how you validate the judge: read the rewrite, read the justification, decide if you agree with the score.

**Model metrics tab:** Shows system-level metrics if tracing is enabled. Not used in this experiment but would show token counts and latency breakdowns in a production setup.

**Traces tab:** If you add `@mlflow.trace` decorators to the agent and judge functions, each model call appears here as a span with inputs, outputs, and timing. Useful for debugging but not configured in the basic experiment scripts.

## The rubric

### Basic rubric (5 criteria, /10)

Used in the first experiments. 5 criteria scored 0-2:
1. **WHAT**: Is the customer need clear?
2. **WHY**: Named customers with business impact?
3. **HOW**: Leaves architecture to engineering?
4. **NOT_TASK**: Business need, not a task/chore?
5. **RIGHT_SIZED**: Maps to one feature?

Every model passed this on iteration 1. The criteria are too coarse.

### Strict rubric (10 criteria, /20)

Added 5 format criteria:
6. **STRUCTURE**: Has all 4 required sections?
7. **ACCEPTANCE_CRITERIA**: Measurable and testable?
8. **CONCISENESS**: 300-800 words, no filler?
9. **CUSTOMER_VOICE**: Quotes or detailed paraphrasing?
10. **ACTIONABILITY**: Engineering could start without clarifying questions?

This forced more iterations with the gpt-5-mini judge. But gpt-4.1-mini still gave perfect scores on iteration 1.

## The bad RFEs

Four deliberately broken RFEs, each failing on different criteria:

| Name | What is wrong | Original score (gpt-5-mini judge) |
|------|--------------|-----------------------------------|
| `vague_no_evidence` | Says "better GPU support" with no specifics or customer names | 3-5/10 |
| `prescriptive_architecture` | Mandates Redis, Envoy ext_proc, Ketama hashing, Go, Protocol Buffers | 2-4/10 |
| `task_not_need` | "Migrate PostgreSQL 14 to 16" is a task, not a business need | 3-4/10 |
| `bundled_scope` | Bundles marketplace + observability + security + testing into one RFE | 4-6/10 |

## Key finding: judge quality determines everything

| Judge | Avg original score | Avg iterations to pass | Outcome |
|-------|-------------------|----------------------|---------|
| gpt-4.1-mini | 5.0/10 | 1.0 | Every model passes immediately |
| gpt-5-mini | 3.8/10 | 1.8 | Models need 1-3 iterations, some regress |

The same bad RFE scores differently depending on the judge. A lenient judge makes the outcome loop worthless (everything passes). A strict judge makes it valuable (genuine revision happens). The judge is the most important component in the system, not the agent model and not the loop code.

## Files in this directory

| File | What it does |
|------|-------------|
| `run_outcome_loop.py` | Basic outcome loop with generic tasks (code review, technical summary) |
| `run_rfe_eval.py` | RFE generation from customer interview excerpts |
| `run_rfe_improvement.py` | Single-model RFE improvement with before/after tracking |
| `run_rfe_multimodel.py` | Multi-model comparison across all available models |
| `README.md` | Quick setup and run instructions |
| `WALKTHROUGH.md` | This file |
