"""
Analyze Application - AI-First Query Answering System

An advanced AI orchestration system that answers complex queries by leveraging
internal and external data sources using the Plan → Execute → Synthesize pattern.

Built with Llama Stack Responses API.
"""

from .config import AnalyzeConfig, get_config
from .analyze import AnalyzeApp, AnalyzeResult

__all__ = [
    "AnalyzeApp",
    "AnalyzeResult", 
    "AnalyzeConfig",
    "get_config"
]

__version__ = "0.1.0"

