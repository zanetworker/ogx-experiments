#!/usr/bin/env python3
"""
Test MCP integration using OGX Responses API

This demonstrates that the Responses API connects directly to MCP servers
without requiring prior toolgroup registration. The MCP server URL is
specified in the tools parameter, and OGX discovers and invokes
tools dynamically.
"""
from openai import OpenAI
from termcolor import cprint
import os
import json


# Configuration
model_id = os.environ.get("INFERENCE_MODEL", "meta-llama/Llama-3.3-70B-Instruct")  # Configurable via INFERENCE_MODEL env var
ogx_port = os.environ.get('OGX_PORT', '8321')
ogx_url = f"http://localhost:{ogx_port}"
mcp_server_url = "http://0.0.0.0:8181"
mcp_server_label = "Red Hat AI Validation"

print("=" * 80)
print("Testing MCP Server via OGX Responses API")
print("=" * 80)
print(f"OGX: {ogx_url}")
print(f"MCP Server: {mcp_server_url}")
print(f"Model: {model_id}")
print()
cprint("Note: No toolgroup registration needed - Responses API connects directly!", "cyan")
print()

# Create OpenAI client pointing to OGX
openai_client = OpenAI(
    base_url=f"{ogx_url}/v1",
    api_key="not-needed"
)

# Define the query
query = "best models to run on an h100"

instructions = """You are a helpful assistant with access to tools via MCP (Model Context Protocol).
When asked to fetch content from a URL, use the 'fetch' tool to do so.
Always use the appropriate tool when asked to retrieve information.
After fetching content, summarize it in a helpful way."""

print("=" * 80)
print("Calling MCP Tools via Responses API")
print("=" * 80)
print(f"Query: {query}")
print("-" * 80)
cprint("\nThe Responses API will:", "cyan")
cprint("  1. Connect to the MCP server at the specified URL", "cyan")
cprint("  2. Discover available tools dynamically", "cyan")
cprint("  3. Invoke tools as needed during the conversation", "cyan")
print()

try:
    response = openai_client.responses.create(
        model=model_id,
        input=query,
        instructions=instructions,
        tools=[{
            "type": "mcp",
            "server_url": mcp_server_url,
            "server_label": mcp_server_label,
        }],
        tool_choice="required",
        stream=False
    )

    # Print formatted response
    print(f"\n💬 Response:")
    print("-" * 40)
    print(f"[Response ID: {response.id}]")
    print(f"[Status: {response.status}]\n")

    if hasattr(response, 'output'):
        print(f"[DEBUG] Total output items: {len(response.output)}")
        for i, item in enumerate(response.output):
            print(f"[DEBUG] Item {i}: type={getattr(item, 'type', 'NO TYPE')}")
        print()

        for item in response.output:
            if hasattr(item, 'type'):
                if item.type == "mcp_call":
                    print(f"[→ MCP Tool called: {item.name}]")
                    if hasattr(item, 'arguments'):
                        print(f"Arguments: {json.dumps(item.arguments, indent=2)}")

                    if hasattr(item, 'output') and item.output:
                        print(f"\n[✓ Tool Result:]")
                        if isinstance(item.output, dict):
                            print(json.dumps(item.output, indent=2))
                        else:
                            print(item.output)
                        print()
                    elif hasattr(item, 'error') and item.error:
                        print(f"\n[⚠️ Tool Error: {item.error}]\n")

                elif item.type == "mcp_call_result":
                    print(f"[✓ MCP result received]")
                    if hasattr(item, 'content'):
                        for content in item.content:
                            if hasattr(content, 'text'):
                                try:
                                    data = json.loads(content.text)
                                    print(json.dumps(data, indent=2))
                                except:
                                    print(content.text)
                    print()

                elif item.type == "message":
                    print(f"[💬 LLM Response:]")
                    if hasattr(item, 'content'):
                        for content in item.content:
                            if hasattr(content, 'text'):
                                print(content.text)
                                print()

    print("-" * 40)
    print(f"[✓ Completed]\n")

except Exception as e:
    cprint(f"\n❌ Error: {e}", "red")
    print(f"Make sure MCP server is running at {mcp_server_url}")
    import traceback
    traceback.print_exc()
