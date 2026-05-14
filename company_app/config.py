"""
Configuration for the Analyze Application

Model Strategy (from context.md):
- Gemini 2.5 Flash (30%): Low-cost, high-speed tasks - planning, routing, formatting
- Gemini 3.0 Pro (60%): Complex reasoning - document analysis, synthesis
- Opus 4.5 (10%): Optional advanced orchestration for ambiguous queries
- Granite Guardian 3.3 (100%): AI safety validation on every response
"""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ModelConfig:
    """Model configuration with role-based selection."""
    
    # Fast model for planning and routing (Gemini Flash equivalent)
    planner_model: str = field(default_factory=lambda: os.environ.get(
        "PLANNER_MODEL", "meta-llama/Llama-3.2-3B-Instruct"
    ))
    
    # Powerful model for reasoning and synthesis (Gemini Pro equivalent)
    reasoning_model: str = field(default_factory=lambda: os.environ.get(
        "REASONING_MODEL", "meta-llama/Llama-3.3-70B-Instruct"
    ))
    
    # Optional advanced model for complex orchestration (Opus equivalent)
    advanced_model: Optional[str] = field(default_factory=lambda: os.environ.get(
        "ADVANCED_MODEL", None
    ))
    
    # Safety model (Granite Guardian equivalent)
    safety_model: str = field(default_factory=lambda: os.environ.get(
        "SAFETY_MODEL", "llama-guard"
    ))


@dataclass
class ServerConfig:
    """Llama Stack server configuration."""
    
    base_url: str = field(default_factory=lambda: 
        f"http://localhost:{os.environ.get('LLAMA_STACK_PORT', '8321')}"
    )
    api_key: str = "not-needed"
    timeout: float = 120.0


@dataclass
class CapabilityConfig:
    """Available capabilities for the Analyze application."""
    
    # Department agents for qualitative analysis
    departments: list = field(default_factory=lambda: [
        "finance", "product", "engineering", "sales", 
        "marketing", "hr", "legal", "operations", "strategy"
    ])
    
    # Dataverse marts for quantitative analysis
    dataverse_marts: list = field(default_factory=lambda: [
        "revenue_master", "apptio", "customer_analytics", "product_metrics"
    ])
    
    # External tools for web research
    external_tools: list = field(default_factory=lambda: [
        "web_search", "fetch_url"
    ])


@dataclass
class AnalyzeConfig:
    """Main configuration for the Analyze application."""
    
    models: ModelConfig = field(default_factory=ModelConfig)
    server: ServerConfig = field(default_factory=ServerConfig)
    capabilities: CapabilityConfig = field(default_factory=CapabilityConfig)
    
    # Execution settings
    max_parallel_executions: int = 10
    execution_timeout: float = 90.0  # 30-90 seconds per context.md
    
    # Planning settings
    planning_timeout: float = 5.0  # 2-5 seconds per context.md
    
    # Synthesis settings
    synthesis_timeout: float = 20.0  # 7-20 seconds per context.md
    
    # Guardian settings
    enable_guardian: bool = True
    hallucination_threshold: float = 0.80  # 80% risk threshold
    
    # Confidence threshold for skipping document search
    confidence_skip_threshold: float = 0.85


def get_config() -> AnalyzeConfig:
    """Get the application configuration."""
    return AnalyzeConfig()

