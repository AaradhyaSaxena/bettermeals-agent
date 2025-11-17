"""
User Agent module for BetterMeals WhatsApp agent.

This module provides an open-ended conversational agent for users using AWS Bedrock/MCP.
It handles user-related queries with AgentCore memory integration for semantic context.
"""

from .service import UserAgentService, user_agent_service
from .memory_config import get_or_create_memory_resource, get_memory_resource_id

__all__ = [
    "UserAgentService",
    "user_agent_service",
    "get_or_create_memory_resource",
    "get_memory_resource_id"
]

