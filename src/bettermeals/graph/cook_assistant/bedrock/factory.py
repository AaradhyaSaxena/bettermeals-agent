"""
Bedrock Client Configuration and Factory

Handles selection between MCP and Runtime implementations based on configuration.
"""

import os
from typing import Optional
import logging
from .interface import AgentClient
from .mcp.client import MCPAgentClient
from .runtime.client import RuntimeAgentClient
from ..utils import get_ssm_parameter

logger = logging.getLogger(__name__)

# Default implementation
DEFAULT_IMPLEMENTATION = "runtime"


def get_implementation() -> str:
    """
    Get the cook assistant implementation type from environment or SSM.
    
    Returns:
        "mcp" or "runtime"
    """
    # Check environment variable first
    impl = os.getenv("COOK_ASSISTANT_IMPLEMENTATION", "").lower()
    
    if impl in ("mcp", "runtime"):
        logger.info(f"Using implementation from environment: {impl}")
        return impl
    
    # Fallback to SSM parameter
    try:
        impl = get_ssm_parameter("/app/cookassistant/implementation").lower()
        if impl in ("mcp", "runtime"):
            logger.info(f"Using implementation from SSM: {impl}")
            return impl
    except Exception as e:
        logger.debug(f"Could not read implementation from SSM: {e}")
    
    # Default to MCP
    logger.info(f"Using default implementation: {DEFAULT_IMPLEMENTATION}")
    return DEFAULT_IMPLEMENTATION


def create_agent_client(
    implementation: Optional[str] = None,
    agent_name: Optional[str] = None
) -> AgentClient:
    """
    Factory function to create the appropriate agent client.
    
    Args:
        implementation: "mcp" or "runtime". If None, reads from config/env/SSM.
        agent_name: Optional agent name for Runtime config file lookup.
    
    Returns:
        AgentClient instance (MCPAgentClient or RuntimeAgentClient)
    
    Raises:
        ValueError: If implementation is invalid
    """
    impl = implementation or get_implementation()
    
    if impl == "runtime":
        logger.info("Creating RuntimeAgentClient")
        return RuntimeAgentClient(agent_name=agent_name)
    elif impl == "mcp":
        logger.info("Creating MCPAgentClient")
        return MCPAgentClient()
    else:
        raise ValueError(
            f"Unknown implementation: {impl}. Must be 'mcp' or 'runtime'"
        )


async def invoke_cook_assistant(
    prompt: str,
    actor_id: str,
    session_id: str,
    context: Optional[dict] = None,
    implementation: Optional[str] = None,
    agent_name: Optional[str] = None
) -> str:
    """
    Unified invoke function that uses factory to select implementation.
    
    Args:
        prompt: The user's message/query
        actor_id: Unique identifier for the user (phone_number)
        session_id: Session identifier for conversation grouping
        context: Optional dictionary of context values for tool calls
        implementation: Optional override ("mcp" or "runtime")
        agent_name: Optional agent name for Runtime config file lookup
    
    Returns:
        Agent response as a string
    """
    client = create_agent_client(implementation=implementation, agent_name=agent_name)
    return await client.invoke(prompt, actor_id, session_id, context)
