#!/usr/bin/env python3
"""Check available models and shields registered in OGX."""

import os
import sys

import httpx


def main():
    port = os.environ.get("OGX_PORT", "8321")
    base_url = f"http://localhost:{port}"

    print("=" * 60)
    print("OGX Configuration Check")
    print("=" * 60)
    print(f"\nServer: {base_url}\n")

    print("Registered Models:")
    print("-" * 60)
    try:
        response = httpx.get(f"{base_url}/v1/models")
        response.raise_for_status()
        models = response.json()
        if models.get("data"):
            for model in models["data"]:
                model_id = model.get("id") or model.get("identifier") or model.get("model_id", "Unknown")
                model_type = model.get("model_type", "")
                print(f"  {model_id} ({model_type})")
        else:
            print("  No models registered.")
    except httpx.HTTPStatusError as e:
        print(f"  HTTP {e.response.status_code}: {e.response.text}")

    print("\nRegistered Shields:")
    print("-" * 60)
    try:
        response = httpx.get(f"{base_url}/v1/shields")
        response.raise_for_status()
        shields = response.json()
        if shields.get("data"):
            for shield in shields["data"]:
                print(f"  {shield['identifier']} -> {shield.get('provider_resource_id', 'N/A')}")
        else:
            print("  No shields registered.")
    except httpx.HTTPStatusError as e:
        print(f"  HTTP {e.response.status_code}: {e.response.text}")


if __name__ == "__main__":
    try:
        main()
    except httpx.ConnectError:
        port = os.environ.get("OGX_PORT", "8321")
        print(f"Failed to connect to OGX at http://localhost:{port}.", file=sys.stderr)
        print("Start the server with: ogx run <config>.yaml", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(130)
