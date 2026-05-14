#!/usr/bin/env python3
"""
MCP integration using OGX Responses API with streaming.

Connects directly to MCP servers without requiring prior toolgroup registration.
The MCP server details are specified in the tools parameter, and OGX discovers
and invokes tools dynamically. Responses stream back in real time.
"""

import os
import sys

from openai import OpenAI


def main():
    model_id = os.environ.get("INFERENCE_MODEL", "openai/gpt-4o-mini")
    ogx_port = os.environ.get("OGX_PORT", "8321")
    ogx_url = f"http://localhost:{ogx_port}"
    mcp_server_url = os.environ.get("MCP_SERVER_URL", "http://0.0.0.0:8181")
    mcp_server_label = "Red Hat Validated Models"

    print("=" * 80)
    print("MCP Server via OGX Responses API (Streaming)")
    print("=" * 80)
    print(f"OGX: {ogx_url}")
    print(f"MCP Server: {mcp_server_url}")
    print(f"Model: {model_id}")
    print()

    client = OpenAI(base_url=f"{ogx_url}/v1", api_key="not-needed")

    query = "What is the current stock price of HDFCBANK.NS?"
    instructions = (
        "You are a helpful assistant with access to Yahoo Finance tools via MCP. "
        "When asked about stock prices, use the available tools to fetch the information."
    )

    print(f"Query: {query}")
    print("-" * 80)
    print()

    stream = client.responses.create(
        model=model_id,
        input=query,
        instructions=instructions,
        tools=[{
            "type": "mcp",
            "server_url": mcp_server_url,
            "server_label": mcp_server_label,
            "require_approval": "never",
        }],
        tool_choice="auto",
        stream=True,
        timeout=120.0,
    )

    print("Streaming Response:")
    print("-" * 80)

    for event in stream:
        event_type = getattr(event, "type", None)
        if not event_type:
            continue

        print(f"[{event_type}]", end="")

        if "mcp" in event_type.lower():
            print(f" (MCP event)", end="")

        if hasattr(event, "output_index"):
            print(f" output_index={event.output_index}", end="")

        if hasattr(event, "delta") and event.delta:
            print(f" delta={event.delta}", end="")

        if hasattr(event, "item_id"):
            print(f" item_id={event.item_id}", end="")

        print()

    print("-" * 80)
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
