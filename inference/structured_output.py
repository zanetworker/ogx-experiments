#!/usr/bin/env python3
"""
Structured Output via OGX Responses API

Demonstrates using json_schema response format to get structured, validated
JSON output from models. OGX supports the same structured output interface
as the OpenAI Responses API, including strict mode.

Features shown:
  1. Simple string-field schema (person profile)
  2. Nested objects (employee with department)
  3. Enum constraints (priority classification)
  4. Array of objects (team roster)
  5. Mixed types in a single schema

Requirements:
  pip install openai termcolor

Usage:
  # Start OGX on port 8321 (default)
  export INFERENCE_MODEL="openai/gpt-4o-mini"  # or any model registered in OGX
  python 11-structured-output.py
"""

import json
import os
import sys

from openai import OpenAI
from termcolor import colored


def get_client():
    """Create an OpenAI client pointed at OGX."""
    port = os.environ.get("OGX_PORT", "8321")
    return OpenAI(base_url=f"http://localhost:{port}/v1", api_key="unused")


def get_model():
    """Get the model ID from environment or use a default."""
    return os.environ.get("INFERENCE_MODEL", "openai/gpt-4o-mini")


def demo_string_fields(client, model):
    """Simple schema with string-only fields."""
    print(colored("=" * 70, "yellow"))
    print(colored("1. String Fields (Person Profile)", "yellow", attrs=["bold"]))
    print(colored("=" * 70, "yellow"))

    text_format = {
        "type": "json_schema",
        "name": "PersonProfile",
        "description": "A profile with multiple string fields",
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
    print(f"  Schema:  PersonProfile (3 string fields)")
    print(f"  Output:  {colored(json.dumps(data, indent=2), 'green')}")

    # Validate structure
    assert isinstance(data, dict), "Expected a dict"
    assert all(isinstance(data[k], str) for k in ["name", "occupation", "city"]), "All fields should be strings"
    print(colored("  [validated: all fields are strings]", "cyan"))
    print()


def demo_nested_objects(client, model):
    """Schema with nested object structures."""
    print(colored("=" * 70, "yellow"))
    print(colored("2. Nested Objects (Employee + Department)", "yellow", attrs=["bold"]))
    print(colored("=" * 70, "yellow"))

    text_format = {
        "type": "json_schema",
        "name": "EmployeeRecord",
        "description": "An employee with nested department information",
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
    print(f"  Schema:  EmployeeRecord (2 nested objects)")
    print(f"  Output:  {colored(json.dumps(data, indent=2), 'green')}")

    # Validate nesting
    assert isinstance(data["employee"], dict), "employee should be a dict"
    assert isinstance(data["department"], dict), "department should be a dict"
    assert isinstance(data["employee"]["employee_id"], int), "employee_id should be an int"
    print(colored("  [validated: nested objects with correct types]", "cyan"))
    print()


def demo_enum_constraints(client, model):
    """Schema with enum constraints for classification tasks."""
    print(colored("=" * 70, "yellow"))
    print(colored("3. Enum Constraints (Priority Classification)", "yellow", attrs=["bold"]))
    print(colored("=" * 70, "yellow"))

    text_format = {
        "type": "json_schema",
        "name": "TicketClassification",
        "description": "A support ticket with priority and category classification",
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
    print(f"  Schema:  TicketClassification (enum-constrained)")
    print(f"  Output:  {colored(json.dumps(data, indent=2), 'green')}")

    # Validate enums
    valid_priorities = {"critical", "high", "medium", "low"}
    valid_categories = {"bug", "feature_request", "question", "documentation"}
    assert data["priority"] in valid_priorities, f"priority must be one of {valid_priorities}"
    assert data["category"] in valid_categories, f"category must be one of {valid_categories}"
    print(colored(f"  [validated: priority={data['priority']}, category={data['category']}]", "cyan"))
    print()


def demo_array_of_objects(client, model):
    """Schema with an array of objects."""
    print(colored("=" * 70, "yellow"))
    print(colored("4. Array of Objects (Team Roster)", "yellow", attrs=["bold"]))
    print(colored("=" * 70, "yellow"))

    text_format = {
        "type": "json_schema",
        "name": "TeamRoster",
        "description": "A team with multiple members",
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
    print(f"  Schema:  TeamRoster (array of objects)")
    print(f"  Output:  {colored(json.dumps(data, indent=2), 'green')}")

    # Validate array structure
    assert isinstance(data["members"], list), "members should be a list"
    assert len(data["members"]) > 0, "should have at least one member"
    for member in data["members"]:
        assert "name" in member and "role" in member, "each member needs name and role"
    print(colored(f"  [validated: {len(data['members'])} members with name+role]", "cyan"))
    print()


def demo_mixed_types(client, model):
    """Complex schema mixing strings, integers, floats, booleans, arrays, and nested objects."""
    print(colored("=" * 70, "yellow"))
    print(colored("5. Mixed Types (Full Profile)", "yellow", attrs=["bold"]))
    print(colored("=" * 70, "yellow"))

    text_format = {
        "type": "json_schema",
        "name": "FullProfile",
        "description": "Complex profile with mixed types",
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
    print(f"  Schema:  FullProfile (string, int, float, bool, array, nested object)")
    print(f"  Output:  {colored(json.dumps(data, indent=2), 'green')}")

    # Validate types
    assert isinstance(data["name"], str), "name should be str"
    assert isinstance(data["age"], int), "age should be int"
    assert isinstance(data["salary"], (int, float)), "salary should be numeric"
    assert isinstance(data["is_active"], bool), "is_active should be bool"
    assert isinstance(data["skills"], list), "skills should be list"
    assert isinstance(data["address"], dict), "address should be dict"
    assert isinstance(data["address"]["zipcode"], int), "zipcode should be int"

    types_found = {
        "string": type(data["name"]).__name__,
        "integer": type(data["age"]).__name__,
        "number": type(data["salary"]).__name__,
        "boolean": type(data["is_active"]).__name__,
        "array": type(data["skills"]).__name__,
        "object": type(data["address"]).__name__,
    }
    print(colored(f"  [validated: {types_found}]", "cyan"))
    print()


def main():
    client = get_client()
    model = get_model()

    port = os.environ.get("OGX_PORT", "8321")
    print(colored(f"\nOGX server: http://localhost:{port}/v1", "cyan"))
    print(colored(f"Model:      {model}", "cyan"))
    print()

    try:
        demo_string_fields(client, model)
        demo_nested_objects(client, model)
        demo_enum_constraints(client, model)
        demo_array_of_objects(client, model)
        demo_mixed_types(client, model)
    except Exception as e:
        print(colored(f"\nError: {e}", "red"))
        print(colored("Make sure OGX is running and the model is available.", "red"))
        sys.exit(1)

    print(colored("All demos completed successfully.", "green"))


if __name__ == "__main__":
    main()
