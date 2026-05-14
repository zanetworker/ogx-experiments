#!/usr/bin/env python3
"""
Gemini Interactions API via OGX

Demonstrates using the Google GenAI SDK to talk to OGX through the
/v1alpha/interactions endpoint. This proves that ADK/Gemini ecosystem
clients can call OGX natively without any code changes.

Features shown:
  1. Basic interaction (non-streaming)
  2. Streaming with event parsing
  3. Multi-turn conversation with 'model' role
  4. Tool use with Gemini function_declarations format

Requirements:
  pip install google-genai termcolor

Usage:
  export INFERENCE_MODEL="openai/gpt-4o-mini"
  python gemini_interactions.py
"""

import json
import os
import sys
import warnings

try:
    from google import genai
except ImportError:
    print("Missing dependency: pip install google-genai")
    sys.exit(1)

try:
    from termcolor import colored
except ImportError:
    print("Missing dependency: pip install termcolor")
    sys.exit(1)


def get_client():
    """Create a Google GenAI client pointed at OGX."""
    port = os.environ.get("OGX_PORT", "8321")

    return genai.Client(
        api_key="unused",
        http_options={"base_url": f"http://localhost:{port}/v1alpha"},
    )


def get_model():
    """Get the model ID from environment or use a default."""
    return os.environ.get("INFERENCE_MODEL", "openai/gpt-4o-mini")


def _get_text_output(interaction):
    """Extract the first text output, skipping any thought content."""
    for output in interaction.outputs:
        if output.type == "text":
            return output
    return None


def demo_basic_interaction(client, model):
    """Basic non-streaming interaction."""
    print(colored("=" * 70, "yellow"))
    print(colored("1. Basic Interaction (non-streaming)", "yellow", attrs=["bold"]))
    print(colored("=" * 70, "yellow"))

    interaction = client.interactions.create(
        model=model,
        input="What is 2+2? Reply with just the number.",
    )

    print(f"  ID:      {interaction.id}")
    print(f"  Status:  {interaction.status}")
    print(f"  Role:    {interaction.role}")
    print(f"  Usage:   {interaction.usage.total_input_tokens} in / {interaction.usage.total_output_tokens} out")

    text_output = _get_text_output(interaction)
    if text_output:
        print(f"  Text:    {colored(text_output.text, 'green')}")

    print()


def demo_streaming(client, model):
    """Streaming interaction with event parsing."""
    print(colored("=" * 70, "yellow"))
    print(colored("2. Streaming", "yellow", attrs=["bold"]))
    print(colored("=" * 70, "yellow"))

    stream = client.interactions.create(
        model=model,
        input="Count from 1 to 5, separated by commas.",
        stream=True,
    )

    event_types = []
    text_parts = []
    interaction_id = None

    print("  Events: ", end="", flush=True)

    for event in stream:
        event_name = type(event).__name__
        event_types.append(event_name)

        if event_name == "InteractionStartEvent" and hasattr(event, "interaction") and event.interaction:
            interaction_id = event.interaction.id

        if event_name == "ContentDelta" and hasattr(event, "delta") and event.delta:
            if hasattr(event.delta, "text"):
                text_parts.append(event.delta.text)

    full_text = "".join(text_parts)

    # Show event sequence
    unique_events = []
    for e in event_types:
        if not unique_events or unique_events[-1] != e:
            unique_events.append(e)
    print(colored(" -> ".join(unique_events), "cyan"))

    print(f"  ID:      {interaction_id}")
    print(f"  Text:    {colored(full_text, 'green')}")
    print()


def demo_multi_turn(client, model):
    """Multi-turn conversation using Gemini's 'model' role."""
    print(colored("=" * 70, "yellow"))
    print(colored("3. Multi-turn Conversation", "yellow", attrs=["bold"]))
    print(colored("=" * 70, "yellow"))

    # Gemini uses 'model' for assistant turns (not 'assistant')
    interaction = client.interactions.create(
        model=model,
        input=[
            {"role": "user", "content": [{"type": "text", "text": "My name is Alice."}]},
            {"role": "model", "content": [{"type": "text", "text": "Hello Alice! Nice to meet you."}]},
            {"role": "user", "content": [{"type": "text", "text": "What is my name?"}]},
        ],
    )

    print(f"  Status:  {interaction.status}")

    text_output = _get_text_output(interaction)
    if text_output:
        print(f"  Text:    {colored(text_output.text, 'green')}")
        if "alice" in text_output.text.lower():
            print(colored("  [context retained]", "cyan"))

    print()


def demo_system_instruction(client, model):
    """Interaction with a system instruction."""
    print(colored("=" * 70, "yellow"))
    print(colored("4. System Instruction", "yellow", attrs=["bold"]))
    print(colored("=" * 70, "yellow"))

    interaction = client.interactions.create(
        model=model,
        input="What are you?",
        system_instruction="You are a pirate. Always respond in pirate speak. Keep it short.",
    )

    print(f"  Status:  {interaction.status}")

    text_output = _get_text_output(interaction)
    if text_output:
        print(f"  Text:    {colored(text_output.text, 'green')}")

    print()


def demo_tool_use(client, model):
    """Tool use with Gemini function_declarations format."""
    print(colored("=" * 70, "yellow"))
    print(colored("5. Tool Use (Gemini function_declarations)", "yellow", attrs=["bold"]))
    print(colored("=" * 70, "yellow"))

    tools = [
        {
            "function_declarations": [
                {
                    "name": "get_weather",
                    "description": "Get the current weather for a location.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {"type": "string", "description": "City name"},
                        },
                        "required": ["location"],
                    },
                }
            ]
        }
    ]

    print("  Step 1: Requesting weather (expecting function_call)...")

    interaction = client.interactions.create(
        model=model,
        input="What is the weather in Paris right now? Use the get_weather tool.",
        tools=tools,
    )

    print(f"  Status:  {interaction.status}")
    print(f"  Outputs: {len(interaction.outputs)}")

    # Look for function_call outputs
    function_calls = [o for o in interaction.outputs if o.type == "function_call"]
    text_outputs = [o for o in interaction.outputs if o.type == "text"]

    if function_calls:
        fc = function_calls[0]
        fc_args = getattr(fc, "arguments", None) or getattr(fc, "args", None) or {}
        print(f"  Tool:    {colored(fc.name, 'cyan')}({json.dumps(fc_args)})")
        print(f"  Call ID: {fc.id}")
    elif text_outputs:
        print(f"  Text:    {colored(text_outputs[0].text[:80], 'green')}...")
        print(colored("  Model answered directly without calling the tool", "yellow"))
    else:
        print(colored("  No text or function_call outputs found", "yellow"))

    print()


def demo_generation_config(client, model):
    """Interaction with generation config parameters."""
    print(colored("=" * 70, "yellow"))
    print(colored("6. Generation Config", "yellow", attrs=["bold"]))
    print(colored("=" * 70, "yellow"))

    interaction = client.interactions.create(
        model=model,
        input="Say hello in one sentence.",
        generation_config={
            "temperature": 0.0,
            "max_output_tokens": 32,
        },
    )

    print(f"  Status:  {interaction.status}")

    text_output = _get_text_output(interaction)
    if text_output:
        print(f"  Text:    {colored(text_output.text, 'green')}")

    print()


def main():
    warnings.filterwarnings("ignore", message="Interactions usage is experimental")

    client = get_client()
    model = get_model()

    port = os.environ.get("OGX_PORT", "8321")
    print(colored(f"\nOGX server: http://localhost:{port}/v1alpha", "cyan"))
    print(colored(f"Model:      {model}", "cyan"))
    print()

    demo_basic_interaction(client, model)
    demo_streaming(client, model)
    demo_multi_turn(client, model)
    demo_system_instruction(client, model)
    demo_tool_use(client, model)
    demo_generation_config(client, model)

    print(colored("All demos completed successfully.", "green"))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
    except ConnectionError as e:
        print(colored(f"\nConnection error: {e}", "red"))
        print(colored("Is OGX running? Start it and try again.", "red"))
        sys.exit(1)
    except Exception as e:
        error_msg = str(e).lower()
        if "connection" in error_msg or "refused" in error_msg or "unreachable" in error_msg:
            print(colored(f"\nConnection error: {e}", "red"))
            print(colored("Is OGX running? Start it and try again.", "red"))
        else:
            print(colored(f"\nError: {e}", "red"))
        sys.exit(1)
