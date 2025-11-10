"""
Token Manager for Runtime Client

Handles M2M (Machine-to-Machine) access token lifecycle with thread-safe caching.
Uses Cognito client credentials flow for authentication.
"""

import asyncio
import base64
import time
from typing import Optional
import logging
import httpx
from ...utils import get_ssm_parameter

logger = logging.getLogger(__name__)


class RuntimeTokenManager:
    """Manages M2M access token with thread-safe caching and automatic refresh"""
    
    def __init__(self):
        """Initialize runtime token manager"""
        self._access_token: Optional[str] = None
        self._expires_at: float = 0
        self._token_lock = asyncio.Lock()
        self._ttl_seconds: int = 3600  # Default 1 hour, adjusted based on token expiry
    
    async def _get_m2m_token(self) -> str:
        """
        Get M2M access token using client credentials flow.
        
        Returns:
            Access token string
            
        Raises:
            Exception: If token request fails
        """
        client_id = get_ssm_parameter("/app/cookassistant/agentcore/machine_client_id")
        client_secret = get_ssm_parameter("/app/cookassistant/agentcore/cognito_secret")
        token_url = get_ssm_parameter("/app/cookassistant/agentcore/cognito_token_url")
        
        # Get scope (optional, but recommended)
        try:
            scope = get_ssm_parameter("/app/cookassistant/agentcore/cognito_auth_scope")
        except Exception:
            scope = ""  # Use default scope if not available
        
        # Base64 encode client_id:client_secret for Basic auth
        credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
        
        data = {
            "grant_type": "client_credentials",
        }
        
        if scope:
            data["scope"] = scope
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_url,
                data=data,
                headers={
                    "Authorization": f"Basic {credentials}",
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                timeout=30.0
            )
            
            if response.status_code != 200:
                error_text = response.text
                raise Exception(f"Failed to get M2M token: {response.status_code} - {error_text}")
            
            token_data = response.json()
            access_token = token_data["access_token"]
            
            # Adjust TTL based on token expiry if available
            if "expires_in" in token_data:
                # Refresh 1 minute before expiry
                self._ttl_seconds = max(60, token_data["expires_in"] - 60)
            
            return access_token
    
    async def get_access_token(self, force_refresh: bool = False) -> str:
        """
        Get M2M access token (thread-safe, cached).
        
        Args:
            force_refresh: If True, force refresh even if token is still valid
            
        Returns:
            Access token string
        """
        async with self._token_lock:
            current_time = time.time()
            
            if force_refresh or not self._access_token or current_time >= self._expires_at:
                logger.info("Fetching new M2M token..." if not self._access_token else "Refreshing M2M token...")
                self._access_token = await self._get_m2m_token()
                self._expires_at = current_time + self._ttl_seconds
                logger.info(f"Token acquired, expires in {self._ttl_seconds}s")
            else:
                logger.debug("Using cached M2M token")
            
            return self._access_token

