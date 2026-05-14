#!/usr/bin/env python3
"""
Batches API via OGX

Demonstrates the OpenAI-compatible Batches API for processing multiple
requests asynchronously. Batches are useful for high-throughput workloads
where you submit many requests at once and retrieve results later.

Features shown:
  1. Creating a JSONL batch input file and uploading it
  2. Submitting a batch for processing
  3. Polling for batch completion with exponential backoff
  4. Retrieving and parsing results from output files
  5. Batch lifecycle: list, retrieve, cancel
  6. Cleanup of uploaded and output files

Requirements:
  pip install openai termcolor

Usage:
  export INFERENCE_MODEL="openai/gpt-4o-mini"
  python batch_processing.py
"""

import json
import os
import sys
import time
from io import BytesIO

try:
    from openai import OpenAI
except ImportError:
    print("Missing dependency: pip install openai")
    sys.exit(1)

try:
    from termcolor import colored
except ImportError:
    print("Missing dependency: pip install termcolor")
    sys.exit(1)


def get_client():
    """Create an OpenAI client pointed at OGX."""
    port = os.environ.get("OGX_PORT", "8321")
    return OpenAI(base_url=f"http://localhost:{port}/v1", api_key="unused")


def get_model():
    """Get the model ID from environment or use a default."""
    return os.environ.get("INFERENCE_MODEL", "openai/gpt-4o-mini")


def upload_batch_file(client, requests):
    """Upload a JSONL batch input file and return the file object."""
    jsonl_content = "\n".join(json.dumps(req) for req in requests)
    file_bytes = jsonl_content.encode("utf-8")

    buf = BytesIO(file_bytes)
    buf.name = "batch_input.jsonl"

    uploaded = client.files.create(file=buf, purpose="batch")
    return uploaded


def wait_for_batch(client, batch_id, max_wait=180, label="batch"):
    """Poll a batch until it reaches a terminal state, using exponential backoff.

    Returns the final batch object, or None if it times out.
    """
    terminal = {"completed", "failed", "cancelled", "expired"}
    interval = 0.5
    max_interval = 10.0
    start = time.time()

    while time.time() - start < max_wait:
        batch = client.batches.retrieve(batch_id)
        elapsed = int(time.time() - start)
        print(f"    [{elapsed}s] {label} status: {batch.status}", end="\r", flush=True)

        if batch.status in terminal:
            print()  # clear the \r line
            return batch

        time.sleep(interval)
        interval = min(interval * 2, max_interval)

    print()
    print(colored(f"    Timed out after {max_wait}s (status: {batch.status})", "yellow"))
    return None


def demo_create_and_process(client, model):
    """Full end-to-end: create batch input, submit, wait, retrieve results."""
    print(colored("=" * 70, "yellow"))
    print(colored("1. End-to-End Batch Processing", "yellow", attrs=["bold"]))
    print(colored("=" * 70, "yellow"))

    # Build batch requests: each is a self-contained chat completion request
    batch_requests = [
        {
            "custom_id": "capital-france",
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": model,
                "messages": [{"role": "user", "content": "What is the capital of France? One word."}],
                "max_tokens": 20,
            },
        },
        {
            "custom_id": "capital-japan",
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": model,
                "messages": [{"role": "user", "content": "What is the capital of Japan? One word."}],
                "max_tokens": 20,
            },
        },
        {
            "custom_id": "capital-brazil",
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": model,
                "messages": [{"role": "user", "content": "What is the capital of Brazil? One word."}],
                "max_tokens": 20,
            },
        },
    ]

    # Step 1: Upload the input file
    print("  Step 1: Uploading batch input file...")
    uploaded = upload_batch_file(client, batch_requests)
    print(f"    File ID:  {uploaded.id}")
    print(f"    Requests: {len(batch_requests)}")

    # Step 2: Create the batch
    print("  Step 2: Submitting batch...")
    batch = client.batches.create(
        input_file_id=uploaded.id,
        endpoint="/v1/chat/completions",
        completion_window="24h",
        metadata={"experiment": "12-batches-demo", "request_count": str(len(batch_requests))},
    )
    print(f"    Batch ID: {batch.id}")
    print(f"    Status:   {batch.status}")

    # Step 3: Wait for completion
    print("  Step 3: Waiting for completion...")
    final = wait_for_batch(client, batch.id, max_wait=180, label="batch")

    if final is None:
        print(colored("    Batch did not complete in time. Skipping result retrieval.", "yellow"))
        # Clean up the input file
        client.files.delete(uploaded.id)
        print()
        return

    print(f"    Final status: {colored(final.status, 'green' if final.status == 'completed' else 'red')}")

    if final.request_counts:
        rc = final.request_counts
        print(f"    Counts:       {rc.completed} completed, {rc.failed} failed, {rc.total} total")

    # Step 4: Retrieve results
    if final.output_file_id:
        print("  Step 4: Retrieving results...")
        output_content = client.files.content(final.output_file_id)
        if isinstance(output_content, str):
            output_text = output_content
        else:
            output_text = output_content.content.decode("utf-8")

        for line in output_text.strip().split("\n"):
            result = json.loads(line)
            custom_id = result["custom_id"]
            status_code = result["response"]["status_code"]
            body = result["response"]["body"]

            if status_code == 200:
                # Extract the assistant's reply
                choices = body.get("choices", [])
                answer = choices[0]["message"]["content"] if choices else "(no content)"
                print(f"    {colored(custom_id, 'cyan'):30s} -> {colored(answer.strip(), 'green')}")
            else:
                print(f"    {colored(custom_id, 'cyan'):30s} -> {colored(f'error ({status_code})', 'red')}")

        # Clean up output file
        client.files.delete(final.output_file_id)

    # Clean up error file if it exists
    if final.error_file_id:
        print("  (cleaning up error file)")
        client.files.delete(final.error_file_id)

    # Clean up input file
    client.files.delete(uploaded.id)

    print()


def demo_list_and_retrieve(client, model):
    """Demonstrate listing batches and retrieving a specific one."""
    print(colored("=" * 70, "yellow"))
    print(colored("2. List and Retrieve Batches", "yellow", attrs=["bold"]))
    print(colored("=" * 70, "yellow"))

    # Create a small batch to have something to list
    batch_requests = [
        {
            "custom_id": "list-test-1",
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": model,
                "messages": [{"role": "user", "content": "Hi"}],
                "max_tokens": 5,
            },
        },
    ]

    uploaded = upload_batch_file(client, batch_requests)
    batch = client.batches.create(
        input_file_id=uploaded.id,
        endpoint="/v1/chat/completions",
        completion_window="24h",
    )

    # List all batches
    batch_list = client.batches.list()
    print(f"  Total batches visible: {len(batch_list.data)}")

    # Show the most recent ones
    for b in batch_list.data[:5]:
        print(f"    {b.id}  status={b.status}  endpoint={b.endpoint}")

    # Retrieve the one we just created
    retrieved = client.batches.retrieve(batch.id)
    print(f"\n  Retrieved batch {retrieved.id}:")
    print(f"    Status:   {retrieved.status}")
    print(f"    Endpoint: {retrieved.endpoint}")
    print(f"    Window:   {retrieved.completion_window}")
    print(f"    Input:    {retrieved.input_file_id}")

    # Wait for it to finish, then clean up
    final = wait_for_batch(client, batch.id, max_wait=120, label="list-test")
    if final and final.output_file_id:
        client.files.delete(final.output_file_id)
    if final and final.error_file_id:
        client.files.delete(final.error_file_id)
    client.files.delete(uploaded.id)

    print()


def demo_cancel(client, model):
    """Demonstrate batch cancellation."""
    print(colored("=" * 70, "yellow"))
    print(colored("3. Batch Cancellation", "yellow", attrs=["bold"]))
    print(colored("=" * 70, "yellow"))

    batch_requests = [
        {
            "custom_id": "cancel-test-1",
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": model,
                "messages": [{"role": "user", "content": "Write a 500-word essay."}],
                "max_tokens": 500,
            },
        },
    ]

    uploaded = upload_batch_file(client, batch_requests)
    batch = client.batches.create(
        input_file_id=uploaded.id,
        endpoint="/v1/chat/completions",
        completion_window="24h",
    )

    print(f"  Created batch: {batch.id} (status: {batch.status})")

    # Immediately cancel
    try:
        cancelled = client.batches.cancel(batch.id)
        print(f"  Cancel requested: status={cancelled.status}")

        # Wait for cancellation to take effect
        final = wait_for_batch(client, batch.id, max_wait=60, label="cancel")
        if final:
            print(f"  Final status: {colored(final.status, 'cyan')}")
        else:
            print(colored("  Cancellation timed out (batch may have completed first)", "yellow"))
    except Exception as e:
        print(colored(f"  Cancel failed (batch may have already completed): {e}", "yellow"))

    # Clean up
    try:
        final_check = client.batches.retrieve(batch.id)
        if final_check.output_file_id:
            client.files.delete(final_check.output_file_id)
        if final_check.error_file_id:
            client.files.delete(final_check.error_file_id)
    except Exception:
        pass
    client.files.delete(uploaded.id)

    print()


def main():
    client = get_client()
    model = get_model()

    port = os.environ.get("OGX_PORT", "8321")
    print(colored(f"\nOGX server: http://localhost:{port}/v1", "cyan"))
    print(colored(f"Model:      {model}", "cyan"))
    print()

    demo_create_and_process(client, model)
    demo_list_and_retrieve(client, model)
    demo_cancel(client, model)

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
