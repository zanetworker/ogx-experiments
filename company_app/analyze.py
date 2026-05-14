"""
Analyze Application - Main Orchestrator

AI-First, Zero Hardcoded Rules query answering system.
Follows the Plan → Execute → Synthesize architecture.

Usage:
    python -m company_app.analyze "What is our Q4 revenue and how does it compare to competitors?"
"""

import time
from dataclasses import dataclass
from typing import Optional
from openai import OpenAI

from .config import AnalyzeConfig, get_config
from .planner import Planner, ExecutionPlan
from .executor import Executor, ExecutionResults
from .synthesizer import Synthesizer, SynthesisResult


@dataclass
class AnalyzeResult:
    """Complete result from the Analyze application."""
    query: str
    plan: ExecutionPlan
    execution: ExecutionResults
    synthesis: SynthesisResult
    total_time: float
    phase_times: dict


class AnalyzeApp:
    """
    Main orchestrator for the Analyze application.
    
    Implements the three-phase workflow:
    1. Plan: Decompose query, select capabilities
    2. Execute: Run capabilities in parallel
    3. Synthesize: Merge results, validate with Guardian
    """
    
    def __init__(self, config: Optional[AnalyzeConfig] = None):
        self.config = config or get_config()
        
        # Initialize OpenAI client pointing to Llama Stack
        self.client = OpenAI(
            base_url=f"{self.config.server.base_url}/v1",
            api_key=self.config.server.api_key
        )
        
        # Initialize components
        self.planner = Planner(self.client, self.config)
        self.executor = Executor(self.client, self.config)
        self.synthesizer = Synthesizer(self.client, self.config)
    
    def analyze(
        self, 
        query: str, 
        user_context: Optional[dict] = None,
        verbose: bool = True
    ) -> AnalyzeResult:
        """
        Analyze a user query using the Plan → Execute → Synthesize workflow.
        
        Args:
            query: Natural language query
            user_context: Optional user context for personalization
            verbose: Whether to print progress
        
        Returns:
            AnalyzeResult with complete analysis
        """
        total_start = time.time()
        phase_times = {}
        
        # =====================================================================
        # Phase 1: Planning (2-5 seconds target)
        # =====================================================================
        if verbose:
            print("\n" + "=" * 70)
            print("📋 PHASE 1: PLANNING")
            print("=" * 70)
        
        plan_start = time.time()
        plan = self.planner.plan(query, user_context)
        phase_times["planning"] = time.time() - plan_start
        
        if verbose:
            print(f"\n⏱️  Planning time: {phase_times['planning']:.2f}s")
            print(f"📌 Selected capabilities: {plan.selected_capabilities}")
            print(f"💭 Reasoning: {plan.reasoning}")
            print(f"\n📝 Specialized questions:")
            for q in plan.specialized_questions:
                print(f"   • [{q.capability}] {q.specialized_question}")
        
        # =====================================================================
        # Phase 2: Execution (30-90 seconds target)
        # =====================================================================
        if verbose:
            print("\n" + "=" * 70)
            print("⚡ PHASE 2: PARALLEL EXECUTION")
            print("=" * 70)
        
        exec_start = time.time()
        execution = self.executor.execute(plan.specialized_questions)
        phase_times["execution"] = time.time() - exec_start
        
        if verbose:
            print(f"\n⏱️  Execution time: {phase_times['execution']:.2f}s")
            print(f"✅ Successful: {execution.successful}")
            print(f"❌ Failed: {execution.failed}")
            for result in execution.results:
                status = "✅" if not result.error else "❌"
                print(f"\n   {status} [{result.capability}] ({result.execution_time:.2f}s)")
                if result.error:
                    print(f"      Error: {result.error}")
                else:
                    preview = result.response[:100].replace('\n', ' ')
                    print(f"      Preview: {preview}...")
        
        # =====================================================================
        # Phase 3: Synthesis & Validation (7-20 seconds target)
        # =====================================================================
        if verbose:
            print("\n" + "=" * 70)
            print("🔬 PHASE 3: SYNTHESIS & GUARDIAN VALIDATION")
            print("=" * 70)
        
        synth_start = time.time()
        synthesis = self.synthesizer.synthesize(query, execution)
        phase_times["synthesis"] = time.time() - synth_start
        
        if verbose:
            print(f"\n⏱️  Synthesis time: {phase_times['synthesis']:.2f}s")
            print(f"🛡️  Guardian violations: {len(synthesis.violations)}")
            print(f"🔧 Was remediated: {synthesis.was_remediated}")
            print(f"📊 Confidence: {synthesis.confidence:.0%}")
            print(f"\n📚 Citations: {synthesis.citations}")
        
        total_time = time.time() - total_start
        
        return AnalyzeResult(
            query=query,
            plan=plan,
            execution=execution,
            synthesis=synthesis,
            total_time=total_time,
            phase_times=phase_times
        )


def main():
    """CLI entry point for the Analyze application."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m company_app.analyze 'Your query here'")
        print("\nExample queries:")
        print("  - 'What is our Q4 revenue and how does it compare to competitors?'")
        print("  - 'What are the top engineering priorities and their status?'")
        print("  - 'Summarize recent product launches and customer feedback'")
        sys.exit(1)
    
    query = " ".join(sys.argv[1:])
    
    print("\n" + "=" * 70)
    print("🔍 ANALYZE APPLICATION")
    print("=" * 70)
    print(f"\n📝 Query: {query}")
    
    app = AnalyzeApp()
    result = app.analyze(query)
    
    # Print final response
    print("\n" + "=" * 70)
    print("📊 FINAL RESPONSE")
    print("=" * 70)
    print(f"\n{result.synthesis.response}")
    
    # Print summary
    print("\n" + "=" * 70)
    print("📈 SUMMARY")
    print("=" * 70)
    print(f"Total time: {result.total_time:.2f}s")
    print(f"  • Planning: {result.phase_times['planning']:.2f}s")
    print(f"  • Execution: {result.phase_times['execution']:.2f}s")
    print(f"  • Synthesis: {result.phase_times['synthesis']:.2f}s")
    print(f"Confidence: {result.synthesis.confidence:.0%}")


if __name__ == "__main__":
    main()

