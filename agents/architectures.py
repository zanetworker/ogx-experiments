#!/usr/bin/env python3
"""
Agentic Architectures with Responses API

A) LLM Workflow: tool_choice="none", structured outputs, sequential steps
B) Agentic Workflow: tool_choice="auto", tool execution loop
C) AI Agent: tool_choice="auto", plan-act-observe-reflect, budgets
"""

import json
import os
import time
from openai import OpenAI

def setup_client():
    url = f"http://localhost:{os.environ.get('OGX_PORT', '8321')}/v1"
    return OpenAI(base_url=url, api_key="not-needed"), os.environ.get("INFERENCE_MODEL", "meta-llama/Llama-3.2-3B-Instruct")  # Configurable via INFERENCE_MODEL env var

# Mock tools
TOOLS = {
    "get_competitors": {
        "fn": lambda company: {"competitors": ["TechCorp", "InnovateCo", "FutureSystems"]},
        "schema": {"type": "function", "name": "get_competitors", "description": "Get competitors",
                   "parameters": {"type": "object", "properties": {"company": {"type": "string"}}, "required": ["company"]}}
    },
    "web_search": {
        "fn": lambda query: {"results": [f"Result 1 for {query}", f"Result 2 for {query}"]},
        "schema": {"type": "function", "name": "web_search", "description": "Search the web",
                   "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}
    },
    "summarize_data": {
        "fn": lambda data: {"summary": f"Summary of: {data[:50]}..."},
        "schema": {"type": "function", "name": "summarize_data", "description": "Summarize data",
                   "parameters": {"type": "object", "properties": {"data": {"type": "string"}}, "required": ["data"]}}
    },
    "send_email": {
        "fn": lambda to, subject, body: {"status": "sent", "message_id": "msg_12345"},
        "schema": {"type": "function", "name": "send_email", "description": "Send email",
                   "parameters": {"type": "object", "properties": {"to": {"type": "string"}, "subject": {"type": "string"}, "body": {"type": "string"}}, "required": ["to", "subject", "body"]}}
    }
}

def execute_tool(name, arguments):
    args = json.loads(arguments) if isinstance(arguments, str) else arguments
    return TOOLS[name]["fn"](**args) if name in TOOLS else {"error": f"Unknown: {name}"}

def get_tool_schemas():
    return [t["schema"] for t in TOOLS.values()]


# Pattern A: LLM Workflow (Low Autonomy)
def pattern_a_llm_workflow(client, model):
    """Sequential chain: tool_choice='none', structured outputs."""
    print("\n" + "=" * 60)
    print("PATTERN A: LLM Workflow (Low Autonomy)")
    print("=" * 60)

    # Step 1: Direct function call
    competitors = TOOLS["get_competitors"]["fn"]("ACME")
    print(f"\nStep 1 - Competitors: {competitors['competitors']}")

    # Step 2: Summarize with structured output
    response = client.responses.create(
        model=model,
        input=f"Summarize these competitors: {json.dumps(competitors)}",
        tool_choice="none",
        text={"format": {
            "type": "json_schema", "name": "summary", "strict": True,
            "schema": {"type": "object", "properties": {"summary": {"type": "string"}, "key_points": {"type": "array", "items": {"type": "string"}}}, "required": ["summary", "key_points"]}
        }},
        stream=False
    )
    summary = json.loads(response.output_text)
    print(f"\nStep 2 - Summary:\n{summary['summary']}")
    print(f"\nKey points:")
    for point in summary.get('key_points', []):
        print(f"  • {point}")

    # Step 3: Draft email
    response = client.responses.create(
        model=model,
        input=f"Draft email about: {json.dumps(summary)}",
        tool_choice="none",
        text={"format": {
            "type": "json_schema", "name": "email", "strict": True,
            "schema": {"type": "object", "properties": {"subject": {"type": "string"}, "body": {"type": "string"}}, "required": ["subject", "body"]}
        }},
        stream=False
    )
    email = json.loads(response.output_text)
    print(f"\nStep 3 - Email:")
    print(f"Subject: {email['subject']}")
    print(f"Body:\n{email['body']}")

    return {"pattern": "A", "steps": 3, "api_calls": 2}


# Pattern B: Agentic Workflow (Medium Autonomy)
def pattern_b_agentic_workflow(client, model):
    """Tool loop: tool_choice='auto', model decides tools."""
    print("\n" + "=" * 60)
    print("PATTERN B: Agentic Workflow (Medium Autonomy)")
    print("=" * 60)

    goal = "Research ACME's competitors and send a brief to team@company.com"
    print(f"\nGoal: {goal}\n")

    prev_id, tool_outputs = None, None
    for i in range(5):
        current_input = goal if i == 0 else (tool_outputs or "")

        response = client.responses.create(
            model=model,
            input=current_input,
            instructions="Use tools to complete the task step by step.",
            tools=get_tool_schemas(),
            tool_choice="auto",
            previous_response_id=prev_id,
            stream=False
        )
        prev_id = response.id

        # Extract function calls and messages
        calls = [{"id": o.call_id, "name": o.name, "args": o.arguments}
                 for o in response.output if getattr(o, 'type', None) == "function_call"]

        messages = []
        for o in response.output:
            if getattr(o, 'type', None) == "message":
                for c in getattr(o, 'content', []):
                    if hasattr(c, 'text'):
                        messages.append(c.text)

        print(f"\n--- Iteration {i+1} ---")

        if calls:
            print(f"Tool calls: {[c['name'] for c in calls]}")
            tool_outputs = []
            for c in calls:
                result = execute_tool(c["name"], c["args"])
                print(f"  {c['name']}({c['args']}) -> {json.dumps(result)}")
                tool_outputs.append({"type": "function_call_output", "call_id": c["id"], "output": json.dumps(result)})
        else:
            tool_outputs = None

        if messages:
            print(f"\nModel response:")
            for msg in messages:
                print(msg)

        if messages and not calls:
            print(f"\nDone in {i+1} iterations")
            return {"pattern": "B", "iterations": i+1}

    return {"pattern": "B", "iterations": 5}


# Pattern C: AI Agent (High Autonomy)
def pattern_c_ai_agent(client, model):
    """Autonomous: plan-act-observe-reflect loop with budgets."""
    print("\n" + "=" * 60)
    print("PATTERN C: AI Agent (High Autonomy)")
    print("=" * 60)

    goal = "Increase ACME's newsletter CTR by 10%"
    instructions = """You are an autonomous agent. Process:
1. PLAN: Create steps  2. ACT: Execute with tools  3. OBSERVE: Analyze  4. REFLECT: Update plan
When done, respond with GOAL_COMPLETE or GOAL_FAILED."""

    print(f"\nGoal: {goal}")
    print("Budget: 8 iterations, 120s\n")

    start, prev_id, tool_outputs = time.time(), None, None
    stats = {"planning": 0, "reflections": 0}

    for i in range(8):
        if time.time() - start > 120:
            print("Time exceeded")
            break

        current_input = goal if i == 0 else (tool_outputs or "")
        response = client.responses.create(
            model=model,
            input=current_input,
            instructions=instructions,
            tools=get_tool_schemas(),
            tool_choice="auto",
            previous_response_id=prev_id,
            stream=False
        )
        prev_id = response.id

        print(f"\n--- Iteration {i+1} ---")

        calls = []
        messages = []
        for o in response.output:
            if getattr(o, 'type', None) == "function_call":
                calls.append({"id": o.call_id, "name": o.name, "args": o.arguments})
            elif getattr(o, 'type', None) == "message":
                for c in getattr(o, 'content', []):
                    text = getattr(c, 'text', '')
                    if text:
                        messages.append(text)
                    if "plan" in text.lower(): stats["planning"] += 1
                    if "reflect" in text.lower(): stats["reflections"] += 1

        if calls:
            print(f"Tool calls: {[c['name'] for c in calls]}")
            tool_outputs = []
            for c in calls:
                result = execute_tool(c["name"], c["args"])
                print(f"  {c['name']}({c['args']}) -> {json.dumps(result)}")
                tool_outputs.append({"type": "function_call_output", "call_id": c["id"], "output": json.dumps(result)})
        else:
            tool_outputs = None

        if messages:
            print(f"\nModel response:")
            for msg in messages:
                print(msg)
            if "GOAL_COMPLETE" in "\n".join(messages) or "GOAL_FAILED" in "\n".join(messages):
                print(f"\nDone in {i+1} iterations")
                return {"pattern": "C", "iterations": i+1, **stats, "completed": "GOAL_COMPLETE" in "\n".join(messages)}

    return {"pattern": "C", "iterations": 8, **stats, "completed": False}


def main():
    print("=" * 60)
    print("Agentic Architectures Demo")
    print("=" * 60)

    client, model = setup_client()
    print(f"Model: {model}\n")

    results = {
        'A': pattern_a_llm_workflow(client, model),
        'B': pattern_b_agentic_workflow(client, model),
        'C': pattern_c_ai_agent(client, model)
    }

    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"A (Low):    {results['A']['steps']} steps, {results['A']['api_calls']} API calls")
    print(f"B (Medium): {results['B']['iterations']} iterations")
    print(f"C (High):   {results['C']['iterations']} iterations, {results['C']['planning']} plans, {results['C']['reflections']} reflections")


if __name__ == "__main__":
    main()
