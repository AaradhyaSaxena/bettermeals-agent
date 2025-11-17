"""
Agent Client Interface

This module defines the abstract interface for user agent agent clients.
All implementations (MCP, Runtime, etc.) must implement this protocol.
"""

from typing import Protocol, Optional, Dict, Any


class AgentClient(Protocol):
    """Protocol defining the interface for user agent agent clients"""
    
    async def invoke(
        self,
        prompt: str,
        actor_id: str,
        session_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Invoke the User Agent agent with AgentCore memory integration.
        
        Args:
            prompt: The user's message/query
            actor_id: Unique identifier for the user (phone_number)
            session_id: Session identifier for conversation grouping
            context: Optional dictionary of context values to make available for tool calls.
                     Keys should match tool parameter names (e.g., {"user_id": "123", "household_id": "456"}).
                     This makes the function extensible - add new keys as new tools/parameters are added.
            
        Returns:
            Agent response as a string
            
        Raises:
            Exception: If agent invocation fails
        """
        ...

