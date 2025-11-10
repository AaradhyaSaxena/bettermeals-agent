"""
Bedrock Agent Client Module

This module provides the interface and implementations for cook assistant agent clients.
Supports both MCP-based and Runtime-based implementations.
"""

from .interface import AgentClient
from .mcp.client import MCPAgentClient, invoke_cook_assistant
from .runtime.client import RuntimeAgentClient

__all__ = [
    "AgentClient",
    "MCPAgentClient",
    "RuntimeAgentClient",
    "invoke_cook_assistant",
]

