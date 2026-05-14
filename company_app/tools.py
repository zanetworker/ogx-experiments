"""
Tool Definitions for the Analyze Application

Defines function tools for:
1. Department queries (qualitative analysis)
2. Dataverse queries (quantitative analysis via SQL)
3. External tools (web search, URL fetch)

Uses Llama Stack Responses API FLAT format:
{type: "function", name, description, parameters}
"""

import json
from typing import Any


# =============================================================================
# Department Tools - For qualitative document-based analysis
# =============================================================================

def create_department_tool(department: str) -> dict:
    """Create a function tool schema for a department agent."""
    return {
        "type": "function",
        "name": f"query_{department}",
        "description": f"Query the {department.title()} department for insights, documents, and expert analysis. "
                      f"Use for qualitative questions about {department}-related topics.",
        "parameters": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": f"The specialized question to ask the {department} department"
                },
                "include_documents": {
                    "type": "boolean",
                    "description": "Whether to search department documents (slower but more comprehensive)",
                    "default": True
                }
            },
            "required": ["question"]
        }
    }


# =============================================================================
# Dataverse Tools - For quantitative SQL-based analysis
# =============================================================================

def create_dataverse_tool(mart: str) -> dict:
    """Create a function tool schema for a Dataverse mart."""
    mart_descriptions = {
        "revenue_master": "Revenue, sales metrics, and financial performance data",
        "apptio": "IT cost management, technology spending, and resource allocation",
        "customer_analytics": "Customer behavior, segmentation, and lifecycle metrics",
        "product_metrics": "Product usage, feature adoption, and performance KPIs"
    }
    
    return {
        "type": "function",
        "name": f"query_{mart}",
        "description": f"Query the {mart.replace('_', ' ').title()} data mart. "
                      f"Contains: {mart_descriptions.get(mart, 'Enterprise data')}. "
                      f"Use for quantitative analysis requiring structured data.",
        "parameters": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "Natural language question to convert to SQL"
                },
                "time_range": {
                    "type": "string",
                    "description": "Time range for the query (e.g., 'last_quarter', 'ytd', 'last_30_days')",
                    "default": "last_quarter"
                }
            },
            "required": ["question"]
        }
    }


# =============================================================================
# External Tools - For web research
# =============================================================================

WEB_SEARCH_TOOL = {
    "type": "function",
    "name": "web_search",
    "description": "Search the web for current information, news, and external research. "
                  "Use for questions requiring up-to-date external information.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query"
            },
            "num_results": {
                "type": "integer",
                "description": "Number of results to return",
                "default": 5
            }
        },
        "required": ["query"]
    }
}

FETCH_URL_TOOL = {
    "type": "function",
    "name": "fetch_url",
    "description": "Fetch and extract content from a specific URL. "
                  "Use when you have a specific URL to retrieve.",
    "parameters": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The URL to fetch"
            }
        },
        "required": ["url"]
    }
}


def get_all_tools(config) -> list:
    """Get all available tools based on configuration."""
    tools = []
    
    # Add department tools
    for dept in config.capabilities.departments:
        tools.append(create_department_tool(dept))
    
    # Add dataverse tools
    for mart in config.capabilities.dataverse_marts:
        tools.append(create_dataverse_tool(mart))
    
    # Add external tools
    tools.append(WEB_SEARCH_TOOL)
    tools.append(FETCH_URL_TOOL)
    
    return tools


def get_tool_names(config) -> list:
    """Get list of all tool names for capability selection."""
    names = []
    names.extend([f"query_{d}" for d in config.capabilities.departments])
    names.extend([f"query_{m}" for m in config.capabilities.dataverse_marts])
    names.extend(["web_search", "fetch_url"])
    return names

