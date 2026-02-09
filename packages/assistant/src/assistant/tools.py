"""Tool definitions for Bedrock Claude tool-calling."""

from __future__ import annotations

TOOL_DEFINITIONS: list[dict] = [
    {
        "name": "search_threats",
        "description": "Search the OT/ICS threat intelligence database for relevant advisories, threat reports, and incidents.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query describing the threat or topic"},
                "source_type": {
                    "type": "string",
                    "enum": ["advisory", "threat_report", "incident"],
                    "description": "Filter by document type",
                },
                "severity": {
                    "type": "string",
                    "enum": ["critical", "high", "medium", "low"],
                    "description": "Filter by severity level",
                },
                "max_results": {"type": "integer", "description": "Maximum number of results to return", "default": 5},
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_advisory",
        "description": "Retrieve a specific ICS security advisory by its ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "advisory_id": {"type": "string", "description": "The advisory identifier (e.g., ICSA-2024-001)"},
            },
            "required": ["advisory_id"],
        },
    },
    {
        "name": "get_recommendations",
        "description": "Get ML-powered recommendations for related threat intelligence based on the current context.",
        "input_schema": {
            "type": "object",
            "properties": {
                "context": {"type": "string", "description": "Current research context to base recommendations on"},
                "max_results": {"type": "integer", "description": "Maximum number of recommendations", "default": 5},
            },
            "required": ["context"],
        },
    },
]
