#!/usr/bin/env python3
"""
Anthropic Messages API via OGX

Demonstrates using the Anthropic Python SDK to talk to OGX through the
/v1/messages endpoint. OGX translates between Anthropic and OpenAI formats
transparently, so any Anthropic SDK client can point at OGX and work.

Features shown:
  1. Basic message creation (non-streaming)
  2. Streaming with SSE event parsing
  3. Multi-turn conversation
  4. Tool use with Anthropic format (tool definitions + round-trip)

Requirements:
  pip install anthropic termcolor

Usage:
  # Start OGX on port 8321 (default)
  export INFERENCE_MODEL="openai/gpt-4o-mini"  # or any model registered in OGX
  python 9-anthropic-messages.py
"""

import json
import os
import sys

from anthropic import Anthropic
from termcolor import colored


def get_client():
    """Create an Anthropic client pointed at OGX."""
    port = os.environ.get("OGX_PORT", "8321")
    base_url = f"http://localhost:{port}"
    return Anthropic(base_url=base_url, api_key="unused")


def get_model():
    """Get the model ID from environment or use a default."""
    return os.environ.get("INFERENCE_MODEL", "openai/gpt-4o-mini")


def demo_basic_message(client, model):
    """Basic non-streaming message creation."""
    print(colored("=" * 70, "yellow"))
    print(colored("1. Basic Message (non-streaming)", "yellow", attrs=["bold"]))
    print(colored("=" * 70, "yellow"))

    response = client.messages.create(
        model=model,
        max_tokens=128,
        messages=[
            {"role": "user", "content": "What is 2+2? Reply with just the number."},
        ],
    )

    print(f"  ID:          {response.id}")
    print(f"  Role:        {response.role}")
    print(f"  Stop reason: {response.stop_reason}")
    print(f"  Usage:       {response.usage.input_tokens} in / {response.usage.output_tokens} out")

    # Content may include thinking blocks; extract text blocks
    for block in response.content:
        if block.type == "text":
            print(f"  Text:        {colored(block.text, 'green')}")

    print()


def demo_streaming(client, model):
    """Streaming message creation with SSE events."""
    print(colored("=" * 70, "yellow"))
    print(colored("2. Streaming", "yellow", attrs=["bold"]))
    print(colored("=" * 70, "yellow"))

    print("  Response: ", end="", flush=True)

    with client.messages.stream(
        model=model,
        max_tokens=128,
        messages=[
            {"role": "user", "content": "Count from 1 to 5, separated by commas."},
        ],
    ) as stream:
        for text in stream.text_stream:
            print(colored(text, "green"), end="", flush=True)

    print("\n")


def demo_multi_turn(client, model):
    """Multi-turn conversation preserving context."""
    print(colored("=" * 70, "yellow"))
    print(colored("3. Multi-turn Conversation", "yellow", attrs=["bold"]))
    print(colored("=" * 70, "yellow"))

    messages = [
        {"role": "user", "content": "My name is Alice and I work on AI safety."},
    ]

    # Turn 1
    response = client.messages.create(
        model=model,
        max_tokens=128,
        messages=messages,
    )

    assistant_text = ""
    for block in response.content:
        if block.type == "text":
            assistant_text = block.text
            break

    print(f"  User:      My name is Alice and I work on AI safety.")
    print(f"  Assistant: {colored(assistant_text, 'green')}")

    # Turn 2: add the assistant response and ask a follow-up
    messages.append({"role": "assistant", "content": assistant_text})
    messages.append({"role": "user", "content": "What is my name and what do I work on?"})

    response2 = client.messages.create(
        model=model,
        max_tokens=128,
        messages=messages,
    )

    for block in response2.content:
        if block.type == "text":
            print(f"  User:      What is my name and what do I work on?")
            print(f"  Assistant: {colored(block.text, 'green')}")
            # Verify the model remembered the context
            lower = block.text.lower()
            if "alice" in lower:
                print(colored("  [context retained]", "cyan"))
            break

    print()


def demo_tool_use(client, model):
    """Tool use with Anthropic format: definitions, tool_use response, and round-trip."""
    print(colored("=" * 70, "yellow"))
    print(colored("4. Tool Use (Anthropic format)", "yellow", attrs=["bold"]))
    print(colored("=" * 70, "yellow"))

    tools = [
        {
            "name": "get_weather",
            "description": "Get the current weather for a city.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name, e.g. San Francisco, CA",
                    },
                },
                "required": ["location"],
            },
        }
    ]

    # Step 1: ask a question that should trigger tool use
    print("  Step 1: Requesting weather information...")

    response = client.messages.create(
        model=model,
        max_tokens=256,
        messages=[
            {"role": "user", "content": "What's the weather in San Francisco?"},
        ],
        tools=tools,
    )

    print(f"  Stop reason: {response.stop_reason}")

    # Look for tool_use blocks
    tool_use_block = None
    for block in response.content:
        if block.type == "tool_use":
            tool_use_block = block
            print(f"  Tool call:   {colored(block.name, 'cyan')}({json.dumps(block.input)})")
            print(f"  Call ID:     {block.id}")
        elif block.type == "text":
            print(f"  Text:        {block.text[:80]}...")

    if not tool_use_block:
        print(colored("  Model did not call a tool (may have answered directly)", "yellow"))
        print()
        return

    # Step 2: provide the tool result and get a final answer
    print("  Step 2: Sending tool result back...")

    fake_result = json.dumps({"temperature": "62F", "condition": "Foggy", "humidity": "85%"})

    response2 = client.messages.create(
        model=model,
        max_tokens=256,
        messages=[
            {"role": "user", "content": "What's the weather in San Francisco?"},
            {"role": "assistant", "content": response.content},
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use_block.id,
                        "content": fake_result,
                    }
                ],
            },
        ],
        tools=tools,
    )

    for block in response2.content:
        if block.type == "text":
            print(f"  Final:       {colored(block.text, 'green')}")
            break

    print()


def main():
    client = get_client()
    model = get_model()

    port = os.environ.get("OGX_PORT", "8321")
    print(colored(f"\nOGX server: http://localhost:{port}", "cyan"))
    print(colored(f"Model:      {model}", "cyan"))
    print()

    try:
        demo_basic_message(client, model)
        demo_streaming(client, model)
        demo_multi_turn(client, model)
        demo_tool_use(client, model)
    except Exception as e:
        print(colored(f"\nError: {e}", "red"))
        print(colored("Make sure OGX is running and the model is available.", "red"))
        sys.exit(1)

    print(colored("All demos completed successfully.", "green"))


if __name__ == "__main__":
    main()
