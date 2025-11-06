#!/usr/bin/env python3
"""Test Ollama and vLLM providers using Llama Stack Responses API"""

import os
from openai import OpenAI
from termcolor import colored

port = os.environ.get('LLAMA_STACK_PORT', '8321')
client = OpenAI(base_url=f"http://localhost:{port}/v1", api_key="unused")

print(colored("--- vLLM Code Model (Qwen2.5-Coder) ---", "green"))
response = client.responses.create(
    model="vllm-code/RedHatAI/Qwen2.5-Coder-7B-FP8-dynamic",
    input="Write a Python function to calculate fibonacci numbers.",
    stream=False
)
for item in response.output:
    if item.type == "message":
        print(item.content[0].text)
print()

print(colored("--- vLLM Text Model (Llama 4 Scout) ---", "green"))
response = client.responses.create(
    model="vllm-text/llama-4-scout-17b-16e-w4a16",
    input="Explain microservices in simple terms.",
    stream=False
)
for item in response.output:
    if item.type == "message":
        print(item.content[0].text)
print()

print(colored("--- Ollama Model (Llama 3.2) ---", "green"))
response = client.responses.create(
    model="ollama/llama3.2:latest",
    input="What are the benefits of containerization?",
    stream=False
)
for item in response.output:
    if item.type == "message":
        print(item.content[0].text)
print()

print(colored("--- OpenAI Model (gpt-4o ---", "green"))

response = client.responses.create(
    model="openai/gpt-4o",
    input="What are the benefits of containerization?",
    stream=False
)
for item in response.output:
    if item.type == "message":
        print(item.content[0].text)
print()

# print(colored("--- Streaming (vLLM Code) ---", "green"))
# stream = client.responses.create(
#     model="vllm-code/RedHatAI/Qwen2.5-Coder-7B-FP8-dynamic",
#     input="Write a simple Python hello world program with a main function.",
#     stream=True
# )
# for chunk in stream:
#     if hasattr(chunk, 'delta') and chunk.delta:
#         print(chunk.delta, end="", flush=True)
#     elif hasattr(chunk, 'output'):
#         # Handle non-streaming chunks in stream
#         for item in chunk.output:
#             if item.type == "message":
#                 print(item.content[0].text, end="", flush=True)
# print("\n")

print(colored("✓ All tests completed successfully!", "green"))
