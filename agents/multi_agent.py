#!/usr/bin/env python3
"""
Multi-agent system using OGX Responses API.

Specialized agents collaborate using previous_response_id to chain responses.
"""

import json
import os
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from openai import OpenAI


@dataclass
class Agent:
    name: str
    instructions: str
    tools: Optional[List[Dict[str, Any]]] = None
    params: Dict[str, Any] = field(default_factory=dict)


def create_agents(mcp_server_url: Optional[str] = None) -> List[Agent]:
    agents = [
        Agent(
            name="Orchestrator",
            instructions="Analyze the request, break it into subtasks, and create a clear execution plan.",
            params={"temperature": 0.7},
        ),
        Agent(
            name="Research",
            instructions="Review the plan, gather information using tools, and organize findings.",
            tools=[{
                "type": "mcp",
                "server_url": mcp_server_url,
                "server_label": "Research Tools",
                "require_approval": "never",
            }] if mcp_server_url else None,
            params={"temperature": 0.3, "max_output_tokens": 2000},
        ),
        Agent(
            name="Analysis",
            instructions="Extract insights from research, identify patterns, and provide recommendations.",
            params={"temperature": 0.5},
        ),
        Agent(
            name="Writer",
            instructions="Create a polished final deliverable based on the analysis.",
            params={"temperature": 0.8, "max_output_tokens": 3000},
        ),
    ]
    return agents


class MultiAgentSystem:
    def __init__(self, ogx_url: str, model_id: str):
        self.client = OpenAI(base_url=f"{ogx_url}/v1", api_key="not-needed")
        self.model_id = model_id
        self.response_ids: List[str] = []

    def _execute_agent(self, agent: Agent, user_query: str, previous_response_id: Optional[str] = None) -> Any:
        print(f"\n{'=' * 80}\n{agent.name}\n{'=' * 80}")

        params = {
            "model": self.model_id,
            "input": user_query,
            "instructions": agent.instructions,
            "stream": False,
        }

        if previous_response_id:
            params["previous_response_id"] = previous_response_id

        if agent.tools:
            params["tools"] = agent.tools
            params["tool_choice"] = "auto"

        params.update(agent.params)

        try:
            response = self.client.responses.create(**params)
        except Exception as e:
            if agent.tools and ("500" in str(e) or "Internal server error" in str(e)):
                print(f"MCP error, retrying without tools...")
                retry_params = {k: v for k, v in params.items() if k not in ("tools", "tool_choice")}
                response = self.client.responses.create(**retry_params)
            else:
                raise

        print(f"Status: {response.status} | ID: {response.id[:16]}...\n")
        self.response_ids.append(response.id)
        self._display_response(response)
        return response

    def _display_response(self, response: Any):
        if not hasattr(response, "output"):
            return

        for item in response.output:
            item_type = getattr(item, "type", None)

            if item_type == "message" and hasattr(item, "content"):
                for content in item.content:
                    if hasattr(content, "text"):
                        print(content.text)

            elif item_type in ("mcp_call", "function_call"):
                print(f"[Tool: {item.name}]")
                if hasattr(item, "arguments"):
                    print(f"  Arguments: {json.dumps(item.arguments, indent=2)}")
                if hasattr(item, "error") and item.error:
                    print(f"  Error: {item.error}")
                elif hasattr(item, "output") and item.output:
                    print(f"  Output: {item.output}")

            elif item_type == "mcp_call_result":
                if hasattr(item, "error") and item.error:
                    print(f"[MCP Error: {item.error}]")
                elif hasattr(item, "content"):
                    print(f"[MCP Result: {item.content}]")

    def run(self, user_query: str, agents: List[Agent]):
        print(f"\nTask: {user_query}")
        print(f"Agents: {' -> '.join(a.name for a in agents)}\n")

        previous_response_id = None
        for agent in agents:
            try:
                response = self._execute_agent(agent, user_query, previous_response_id)
                previous_response_id = response.id
            except Exception as e:
                print(f"Failed at {agent.name}: {e}")
                break

        if self.response_ids:
            print(f"\n{'=' * 80}")
            print(f"Chain: {' -> '.join(rid[:8] for rid in self.response_ids)}")
            print(f"{'=' * 80}")


def main():
    ogx_url = f"http://localhost:{os.environ.get('OGX_PORT', '8321')}"
    model_id = os.environ.get("INFERENCE_MODEL", "openai/gpt-4o-mini")
    mcp_server_url = os.environ.get("MCP_SERVER_URL", "https://mcp.context7.com/mcp")

    print(f"OGX: {ogx_url}")
    print(f"Model: {model_id}")
    print(f"MCP: {mcp_server_url}")

    system = MultiAgentSystem(ogx_url, model_id)
    agents = create_agents(mcp_server_url)

    user_query = "Search OGX documentation and find the best way to do rag"
    system.run(user_query, agents)


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
