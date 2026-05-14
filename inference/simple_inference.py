#!/usr/bin/env python3
"""Test inference using OGX Responses API with streaming and non-streaming modes."""

import os
from openai import OpenAI
from termcolor import colored

port = os.environ.get('OGX_PORT', '8321')
model = os.environ.get('INFERENCE_MODEL', 'openai/gpt-4o-mini')

client = OpenAI(base_url=f"http://localhost:{port}/v1", api_key="unused")

print(f"Model: {colored(model, 'cyan')}")
print()

print(colored("--- Non-streaming ---", "green"))
response = client.responses.create(
    model=model,
    input="Explain microservices in two sentences.",
    stream=False,
)
for item in response.output:
    if item.type == "message":
        print(item.content[0].text)
print()

print(colored("--- Streaming ---", "green"))
stream = client.responses.create(
    model=model,
    input="What are the benefits of containerization? Be brief.",
    stream=True,
)
for event in stream:
    if event.type == "response.output_text.delta":
        print(event.delta, end="", flush=True)
print("\n")

print(colored("Done.", "green"))
