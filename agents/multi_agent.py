#!/usr/bin/env python3
"""
Multi-Agent System using OGX Responses API

Demonstrates specialized agents collaborating using previous_response_id to chain responses.
"""

import json
import os
from typing import List, Dict, Any, Optional
from openai import OpenAI
from termcolor import colored
from dataclasses import dataclass


@dataclass
class Agent:
    name: str
    instructions: str
    tools: Optional[List[Dict[str, Any]]] = None
    params: Optional[Dict[str, Any]] = None  # Additional params like temperature, max_tokens, etc.


def create_agents(mcp_server_url: Optional[str] = None):
    """Create agent instances with optional MCP server configuration"""

    orchestrator = Agent(
        name="Orchestrator",
        instructions="Analyze the request, break it into subtasks, and create a clear execution plan.",
        params={"temperature": 0.7}
    )

    research_agent = Agent(
        name="Research",
        instructions="Review the plan, gather information using tools, and organize findings.",
        tools=[{
            "type": "mcp",
            "server_url": mcp_server_url,
            "server_label": "Research Tools",
            "require_approval": "never"
        }] if mcp_server_url else None,
        params={"temperature": 0.3, "max_output_tokens": 2000}
    )

    analysis_agent = Agent(
        name="Analysis",
        instructions="Extract insights from research, identify patterns, and provide recommendations.",
        params={"temperature": 0.5}
    )

    writing_agent = Agent(
        name="Writer",
        instructions="Create a polished final deliverable based on the analysis.",
        params={"temperature": 0.8, "max_output_tokens": 3000}
    )

    return orchestrator, research_agent, analysis_agent, writing_agent

class MultiAgentSystem:
    def __init__(self, ogx_url: str, model_id: str, mcp_server_url: Optional[str] = None):
        self.client = OpenAI(base_url=f"{ogx_url}/v1", api_key="not-needed")
        self.model_id = model_id
        self.mcp_server_url = mcp_server_url
        self.conversation_history: List[Dict[str, Any]] = []

    def _execute_agent(self, agent: Agent, user_query: str, previous_response_id: Optional[str] = None) -> Any:
        print(f"\n{'='*80}\n{agent.name}\n{'='*80}")

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

        if agent.params:
            params.update(agent.params)

        try:
            response = self.client.responses.create(**params)
            print(f"Status: {response.status} | ID: {response.id[:16]}...\n")

            self.conversation_history.append({
                "agent": agent.name,
                "response_id": response.id,
                "response": response
            })

            self._display_response(response)
            return response
        except Exception as e:
            print(f"Error: {e}")
            # Retry without MCP tools if they cause errors
            if agent.tools and ("500" in str(e) or "Internal server error" in str(e)):
                print(f"Retrying without MCP tools...")
                retry_params = {k: v for k, v in params.items() if k not in ["tools", "tool_choice"]}
                try:
                    response = self.client.responses.create(**retry_params)
                    print(f"Status: {response.status} | ID: {response.id[:16]}...\n")
                    self.conversation_history.append({"agent": agent.name, "response_id": response.id, "response": response})
                    self._display_response(response)
                    return response
                except Exception:
                    pass
            return None

    def _display_response(self, response: Any):
        if not hasattr(response, 'output'):
            return

        for item in response.output:
            if not hasattr(item, 'type'):
                continue

            print(f"[DEBUG] Item type: {item.type}")

            if item.type == "message" and hasattr(item, 'content'):
                for content in item.content:
                    if hasattr(content, 'text'):
                        print(content.text)
            elif item.type in ["mcp_call", "function_call"]:
                print(f"[Tool Call: {item.name}]")
                print(f"  Arguments: {json.dumps(getattr(item, 'arguments', {}), indent=2)}")
                if hasattr(item, 'error') and item.error:
                    print(f"  ERROR: {item.error}")
                if hasattr(item, 'output'):
                    print(f"  Output: {item.output}")
            elif item.type == "mcp_call_result":
                print(f"[MCP Result]")
                if hasattr(item, 'error') and item.error:
                    print(f"  ERROR: {item.error}")
                if hasattr(item, 'content'):
                    print(f"  Content: {item.content}")
            else:
                # Show any other item types for debugging
                print(f"[Unknown type: {item.type}]")
                if hasattr(item, '__dict__'):
                    print(f"  Attributes: {item.__dict__}")

    def run(self, user_query: str, agents: List[Agent]):
        print(f"\nTask: {user_query}\nAgents: {' → '.join([a.name for a in agents])}\n")

        previous_response_id = None
        for agent in agents:
            response = self._execute_agent(agent, user_query, previous_response_id)
            if response:
                previous_response_id = response.id
            else:
                print(f"Failed at {agent.name}")
                break

        print(f"\n{'='*80}\nChain: {' → '.join([e['response_id'][:8] for e in self.conversation_history])}\n{'='*80}")


def main():
    ogx_url = f"http://localhost:{os.environ.get('OGX_PORT', '8321')}"
    model_id = os.environ.get("INFERENCE_MODEL", "openai/gpt-4o")  # Configurable via INFERENCE_MODEL env var
    mcp_server_url = os.environ.get("MCP_SERVER_URL", "https://mcp.context7.com/mcp")

    print(f"Config: OGX={ogx_url}, Model={model_id}, MCP={mcp_server_url}")

    system = MultiAgentSystem(ogx_url, model_id, mcp_server_url)

    # Create agents with MCP configuration
    orchestrator, research_agent, analysis_agent, writing_agent = create_agents(mcp_server_url)

    user_query = "Search OGX documentation and find the best way to do rag"
    agents = [orchestrator, research_agent, analysis_agent, writing_agent]

    system.run(user_query, agents)


if __name__ == "__main__":
    main()
