"""Phase 2: Parallel Execution Engine."""

import json
import time
from dataclasses import dataclass, field
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI

from .config import AnalyzeConfig
from .planner import SpecializedQuestion


@dataclass
class ExecutionResult:
    capability: str
    question: str
    response: str
    confidence: float = 0.0
    citations: list = field(default_factory=list)
    execution_time: float = 0.0
    error: Optional[str] = None


@dataclass
class ExecutionResults:
    results: list[ExecutionResult]
    total_time: float
    successful: int
    failed: int


class Executor:
    """Parallel execution of specialized questions."""

    def __init__(self, client: OpenAI, config: AnalyzeConfig):
        self.client = client
        self.config = config
        self.reasoning_model = config.models.reasoning_model
        self.planner_model = config.models.planner_model

    def execute(self, questions: list[SpecializedQuestion]) -> ExecutionResults:
        start_time = time.time()
        results = []

        with ThreadPoolExecutor(max_workers=self.config.max_parallel_executions) as executor:
            future_to_question = {executor.submit(self._execute_single, q): q for q in questions}
            for future in as_completed(future_to_question, timeout=self.config.execution_timeout):
                question = future_to_question[future]
                try:
                    results.append(future.result())
                except Exception as e:
                    results.append(ExecutionResult(
                        capability=question.capability, question=question.specialized_question,
                        response="", error=str(e)
                    ))

        total_time = time.time() - start_time
        successful = sum(1 for r in results if r.error is None)
        return ExecutionResults(results=results, total_time=total_time, successful=successful, failed=len(results) - successful)

    def _execute_single(self, question: SpecializedQuestion) -> ExecutionResult:
        start_time = time.time()

        if question.capability.startswith("query_"):
            name = question.capability[6:]
            if name in self.config.capabilities.departments:
                result = self._execute_department(question, name)
            elif name in self.config.capabilities.dataverse_marts:
                result = self._execute_dataverse(question, name)
            else:
                result = ExecutionResult(capability=question.capability, question=question.specialized_question, response="", error=f"Unknown: {question.capability}")
        elif question.capability == "web_search":
            result = self._execute_web_search(question)
        elif question.capability == "fetch_url":
            result = self._execute_fetch_url(question)
        else:
            result = ExecutionResult(capability=question.capability, question=question.specialized_question, response="", error=f"Unknown: {question.capability}")

        result.execution_time = time.time() - start_time
        return result

    def _execute_department(self, question: SpecializedQuestion, dept: str) -> ExecutionResult:
        response = self.client.responses.create(
            model=self.reasoning_model,
            input=question.specialized_question,
            instructions=f"You are the {dept.title()} department expert. Provide detailed insights with data points.",
            tool_choice="none", stream=False
        )
        confidence = self._extract_confidence(response.output_text)
        citations = [f"[{dept.upper()}-DOC-001]"] if confidence < self.config.confidence_skip_threshold else []
        return ExecutionResult(
            capability=question.capability, question=question.specialized_question,
            response=response.output_text, confidence=confidence, citations=citations
        )

    def _execute_dataverse(self, question: SpecializedQuestion, mart: str) -> ExecutionResult:
        # Simulate SQL workflow
        mock_results = {"rows": [["Revenue", "$1.2M", "Q4 2024"], ["Growth", "15%", "YoY"], ["Customers", "1,234", "Active"]]}
        format_response = self.client.responses.create(
            model=self.planner_model,
            input=f"Summarize: {json.dumps(mock_results)}\nQuestion: {question.specialized_question}",
            instructions="Create concise summary with key metrics.",
            tool_choice="none", stream=False
        )
        return ExecutionResult(
            capability=question.capability, question=question.specialized_question,
            response=format_response.output_text, confidence=0.95, citations=[f"[{mart.upper()}-SQL]"]
        )

    def _execute_web_search(self, question: SpecializedQuestion) -> ExecutionResult:
        mock = [{"title": "Industry Report 2024", "snippet": "Key trends..."}, {"title": "Competitor Analysis", "snippet": "Market share..."}]
        text = f"Web search: {question.specialized_question}\n" + "\n".join(f"{i}. {r['title']}: {r['snippet']}" for i, r in enumerate(mock, 1))
        return ExecutionResult(capability=question.capability, question=question.specialized_question, response=text, confidence=0.7, citations=["[WEB-001]", "[WEB-002]"])

    def _execute_fetch_url(self, question: SpecializedQuestion) -> ExecutionResult:
        return ExecutionResult(capability=question.capability, question=question.specialized_question, response=f"Fetched: {question.specialized_question}", confidence=0.8, citations=["[URL-001]"])

    def _extract_confidence(self, response: str) -> float:
        r = response.lower()
        if "high confidence" in r or "confident" in r: return 0.9
        if "moderate" in r or "likely" in r: return 0.7
        if "uncertain" in r: return 0.4
        return 0.6
