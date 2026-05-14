#!/usr/bin/env python3
"""
Function tools with the OGX Responses API.

Demonstrates the full tool-calling loop:
1. Define a function and its JSON schema
2. Send a request; model returns a function_call
3. Execute the function locally
4. Send the result back via function_call_output in the input array
5. Model produces the final answer

OGX uses a FLAT tool schema: {type, name, description, parameters}
(not the nested {type, function: {name, parameters}} from Chat Completions).
"""

import json
import os
import sys

from openai import OpenAI


def calculate(x: float, y: float, operation: str) -> dict:
    """Perform basic math operations."""
    ops = {
        "add": x + y,
        "subtract": x - y,
        "multiply": x * y,
        "divide": x / y if y != 0 else None,
    }
    result = ops.get(operation)
    if result is None:
        return {"error": f"Invalid operation or division by zero: {operation}"}
    return {"result": result}


CALCULATOR_TOOL = {
    "type": "function",
    "name": "calculate",
    "description": "Perform basic math operations (add, subtract, multiply, divide)",
    "parameters": {
        "type": "object",
        "properties": {
            "x": {"type": "number", "description": "First number"},
            "y": {"type": "number", "description": "Second number"},
            "operation": {
                "type": "string",
                "enum": ["add", "subtract", "multiply", "divide"],
                "description": "Mathematical operation to perform",
            },
        },
        "required": ["x", "y", "operation"],
    },
}

FUNCTIONS = {
    "calculate": calculate,
}


def execute_function_call(function_name: str, arguments) -> dict:
    """Route and execute a function call. Arguments may be dict or JSON string."""
    if isinstance(arguments, str):
        try:
            arguments = json.loads(arguments)
        except json.JSONDecodeError as e:
            return {"error": f"Failed to parse arguments: {e}"}

    fn = FUNCTIONS.get(function_name)
    if fn is None:
        return {"error": f"Unknown function: {function_name}"}
    return fn(**arguments)


def main():
    ogx_url = f"http://localhost:{os.environ.get('OGX_PORT', '8321')}"
    model_id = os.environ.get("INFERENCE_MODEL", "openai/gpt-4o-mini")

    client = OpenAI(base_url=f"{ogx_url}/v1", api_key="not-needed")

    print("=" * 60)
    print("Function Tools with OGX Responses API")
    print("=" * 60)
    print(f"OGX: {ogx_url}")
    print(f"Model: {model_id}")

    user_query = "What is 25 plus 15?"
    print(f"\nQuery: {user_query}")

    # Step 1: Send request, model returns function_call items
    print("\n--- Step 1: Initial request ---")
    response = client.responses.create(
        model=model_id,
        input=user_query,
        instructions="Use the calculate tool to perform math operations. Always use the tool for calculations.",
        tools=[CALCULATOR_TOOL],
        tool_choice="auto",
        stream=False,
    )
    print(f"Response ID: {response.id} | Status: {response.status}")

    # Step 2: Extract function calls
    function_calls = []
    for item in response.output:
        if getattr(item, "type", None) == "function_call":
            function_calls.append({
                "call_id": item.call_id,
                "name": item.name,
                "arguments": item.arguments,
            })
            print(f"Function call: {item.name}({item.arguments})")

    if not function_calls:
        print("No function calls requested by model.")
        # Print any text response instead
        for item in response.output:
            if getattr(item, "type", None) == "message":
                for content in getattr(item, "content", []):
                    if hasattr(content, "text"):
                        print(f"Model: {content.text}")
        return

    # Step 3: Execute functions and build function_call_output items
    print("\n--- Step 2: Execute functions ---")
    tool_outputs = []
    for call in function_calls:
        result = execute_function_call(call["name"], call["arguments"])
        print(f"{call['name']} -> {json.dumps(result)}")
        tool_outputs.append({
            "type": "function_call_output",
            "call_id": call["call_id"],
            "output": json.dumps(result),
        })

    # Step 4: Send results back in the input array (NOT as tool_results kwarg)
    print("\n--- Step 3: Send results back ---")
    final_response = client.responses.create(
        model=model_id,
        input=tool_outputs,
        previous_response_id=response.id,
        stream=False,
    )
    print(f"Response ID: {final_response.id} | Status: {final_response.status}")

    # Step 5: Display final answer
    print("\n--- Final Answer ---")
    for item in final_response.output:
        if getattr(item, "type", None) == "message":
            for content in getattr(item, "content", []):
                if hasattr(content, "text"):
                    print(f"Assistant: {content.text}")

    print("\nDone.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
    except Exception as e:
        if "Connection" in type(e).__name__ or "connection" in str(e).lower():
            ogx_port = os.environ.get("OGX_PORT", "8321")
            print(f"Error: Cannot connect to OGX server at localhost:{ogx_port}", file=sys.stderr)
            print("Make sure the server is running.", file=sys.stderr)
        else:
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
