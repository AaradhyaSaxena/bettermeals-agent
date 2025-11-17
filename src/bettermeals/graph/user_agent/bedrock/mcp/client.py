"""
MCP Agent Client

Main client implementation for invoking the User Agent agent via MCP.
Composes TokenManager, ConfigManager, MCPClientFactory, and AgentFactory.
"""

from typing import Optional, Dict, Any
import logging
from ..interface import AgentClient
from .token_manager import TokenManager
from .config_manager import ConfigManager
from .mcp_client_factory import MCPClientFactory
from .agent_factory import AgentFactory
from ..prompt_enhancer import enhance_prompt_with_context

logger = logging.getLogger(__name__)


class MCPAgentClient:
    """
    MCP-based implementation of AgentClient.
    
    Handles authentication, MCP client setup, and agent invocation with AgentCore memory integration.
    """
    
    def __init__(
        self,
        token_manager: Optional[TokenManager] = None,
        config_manager: Optional[ConfigManager] = None,
        mcp_client_factory: Optional[MCPClientFactory] = None,
        agent_factory: Optional[AgentFactory] = None
    ):
        """
        Initialize MCP agent client with dependencies.
        
        Args:
            token_manager: TokenManager instance (created if None)
            config_manager: ConfigManager instance (created if None)
            mcp_client_factory: MCPClientFactory instance (created if None)
            agent_factory: AgentFactory instance (created if None)
        """
        self.token_manager = token_manager or TokenManager()
        self.config_manager = config_manager or ConfigManager()
        self.mcp_client_factory = mcp_client_factory or MCPClientFactory()
        self.agent_factory = agent_factory or AgentFactory(self.config_manager)
    
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
        try:
            # Get access token (cached, thread-safe)
            access_token = await self.token_manager.get_access_token()
            
            # Get gateway URL (cached)
            gateway_url = self.config_manager.get_gateway_url()
            
            # Create MCP client
            client = self.mcp_client_factory.create_client(access_token, gateway_url)
            
            # Enhance prompt with available context for tool calls
            enhanced_prompt = enhance_prompt_with_context(prompt, context or {})
            
            # Invoke agent with memory
            # The MCP client context manager must stay open for the entire agent execution
            # including async tool calls. The agent() call should block until all operations complete.
            with client:
                agent = self.agent_factory.create_agent(client, actor_id, session_id)
                
                # AgentCore handles conversation context automatically through session_manager
                # Call agent synchronously - it should handle async operations internally
                # and block until completion before returning
                response = agent(enhanced_prompt)
                
                # Convert response to string
                return str(response)
                
        except Exception as e:
            # Log and re-raise for caller to handle
            logger.error(f"Error invoking user agent: {str(e)}", exc_info=True)
            raise


# Create a singleton instance for backward compatibility
_default_client: Optional[MCPAgentClient] = None


async def invoke_user_agent(
    prompt: str,
    actor_id: str,
    session_id: str,
    context: Optional[Dict[str, Any]] = None
) -> str:
    """
    Invoke the User Agent agent (backward compatibility function).
    
    This function maintains the original API while delegating to MCPAgentClient.
    Consider using MCPAgentClient directly for better testability.
    """
    global _default_client
    if _default_client is None:
        _default_client = MCPAgentClient()
    
    return await _default_client.invoke(prompt, actor_id, session_id, context)

