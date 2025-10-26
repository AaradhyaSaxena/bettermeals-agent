"""
Cook Assistant module for BetterMeals WhatsApp agent.

This module provides an open-ended conversational agent for cooks using AWS Bedrock/MCP.
It handles cooking-related queries with conversation history persistence.
"""

from .service import CookAssistantService, cook_assistant_service

__all__ = [
    "CookAssistantService",
    "cook_assistant_service"
]

