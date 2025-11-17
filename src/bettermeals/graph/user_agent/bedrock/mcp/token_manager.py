"""
Token Manager for MCP Client

Handles AWS gateway access token lifecycle with thread-safe caching.
"""

import os
import asyncio
from pathlib import Path
from typing import Optional
import logging
from bedrock_agentcore.identity.auth import requires_access_token
from ...utils import get_ssm_parameter

logger = logging.getLogger(__name__)

# Get provider name at module load time (matching original behavior)
# This matches the original bedrock_client.py where get_ssm_parameter was called at decoration time
_COGNITO_PROVIDER = get_ssm_parameter("/app/useragent/agentcore/cognito_provider")


class TokenManager:
    """Manages AWS gateway access token with thread-safe caching"""
    
    def __init__(self):
        """Initialize token manager and set up AGENTCORE_CONFIG_PATH"""
        self._access_token: Optional[str] = None
        self._token_lock = asyncio.Lock()
        
        # Set the path to .agentcore.json in user_agent directory
        # Path from bedrock/mcp/ -> bedrock/ -> user_agent/
        config_dir = Path(__file__).parent.parent.parent
        config_file = config_dir / ".agentcore.json"
        
        # Set AGENTCORE_CONFIG_PATH environment variable if not already set
        if "AGENTCORE_CONFIG_PATH" not in os.environ and config_file.exists():
            os.environ["AGENTCORE_CONFIG_PATH"] = str(config_file)
    
    @requires_access_token(
        provider_name=_COGNITO_PROVIDER,
        scopes=[],
        auth_flow="M2M",
    )
    async def _get_access_token_manually(self, *, access_token: str):
        """Get access token - called by decorator"""
        logger.info(f"Received access token, length: {len(access_token) if access_token else 0}")
        self._access_token = access_token
        return access_token
    
    async def get_access_token(self) -> str:
        """Get AWS gateway access token (thread-safe)"""
        async with self._token_lock:
            if self._access_token is None:
                logger.info("Token is None, fetching new token...")
                await self._get_access_token_manually(access_token="")
                logger.info(f"Token fetched, length: {len(self._access_token) if self._access_token else 0}")
            else:
                logger.debug("Using cached token")
            return self._access_token

