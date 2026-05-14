#!/usr/bin/env python3
"""Analyze Application Demo - Plan → Execute → Synthesize with Llama Stack."""

import os
import sys
from termcolor import colored, cprint

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from company_app import AnalyzeApp, get_config


def run_demo(name: str, query: str, user_context: dict = None):
    """Run a single demo."""
    print(colored(f"\n{'='*60}\n {name}\n{'='*60}", "yellow"))
    print(f"\n📝 Query: {colored(query, 'green')}")
    if user_context:
        print(f"👤 Context: {user_context}")

    app = AnalyzeApp()
    result = app.analyze(query, user_context=user_context, verbose=True)

    print(colored(f"\n{'─'*60}\nFinal Response:\n{'─'*60}", "cyan"))
    print(result.synthesis.response)
    print(colored(f"\n✅ {result.total_time:.2f}s | {result.synthesis.confidence:.0%} confidence", "green"))


def main():
    config = get_config()
    print(colored(f"""
╔═══════════════════════════════════════════════════════════╗
║  🔍 ANALYZE - Plan → Execute → Synthesize                 ║
╚═══════════════════════════════════════════════════════════╝
  URL: {config.server.base_url}
  Planner: {config.models.planner_model}
  Reasoning: {config.models.reasoning_model}
""", "cyan"))

    demos = [
        ("Multi-Capability", "What is our Q4 revenue and how does it compare to industry trends?", None),
        ("Department Focus", "What are the top engineering priorities and how is product supporting them?", None),
        ("Personalized", "What are my team's metrics and deadlines?", {"email": "manager@company.com", "department": "engineering"}),
        ("External Research", "What are the latest AI trends and how should we position our product?", None),
    ]

    print("Select demo:")
    for i, (name, _, _) in enumerate(demos, 1):
        print(f"  {i}. {name}")
    print(f"  5. Run all\n  0. Exit")

    try:
        choice = int(input(colored("\nChoice: ", "cyan")))
        if choice == 0:
            return
        elif 1 <= choice <= 4:
            name, query, ctx = demos[choice - 1]
            run_demo(name, query, ctx)
        elif choice == 5:
            for name, query, ctx in demos:
                try:
                    run_demo(name, query, ctx)
                except Exception as e:
                    cprint(f"❌ {name} failed: {e}", "red")
    except (ValueError, KeyboardInterrupt):
        pass


if __name__ == "__main__":
    main()

