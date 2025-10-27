"""
Cook Assistant module for BetterMeals WhatsApp agent.

This module provides an open-ended conversational agent for cooks using AWS Bedrock/MCP.
It handles cooking-related queries with AgentCore memory integration for semantic context.
"""

from .service import CookAssistantService, cook_assistant_service
from .memory_config import get_or_create_memory_resource, get_memory_resource_id

__all__ = [
    "CookAssistantService",
    "cook_assistant_service",
    "get_or_create_memory_resource",
    "get_memory_resource_id"
]

