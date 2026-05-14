#!/usr/bin/env python3
"""
Test MCP Integration using OGX Responses API (Direct Approach)

This demonstrates that the Responses API can connect directly to MCP servers
without requiring prior toolgroup registration. The MCP server details are
specified in the tools parameter, and OGX discovers and invokes
tools dynamically.
"""
from openai import OpenAI
from termcolor import cprint
import os
import json

# Configuration
model_id = os.environ.get("INFERENCE_MODEL", "ollama/llama3.2:3b")  # Configurable via INFERENCE_MODEL env var
ogx_port = os.environ.get('OGX_PORT', '8321')
ogx_url = f"http://localhost:{ogx_port}"
mcp_server_url = "http://0.0.0.0:8181"
mcp_server_label = "Red Hat Validated Models"

print("=" * 80)
print("Testing MCP Server via OGX Responses API (Direct)")
print("=" * 80)
print(f"OGX: {ogx_url}")
print(f"MCP Server: {mcp_server_url}")
print(f"Model: {model_id}")
print()
cprint("Note: Using direct MCP connection (no toolgroup registration needed)", "cyan")
print()

# Create OpenAI client pointing to OGX
openai_client = OpenAI(
    base_url=f"{ogx_url}/v1",
    api_key="not-needed"
)

# Define the query
query = "What is the current stock price of HDFCBANK.NS?"

instructions = """You are a helpful assistant with access to Yahoo Finance tools via MCP.
When asked about stock prices, use the available tools to fetch the information.
Always provide clear and helpful responses."""

print("=" * 80)
print("Making Responses API Call with MCP Tools")
print("=" * 80)
print(f"Query: {query}")
print("-" * 80)
cprint("\nThe Responses API will:", "cyan")
cprint("  1. Connect to the MCP server at the specified URL", "cyan")
cprint("  2. Discover available tools dynamically", "cyan")
cprint("  3. Invoke tools as needed during the conversation", "cyan")
print()

try:
    print(":hourglass_flowing_sand: Sending request to OGX with streaming...\n")

    stream = openai_client.responses.create(
        model=model_id,
        input=query,
        instructions=instructions,
        tools=[{
            "type": "mcp",
            "server_url": mcp_server_url,
            "server_label": mcp_server_label,
            "require_approval": "never",  # Required field: "always", "never", or filter
        }],
        tool_choice="auto",  # Let the model decide when to use tools
        stream=True,  # Enable streaming for real-time feedback
        timeout=120.0  # 2 minute timeout
    )

    # Process streaming response
    print(f":speech_balloon: Streaming Response:")
    print("-" * 80)

    for event in stream:
        if hasattr(event, 'type'):
            event_type = event.type

            # Show all event types for debugging
            print(f"[Event: {event_type}]")

            if "mcp" in event_type.lower():
                cprint(f"  → MCP Event: {event_type}", "yellow")

            if hasattr(event, 'output_index'):
                print(f"  Output index: {event.output_index}")

            if hasattr(event, 'delta') and event.delta:
                print(f"  Delta: {event.delta}")

            if hasattr(event, 'item_id'):
                print(f"  Item ID: {event.item_id}")

            # Try to extract any text content
            if hasattr(event, 'content'):
                print(f"  Content: {event.content}")

            print()

    print("-" * 80)
    cprint("✓ Test Completed Successfully\n", "green")

except Exception as e:
    cprint(f"\n:x: Error: {e}", "red")
    print(f"Make sure:")
    print(f"  1. OGX is running at {ogx_url}")
    print(f"  2. MCP server is accessible at {mcp_server_url}")
    print()
    import traceback

    traceback.print_exc()