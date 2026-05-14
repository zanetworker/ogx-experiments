#!/usr/bin/env python3
"""
Complete example of using function tools with the OGX Responses API

This demonstrates:
1. Defining Python functions
2. Creating function tool schemas with JSON validation for OGX
3. Using the Responses API to call functions
4. Handling function execution
5. Sending results back to the model

IMPORTANT: OGX Responses API uses a FLAT structure for function tools:
{
    "type": "function",
    "name": "function_name",
    "description": "...",
    "parameters": {...}
}

This is DIFFERENT from OpenAI's Chat Completions API nested format:
{
    "type": "function",
    "function": {
        "name": "...",
        "parameters": {...}
    }
}
"""

import json
import os
from openai import OpenAI
from termcolor import colored, cprint

# ============================================================================
# STEP 1: Define Your Python Functions
# ============================================================================

def calculate(x: float, y: float, operation: str) -> dict:
    """
    Perform basic math operations.
    
    This is the actual Python function that will be executed when the model
    requests it via the function tool.
    """
    print(colored(f"\n🔧 Executing calculate({x}, {y}, '{operation}')", "cyan"))
    
    ops = {
        "add": x + y,
        "subtract": x - y,
        "multiply": x * y,
        "divide": x / y if y != 0 else None
    }
    
    result = ops.get(operation)
    if result is None:
        return {"error": f"Invalid operation or division by zero: {operation}"}
    
    return {"result": result}


# ============================================================================
# STEP 2: Define Function Tool Schema (OGX Responses API Format)
# ============================================================================
#
# NOTE: Unlike OpenAI's Chat Completions API which uses nested format:
#   {type: "function", function: {name, parameters}}
#
# OGX's Responses API uses a FLAT format:
#   {type: "function", name, description, parameters}
#

calculator_tool = {
    "type": "function",
    "name": "calculate",
    "description": "Perform basic math operations (add, subtract, multiply, divide)",
    "parameters": {
        "type": "object",
        "properties": {
            "x": {
                "type": "number",
                "description": "First number"
            },
            "y": {
                "type": "number",
                "description": "Second number"
            },
            "operation": {
                "type": "string",
                "enum": ["add", "subtract", "multiply", "divide"],
                "description": "Mathematical operation to perform"
            }
        },
        "required": ["x", "y", "operation"]
    }
}


# ============================================================================
# STEP 3: Function to Execute Tool Calls
# ============================================================================

def execute_function_call(function_name: str, arguments) -> dict:
    """
    Route function calls to the appropriate Python function.
    
    In a real application, you might have multiple functions and route
    based on the function_name.
    
    Note: arguments may come as either a dict or JSON string, so we handle both.
    """
    # Parse arguments if they come as a JSON string
    if isinstance(arguments, str):
        try:
            arguments = json.loads(arguments)
        except json.JSONDecodeError as e:
            return {"error": f"Failed to parse arguments: {e}"}
    
    if function_name == "calculate":
        return calculate(**arguments)
    else:
        return {"error": f"Unknown function: {function_name}"}


# ============================================================================
# STEP 4: Main Function - Responses API Workflow
# ============================================================================

def main():
    """
    Complete workflow demonstrating function tools with Responses API.
    
    This shows the two-step process:
    1. Model requests to call a function
    2. We execute it and send the result back for final answer
    """
    
    print(colored("=" * 80, "yellow"))
    print(colored("Function Tools with OGX Responses API", "yellow", attrs=["bold"]))
    print(colored("=" * 80, "yellow"))
    
    # Setup OpenAI client pointing to OGX
    ogx_url = f"http://localhost:{os.environ.get('OGX_PORT', '8321')}"
    client = OpenAI(
        base_url=f"{ogx_url}/v1",
        api_key="not-needed"
    )

    print(f"\n📍 OGX URL: {ogx_url}")
    
    # Get model ID
    model_id = os.environ.get("INFERENCE_MODEL", "meta-llama/Llama-3.2-3B-Instruct")  # Configurable via INFERENCE_MODEL env var
    print(f"🤖 Model: {model_id}")
    
    # User query
    user_query = "What is 25 plus 15?"
    print(f"\n💬 User Query: {colored(user_query, 'cyan')}")
    
    # ========================================================================
    # STEP 4A: First API Call - Model Requests Function
    # ========================================================================
    
    print(colored("\n" + "─" * 80, "yellow"))
    print(colored("STEP 1: Initial Responses API Call", "yellow", attrs=["bold"]))
    print(colored("─" * 80, "yellow"))
    
    try:
        response = client.responses.create(
            model=model_id,
            input=user_query,
            instructions="Use the calculate tool to perform math operations. Always use the tool for calculations.",
            tools=[calculator_tool],  # Pass function tool schema
            tool_choice="auto",       # Let model decide when to use tools
            stream=False
        )
        
        print(f"✅ Response ID: {response.id}")
        print(f"📊 Status: {response.status}")
        
    except Exception as e:
        cprint(f"\n❌ Error calling Responses API: {e}", "red")
        return
    
    # ========================================================================
    # STEP 4B: Process Response - Extract Function Calls
    # ========================================================================
    
    print(colored("\n" + "─" * 80, "yellow"))
    print(colored("STEP 2: Process Model Response", "yellow", attrs=["bold"]))
    print(colored("─" * 80, "yellow"))
    
    function_calls_to_execute = []
    
    if hasattr(response, 'output'):
        print(f"\n📦 Total output items: {len(response.output)}")
        
        for i, item in enumerate(response.output):
            print(f"\n  Item {i + 1}: type = {colored(getattr(item, 'type', 'NO TYPE'), 'cyan')}")
            
            # Check if this is a function call request
            if hasattr(item, 'type') and item.type == "function_call":
                function_name = item.name
                function_args = item.arguments
                call_id = item.call_id
                
                print(colored(f"\n  🎯 Function Call Requested:", "green", attrs=["bold"]))
                print(f"     Function: {colored(function_name, 'yellow')}")
                print(f"     Arguments: {colored(json.dumps(function_args, indent=6), 'cyan')}")
                print(f"     Call ID: {call_id}")
                
                function_calls_to_execute.append({
                    "call_id": call_id,
                    "name": function_name,
                    "arguments": function_args
                })
    
    # ========================================================================
    # STEP 4C: Execute Functions
    # ========================================================================
    
    if not function_calls_to_execute:
        print(colored("\n⚠️  No function calls requested by model", "yellow"))
        return
    
    print(colored("\n" + "─" * 80, "yellow"))
    print(colored("STEP 3: Execute Functions", "yellow", attrs=["bold"]))
    print(colored("─" * 80, "yellow"))
    
    tool_outputs = []

    for call in function_calls_to_execute:
        print(f"\n🔧 Executing: {colored(call['name'], 'yellow')}")

        # Execute the actual Python function
        result = execute_function_call(call['name'], call['arguments'])

        print(f"✅ Result: {colored(json.dumps(result, indent=2), 'green')}")

        # Prepare function_call_output for the input array
        tool_outputs.append({
            "type": "function_call_output",
            "call_id": call['call_id'],
            "output": json.dumps(result),
        })

    # ========================================================================
    # STEP 4D: Send Results Back to Model
    # ========================================================================

    print(colored("\n" + "─" * 80, "yellow"))
    print(colored("STEP 4: Send Results Back for Final Answer", "yellow", attrs=["bold"]))
    print(colored("─" * 80, "yellow"))

    try:
        final_response = client.responses.create(
            model=model_id,
            input=tool_outputs,
            previous_response_id=response.id,
            stream=False,
        )
        
        print(f"\n✅ Final Response ID: {final_response.id}")
        print(f"📊 Status: {final_response.status}")
        
    except Exception as e:
        cprint(f"\n❌ Error sending tool results: {e}", "red")
        return
    
    # ========================================================================
    # STEP 4E: Display Final Answer
    # ========================================================================
    
    print(colored("\n" + "─" * 80, "yellow"))
    print(colored("STEP 5: Final Answer", "yellow", attrs=["bold"]))
    print(colored("─" * 80, "yellow"))
    
    if hasattr(final_response, 'output'):
        for item in final_response.output:
            if hasattr(item, 'type') and item.type == "message":
                if hasattr(item, 'content'):
                    for content in item.content:
                        if hasattr(content, 'text'):
                            print(colored(f"\n🤖 Assistant: {content.text}", "green", attrs=["bold"]))
    
    print(colored("\n" + "=" * 80, "yellow"))
    print(colored("✅ Complete!", "green", attrs=["bold"]))
    print(colored("=" * 80, "yellow"))
    
    # ========================================================================
    # Summary
    # ========================================================================
    
    print(colored("\n📝 Summary:", "cyan", attrs=["bold"]))
    print("""
This example demonstrated:
  ✅ Defining Python functions (calculate)
  ✅ Creating function tool schemas with JSON validation
  ✅ Using Responses API with function tools
  ✅ Extracting function call requests from model
  ✅ Executing Python functions with provided arguments
  ✅ Sending results back to model via tool_results
  ✅ Getting final natural language answer from model

Key Differences from Agents API:
  • You manually define JSON schemas (vs @client_tool decorator)
  • You control function execution (vs automatic execution)
  • You manage the request/response loop (vs Agent handles it)
  • More control but requires more code
  
Key Format Difference from OpenAI:
  • OGX Responses API uses FLAT structure: {type, name, description, parameters}
  • OpenAI Chat Completions uses NESTED: {type, function: {name, parameters}}
    """)


if __name__ == "__main__":
    main()