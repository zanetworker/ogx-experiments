#!/usr/bin/env python3
"""Structured output via OGX Responses API using json_schema response format."""

import json
import os
import sys

from openai import OpenAI


def get_client():
    port = os.environ.get("OGX_PORT", "8321")
    return OpenAI(base_url=f"http://localhost:{port}/v1", api_key="unused")


def get_model():
    return os.environ.get("INFERENCE_MODEL", "openai/gpt-4o-mini")


def demo_string_fields(client, model):
    """Simple schema with string-only fields."""
    print("=" * 60)
    print("1. String Fields (Person Profile)")
    print("=" * 60)

    text_format = {
        "type": "json_schema",
        "name": "PersonProfile",
        "schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "occupation": {"type": "string"},
                "city": {"type": "string"},
            },
            "required": ["name", "occupation", "city"],
            "additionalProperties": False,
        },
        "strict": True,
    }

    response = client.responses.create(
        model=model,
        input="Generate a profile for Tom, a 30-year-old software engineer in Raleigh.",
        stream=False,
        text={"format": text_format},
    )

    data = json.loads(response.output_text)
    print(f"  Output: {json.dumps(data, indent=2)}")

    assert isinstance(data, dict), "Expected a dict"
    assert all(isinstance(data[k], str) for k in ["name", "occupation", "city"]), "All fields should be strings"
    print("  [validated]\n")


def demo_nested_objects(client, model):
    """Schema with nested object structures."""
    print("=" * 60)
    print("2. Nested Objects (Employee + Department)")
    print("=" * 60)

    text_format = {
        "type": "json_schema",
        "name": "EmployeeRecord",
        "schema": {
            "type": "object",
            "properties": {
                "employee": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "employee_id": {"type": "integer"},
                    },
                    "required": ["name", "employee_id"],
                    "additionalProperties": False,
                },
                "department": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "manager": {"type": "string"},
                    },
                    "required": ["name", "manager"],
                    "additionalProperties": False,
                },
            },
            "required": ["employee", "department"],
            "additionalProperties": False,
        },
        "strict": True,
    }

    response = client.responses.create(
        model=model,
        input="Generate an employee record for Susan (ID 1001) in Engineering managed by Frank.",
        stream=False,
        text={"format": text_format},
    )

    data = json.loads(response.output_text)
    print(f"  Output: {json.dumps(data, indent=2)}")

    assert isinstance(data["employee"], dict), "employee should be a dict"
    assert isinstance(data["department"], dict), "department should be a dict"
    assert isinstance(data["employee"]["employee_id"], int), "employee_id should be an int"
    print("  [validated]\n")


def demo_enum_constraints(client, model):
    """Schema with enum constraints for classification tasks."""
    print("=" * 60)
    print("3. Enum Constraints (Priority Classification)")
    print("=" * 60)

    text_format = {
        "type": "json_schema",
        "name": "TicketClassification",
        "schema": {
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "priority": {
                    "type": "string",
                    "enum": ["critical", "high", "medium", "low"],
                },
                "category": {
                    "type": "string",
                    "enum": ["bug", "feature_request", "question", "documentation"],
                },
            },
            "required": ["summary", "priority", "category"],
            "additionalProperties": False,
        },
        "strict": True,
    }

    response = client.responses.create(
        model=model,
        input=(
            "Classify this support ticket: 'The login page crashes when I enter my "
            "password. This is blocking all users from accessing the system.'"
        ),
        stream=False,
        text={"format": text_format},
    )

    data = json.loads(response.output_text)
    print(f"  Output: {json.dumps(data, indent=2)}")

    valid_priorities = {"critical", "high", "medium", "low"}
    valid_categories = {"bug", "feature_request", "question", "documentation"}
    assert data["priority"] in valid_priorities, f"priority must be one of {valid_priorities}"
    assert data["category"] in valid_categories, f"category must be one of {valid_categories}"
    print(f"  [validated: priority={data['priority']}, category={data['category']}]\n")


def demo_array_of_objects(client, model):
    """Schema with an array of objects."""
    print("=" * 60)
    print("4. Array of Objects (Team Roster)")
    print("=" * 60)

    text_format = {
        "type": "json_schema",
        "name": "TeamRoster",
        "schema": {
            "type": "object",
            "properties": {
                "team_name": {"type": "string"},
                "members": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "role": {"type": "string"},
                        },
                        "required": ["name", "role"],
                        "additionalProperties": False,
                    },
                },
            },
            "required": ["team_name", "members"],
            "additionalProperties": False,
        },
        "strict": True,
    }

    response = client.responses.create(
        model=model,
        input="Generate a team called Platform with three members: Alice as lead, Bob as backend, Carol as frontend.",
        stream=False,
        text={"format": text_format},
    )

    data = json.loads(response.output_text)
    print(f"  Output: {json.dumps(data, indent=2)}")

    assert isinstance(data["members"], list), "members should be a list"
    assert len(data["members"]) > 0, "should have at least one member"
    for member in data["members"]:
        assert "name" in member and "role" in member, "each member needs name and role"
    print(f"  [validated: {len(data['members'])} members]\n")


def demo_mixed_types(client, model):
    """Complex schema mixing strings, integers, floats, booleans, arrays, and nested objects."""
    print("=" * 60)
    print("5. Mixed Types (Full Profile)")
    print("=" * 60)

    text_format = {
        "type": "json_schema",
        "name": "FullProfile",
        "schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
                "salary": {"type": "number"},
                "is_active": {"type": "boolean"},
                "skills": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "address": {
                    "type": "object",
                    "properties": {
                        "street": {"type": "string"},
                        "city": {"type": "string"},
                        "zipcode": {"type": "integer"},
                    },
                    "required": ["street", "city", "zipcode"],
                    "additionalProperties": False,
                },
            },
            "required": ["name", "age", "salary", "is_active", "skills", "address"],
            "additionalProperties": False,
        },
        "strict": True,
    }

    response = client.responses.create(
        model=model,
        input=(
            "Generate a profile for Grace, age 35, salary $120000, active, "
            "skills Python and SQL, living at 123 Main St in Raleigh, zipcode 27601."
        ),
        stream=False,
        text={"format": text_format},
    )

    data = json.loads(response.output_text)
    print(f"  Output: {json.dumps(data, indent=2)}")

    assert isinstance(data["name"], str), "name should be str"
    assert isinstance(data["age"], int), "age should be int"
    assert isinstance(data["salary"], (int, float)), "salary should be numeric"
    assert isinstance(data["is_active"], bool), "is_active should be bool"
    assert isinstance(data["skills"], list), "skills should be list"
    assert isinstance(data["address"], dict), "address should be dict"
    assert isinstance(data["address"]["zipcode"], int), "zipcode should be int"
    print("  [validated]\n")


def main():
    client = get_client()
    model = get_model()
    port = os.environ.get("OGX_PORT", "8321")

    print(f"Server: http://localhost:{port}/v1")
    print(f"Model:  {model}\n")

    demo_string_fields(client, model)
    demo_nested_objects(client, model)
    demo_enum_constraints(client, model)
    demo_array_of_objects(client, model)
    demo_mixed_types(client, model)

    print("All demos completed successfully.")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as e:
        print(f"Validation failed: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        if "Connection" in type(e).__name__ or "connection" in str(e).lower():
            port = os.environ.get("OGX_PORT", "8321")
            print(f"Failed to connect to OGX at http://localhost:{port}.", file=sys.stderr)
            print("Start the server with: ogx run <config>.yaml", file=sys.stderr)
        else:
            print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(130)
