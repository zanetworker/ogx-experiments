"""Phase 1: Planning - Capability Selection and Question Specialization."""

import json
from dataclasses import dataclass
from typing import Optional
from openai import OpenAI

from .config import AnalyzeConfig
from .tools import get_tool_names


@dataclass
class SpecializedQuestion:
    capability: str
    original_question: str
    specialized_question: str
    priority: int = 1


@dataclass
class ExecutionPlan:
    original_query: str
    selected_capabilities: list[str]
    specialized_questions: list[SpecializedQuestion]
    reasoning: str


CAPABILITY_SELECTION_SCHEMA = {
    "type": "json_schema",
    "name": "capability_selection",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "selected_capabilities": {"type": "array", "items": {"type": "string"}},
            "reasoning": {"type": "string"}
        },
        "required": ["selected_capabilities", "reasoning"],
        "additionalProperties": False
    }
}

QUESTION_SPECIALIZATION_SCHEMA = {
    "type": "json_schema",
    "name": "specialized_questions",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "questions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "capability": {"type": "string"},
                        "specialized_question": {"type": "string"},
                        "priority": {"type": "integer"}
                    },
                    "required": ["capability", "specialized_question", "priority"],
                    "additionalProperties": False
                }
            }
        },
        "required": ["questions"],
        "additionalProperties": False
    }
}


class Planner:
    """AI-First Planner using LLM for capability selection and question specialization."""

    def __init__(self, client: OpenAI, config: AnalyzeConfig):
        self.client = client
        self.config = config
        self.model = config.models.planner_model

    def plan(self, query: str, user_context: Optional[dict] = None) -> ExecutionPlan:
        available = get_tool_names(self.config)
        selected = self._select_capabilities(query, available)
        specialized = self._specialize_questions(query, selected["selected_capabilities"], user_context)

        questions = [
            SpecializedQuestion(
                capability=q["capability"],
                original_question=query,
                specialized_question=q["specialized_question"],
                priority=q.get("priority", 1)
            )
            for q in specialized["questions"]
        ]

        return ExecutionPlan(
            original_query=query,
            selected_capabilities=selected["selected_capabilities"],
            specialized_questions=questions,
            reasoning=selected["reasoning"]
        )

    def _select_capabilities(self, query: str, available: list) -> dict:
        prompt = f"""Select capabilities for this query.

Available: {json.dumps(available)}
Query: {query}

Select ONLY needed capabilities:
- query_* for department insights
- Dataverse for metrics
- web_search for external info"""

        response = self.client.responses.create(
            model=self.model,
            input=prompt,
            instructions="Select capabilities precisely.",
            tool_choice="none",
            text={"format": CAPABILITY_SELECTION_SCHEMA},
            stream=False
        )
        return json.loads(response.output_text)

    def _specialize_questions(self, query: str, capabilities: list, user_context: Optional[dict] = None) -> dict:
        context_info = f"\nContext: {json.dumps(user_context)}" if user_context else ""
        prompt = f"""Generate specialized questions.

Query: {query}
Capabilities: {json.dumps(capabilities)}{context_info}

Create domain-specific questions with priority (1=highest)."""

        response = self.client.responses.create(
            model=self.model,
            input=prompt,
            instructions="Create precise, domain-specific questions.",
            tool_choice="none",
            text={"format": QUESTION_SPECIALIZATION_SCHEMA},
            stream=False
        )
        return json.loads(response.output_text)

