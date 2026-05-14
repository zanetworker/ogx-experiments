#!/usr/bin/env python3
"""
MCP integration using OGX Responses API.

The Responses API connects directly to MCP servers without requiring prior
toolgroup registration. The MCP server URL is specified in the tools parameter,
and OGX discovers and invokes tools dynamically.
"""

import json
import os
import sys

from openai import OpenAI


def main():
    model_id = os.environ.get("INFERENCE_MODEL", "openai/gpt-4o-mini")
    ogx_port = os.environ.get("OGX_PORT", "8321")
    ogx_url = f"http://localhost:{ogx_port}"
    mcp_server_url = os.environ.get("MCP_SERVER_URL", "http://0.0.0.0:8181")
    mcp_server_label = "Red Hat AI Validation"

    print("=" * 80)
    print("MCP Server via OGX Responses API")
    print("=" * 80)
    print(f"OGX: {ogx_url}")
    print(f"MCP Server: {mcp_server_url}")
    print(f"Model: {model_id}")
    print()

    client = OpenAI(base_url=f"{ogx_url}/v1", api_key="not-needed")

    query = "best models to run on an h100"
    instructions = (
        "You are a helpful assistant with access to tools via MCP. "
        "Use the appropriate tool when asked to retrieve information. "
        "After fetching content, summarize it in a helpful way."
    )

    print(f"Query: {query}")
    print("-" * 80)

    response = client.responses.create(
        model=model_id,
        input=query,
        instructions=instructions,
        tools=[{
            "type": "mcp",
            "server_url": mcp_server_url,
            "server_label": mcp_server_label,
        }],
        tool_choice="required",
        stream=False,
    )

    print(f"\nResponse ID: {response.id}")
    print(f"Status: {response.status}\n")

    if not hasattr(response, "output"):
        print("No output in response")
        return

    for item in response.output:
        item_type = getattr(item, "type", None)

        if item_type == "mcp_call":
            print(f"[MCP Tool: {item.name}]")
            if hasattr(item, "arguments"):
                print(f"Arguments: {json.dumps(item.arguments, indent=2)}")
            if hasattr(item, "output") and item.output:
                print("Tool Result:")
                if isinstance(item.output, dict):
                    print(json.dumps(item.output, indent=2))
                else:
                    print(item.output)
            elif hasattr(item, "error") and item.error:
                print(f"Tool Error: {item.error}")
            print()

        elif item_type == "mcp_call_result":
            print("[MCP Result]")
            if hasattr(item, "content"):
                for content in item.content:
                    if hasattr(content, "text"):
                        try:
                            data = json.loads(content.text)
                            print(json.dumps(data, indent=2))
                        except json.JSONDecodeError:
                            print(content.text)
            print()

        elif item_type == "message":
            if hasattr(item, "content"):
                for content in item.content:
                    if hasattr(content, "text"):
                        print(content.text)
                        print()

    print("Done.")


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
