"""
Configuration Manager for MCP Client

Handles SSM parameter retrieval and caching for gateway URL, memory ID, and region.
"""

from typing import Optional
import logging
from ...utils import get_ssm_parameter, get_aws_region
from ...memory_config import get_memory_resource_id

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages configuration values with lazy initialization and caching"""
    
    def __init__(self):
        """Initialize config manager with None values (lazy loading)"""
        self._gateway_url: Optional[str] = None
        self._memory_id: Optional[str] = None
        self._region: Optional[str] = None
    
    def get_gateway_url(self) -> str:
        """Get gateway URL from SSM (cached)"""
        if self._gateway_url is None:
            self._gateway_url = get_ssm_parameter("/app/useragent/agentcore/gateway_url")
        return self._gateway_url
    
    def get_memory_id(self) -> str:
        """Get memory resource ID (cached)"""
        if self._memory_id is None:
            self._memory_id = get_memory_resource_id()
        return self._memory_id
    
    def get_region(self) -> str:
        """Get AWS region (cached)"""
        if self._region is None:
            self._region = get_aws_region()
        return self._region

