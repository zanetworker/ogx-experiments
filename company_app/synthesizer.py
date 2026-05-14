"""Phase 3: Synthesis and Guardian Validation."""

import json
import httpx
from dataclasses import dataclass, field
from typing import Optional
from openai import OpenAI

from .config import AnalyzeConfig
from .executor import ExecutionResults


@dataclass
class GuardianViolation:
    violation_type: str
    severity: float
    description: str
    affected_text: str
    remediation: Optional[str] = None


@dataclass
class SynthesisResult:
    original_query: str
    response: str
    citations: list[str]
    violations: list[GuardianViolation] = field(default_factory=list)
    was_remediated: bool = False
    confidence: float = 0.0


class Synthesizer:
    """Merges execution results and validates with Guardian."""

    def __init__(self, client: OpenAI, config: AnalyzeConfig):
        self.client = client
        self.config = config
        self.reasoning_model = config.models.reasoning_model

    def synthesize(self, query: str, execution_results: ExecutionResults) -> SynthesisResult:
        merged_response, all_citations = self._merge_results(query, execution_results)
        violations, was_remediated, final_response = [], False, merged_response

        if self.config.enable_guardian:
            violations = self._run_guardian_checks(query, merged_response)
            if violations:
                final_response, all_citations, was_remediated = self._remediate(merged_response, all_citations, violations)

        return SynthesisResult(
            original_query=query, response=final_response, citations=all_citations,
            violations=violations, was_remediated=was_remediated,
            confidence=self._calculate_confidence(execution_results, violations)
        )

    def _merge_results(self, query: str, results: ExecutionResults) -> tuple[str, list[str]]:
        context_parts, all_citations = [], []
        for r in results.results:
            if not r.error:
                context_parts.append(f"### {r.capability}\n{r.response}")
                all_citations.extend(r.citations)

        response = self.client.responses.create(
            model=self.reasoning_model,
            input=f"Synthesize into comprehensive answer.\n\nQuestion: {query}\n\nInfo:\n{chr(10).join(context_parts)}",
            instructions="Synthesize accurately, cite sources, note conflicts.",
            tool_choice="none", stream=False
        )
        return response.output_text, list(set(all_citations))

    def _run_guardian_checks(self, query: str, response: str) -> list[GuardianViolation]:
        violations = []
        try:
            with httpx.Client() as http:
                result = http.post(
                    f"{self.config.server.base_url}/v1/safety/run-shield",
                    json={"shield_id": self.config.models.safety_model,
                          "messages": [{"role": "user", "content": query}, {"role": "assistant", "content": response}]},
                    timeout=30.0
                ).json()
                if result.get("violation"):
                    v = result["violation"]
                    violations.append(GuardianViolation(violation_type="safety", severity=0.9,
                                                        description=str(v.get("metadata", "Safety violation")), affected_text=response[:100]))
        except Exception:
            pass
        return violations

    def _remediate(self, response: str, citations: list[str], violations: list[GuardianViolation]) -> tuple[str, list[str], bool]:
        if not violations:
            return response, citations, False
        high = [v for v in violations if v.severity >= self.config.hallucination_threshold]
        if high:
            remediated = self.client.responses.create(
                model=self.reasoning_model,
                input=f"Rewrite removing issues:\n{response}\n\nIssues: {json.dumps([{'type': v.violation_type, 'desc': v.description} for v in high])}",
                instructions="Remove unsupported claims, preserve accuracy.",
                tool_choice="none", stream=False
            )
            return remediated.output_text, citations, True
        return response, citations, False

    def _calculate_confidence(self, results: ExecutionResults, violations: list[GuardianViolation]) -> float:
        if not results.results:
            return 0.0
        avg = sum(r.confidence for r in results.results if not r.error) / max(1, results.successful)
        penalty = sum(v.severity * 0.1 for v in violations) + (results.failed / len(results.results)) * 0.2
        return round(max(0.0, min(1.0, avg - penalty)), 2)
