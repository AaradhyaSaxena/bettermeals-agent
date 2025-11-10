"""
Bedrock Agent Client Module

This module provides the interface and implementations for cook assistant agent clients.
Currently supports MCP-based implementation, with runtime implementation coming soon.
"""

from .interface import AgentClient
from .mcp.client import MCPAgentClient, invoke_cook_assistant

__all__ = [
    "AgentClient",
    "MCPAgentClient",
    "invoke_cook_assistant",
]

