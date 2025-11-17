"""
MCP Client Factory

Creates authenticated MCP clients and manages tool retrieval.
"""

import logging
from strands.tools.mcp import MCPClient
from mcp.client.streamable_http import streamablehttp_client

logger = logging.getLogger(__name__)


class MCPClientFactory:
    """Factory for creating MCP clients with authentication"""
    
    @staticmethod
    def create_client(access_token: str, gateway_url: str) -> MCPClient:
        """Create an MCP client with authentication"""
        return MCPClient(
            lambda: streamablehttp_client(
                gateway_url,
                headers={"Authorization": f"Bearer {access_token}"},
            )
        )
    
    @staticmethod
    def get_tools(client: MCPClient) -> list:
        """
        Get tools from MCP client.
        
        Note: Always fetches fresh tools to ensure they're bound to the active client session.
        Tools need the client session to be active when making async calls.
        """
        logger.info("Fetching tools from MCP client...")
        tools = client.list_tools_sync()
        logger.info(f"Fetched {len(tools)} tools")
        return tools

