"""
Runtime Agent Client

Main client implementation for invoking the Cook Assistant agent via Bedrock Runtime API.
Uses M2M authentication and direct API calls (no MCP protocol).
"""

from typing import Optional, Dict, Any
import logging
import httpx
from ..interface import AgentClient
from ..prompt_enhancer import enhance_prompt_with_context
from .token_manager import RuntimeTokenManager
from .config_manager import RuntimeConfigManager

logger = logging.getLogger(__name__)


class RuntimeAgentClient:
    """
    Runtime-based implementation of AgentClient.
    
    Handles M2M authentication and Bedrock Runtime API invocation with AgentCore memory integration.
    """
    
    def __init__(
        self,
        token_manager: Optional[RuntimeTokenManager] = None,
        config_manager: Optional[RuntimeConfigManager] = None,
        agent_name: Optional[str] = None
    ):
        """
        Initialize Runtime agent client with dependencies.
        
        Args:
            token_manager: RuntimeTokenManager instance (created if None)
            config_manager: RuntimeConfigManager instance (created if None)
            agent_name: Optional agent name for config file lookup
        """
        self.token_manager = token_manager or RuntimeTokenManager()
        self.config_manager = config_manager or RuntimeConfigManager(agent_name=agent_name)
    
    async def invoke(
        self,
        prompt: str,
        actor_id: str,
        session_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Invoke the Cook Assistant agent with AgentCore memory integration.
        
        Args:
            prompt: The user's message/query
            actor_id: Unique identifier for the user (phone_number)
            session_id: Session identifier for conversation grouping
            context: Optional dictionary of context values to make available for tool calls.
                     Keys should match tool parameter names (e.g., {"cook_id": "123", "household_id": "456"}).
                     This makes the function extensible - add new keys as new tools/parameters are added.
            
        Returns:
            Agent response as a string
            
        Raises:
            Exception: If agent invocation fails
        """
        try:
            # Get M2M access token (cached, thread-safe)
            access_token = await self.token_manager.get_access_token()
            
            # Enhance prompt with available context for tool calls
            enhanced_prompt = enhance_prompt_with_context(prompt, context or {})
            
            # Build payload
            payload = {
                "prompt": enhanced_prompt,
                "actor_id": actor_id
            }
            
            # Get runtime endpoint and configuration
            endpoint_url = self.config_manager.get_runtime_endpoint()
            endpoint_name = self.config_manager.get_endpoint_name()
            
            # Prepare headers
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "X-Amzn-Bedrock-AgentCore-Runtime-Session-Id": session_id,
            }
            
            logger.info(f"Invoking Bedrock Runtime agent at {endpoint_url}")
            
            # Invoke agent endpoint with streaming
            async with httpx.AsyncClient(timeout=100.0) as client:
                response = await client.post(
                    endpoint_url,
                    params={"qualifier": endpoint_name},
                    headers=headers,
                    json=payload,
                    timeout=100.0
                )
                
                # Check response status
                if response.status_code != 200:
                    error_text = response.text
                    logger.error(f"Bedrock Runtime API error: {response.status_code} - {error_text}")
                    response.raise_for_status()
                
                # Handle streaming response
                # The response is Server-Sent Events (SSE) format with "data: " prefix
                response_text = ""
                async for line in response.aiter_lines():
                    if line:
                        decoded_line = line.decode("utf-8") if isinstance(line, bytes) else line
                        if decoded_line.startswith("data: "):
                            # Extract content after "data: " prefix
                            content = decoded_line[6:].strip()
                            # Remove quotes if present
                            content = content.strip('"')
                            response_text += content
                        elif decoded_line.strip():
                            # Handle any other non-empty lines
                            response_text += decoded_line.strip()
                
                logger.info(f"Received response from Bedrock Runtime (length: {len(response_text)})")
                return response_text
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error invoking Bedrock Runtime: {e.response.status_code} - {e.response.text}", exc_info=True)
            raise Exception(f"Bedrock Runtime API error: {e.response.status_code}") from e
        except httpx.RequestError as e:
            logger.error(f"Request error invoking Bedrock Runtime: {str(e)}", exc_info=True)
            raise Exception(f"Failed to invoke Bedrock Runtime: {str(e)}") from e
        except Exception as e:
            # Log and re-raise for caller to handle
            logger.error(f"Error invoking cook assistant via Runtime: {str(e)}", exc_info=True)
            raise

