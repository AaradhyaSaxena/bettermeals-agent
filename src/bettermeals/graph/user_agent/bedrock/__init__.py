"""
Bedrock Agent Client Module

This module provides the interface and implementations for user agent agent clients.
Supports both MCP-based and Runtime-based implementations.
"""

from .interface import AgentClient
from .mcp.client import MCPAgentClient
from .runtime.client import RuntimeAgentClient
from .factory import create_agent_client, invoke_user_agent, get_implementation

__all__ = [
    "AgentClient",
    "MCPAgentClient",
    "RuntimeAgentClient",
    "create_agent_client",
    "invoke_user_agent",
    "get_implementation",
]

