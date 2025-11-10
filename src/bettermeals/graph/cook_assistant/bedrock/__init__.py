"""
Bedrock Agent Client Module

This module provides the interface and implementations for cook assistant agent clients.
Supports both MCP-based and Runtime-based implementations.
"""

from .interface import AgentClient
from .mcp.client import MCPAgentClient
from .runtime.client import RuntimeAgentClient
from .factory import create_agent_client, invoke_cook_assistant, get_implementation

__all__ = [
    "AgentClient",
    "MCPAgentClient",
    "RuntimeAgentClient",
    "create_agent_client",
    "invoke_cook_assistant",
    "get_implementation",
]

