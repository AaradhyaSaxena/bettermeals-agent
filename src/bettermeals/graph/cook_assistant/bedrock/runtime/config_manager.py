"""
Configuration Manager for Runtime Client

Manages agent ARN and runtime endpoint configuration.
Supports reading from config file or SSM parameters.
"""

import os
import urllib.parse
from pathlib import Path
from typing import Optional
import logging
from ...utils import get_ssm_parameter, get_aws_region, read_config

logger = logging.getLogger(__name__)


class RuntimeConfigManager:
    """Manages runtime configuration with lazy initialization and caching"""
    
    def __init__(self, agent_name: Optional[str] = None):
        """
        Initialize runtime config manager.
        
        Args:
            agent_name: Optional agent name to look up in config file.
                       If None, will use SSM parameter or default.
        """
        self._agent_arn: Optional[str] = None
        self._endpoint_name: Optional[str] = None
        self._region: Optional[str] = None
        self._agent_name = agent_name
    
    def get_agent_arn(self) -> str:
        """
        Get agent ARN from config file or SSM parameter.
        
        Returns:
            Agent ARN string
            
        Raises:
            ValueError: If agent ARN cannot be found
        """
        if self._agent_arn is None:
            # Try config file first (if agent_name is provided)
            if self._agent_name:
                try:
                    # Look for config file in project root
                    config_path = Path(__file__).parent.parent.parent.parent.parent.parent / ".bedrock_agentcore.yaml"
                    if config_path.exists():
                        runtime_config = read_config(str(config_path))
                        if self._agent_name in runtime_config.get("agents", {}):
                            agent_config = runtime_config["agents"][self._agent_name]
                            self._agent_arn = agent_config.get("bedrock_agentcore", {}).get("agent_arn")
                            logger.info(f"Found agent ARN from config file: {self._agent_arn[:50]}...")
                except Exception as e:
                    logger.warning(f"Could not read agent ARN from config file: {e}")
            
            # Fallback to SSM parameter
            if not self._agent_arn:
                try:
                    self._agent_arn = get_ssm_parameter("/app/cookassistant/runtime/agent_arn")
                    logger.info(f"Found agent ARN from SSM parameter")
                except Exception as e:
                    raise ValueError(
                        f"Could not find agent ARN. "
                        f"Either provide agent_name for config file lookup or set SSM parameter "
                        f"/app/cookassistant/runtime/agent_arn. Error: {e}"
                    )
        
        return self._agent_arn
    
    def get_runtime_endpoint(self) -> str:
        """
        Get Bedrock Runtime API endpoint URL.
        
        Returns:
            Runtime endpoint URL string with URL-encoded agent ARN
        """
        if self._region is None:
            self._region = get_aws_region()
        
        agent_arn = self.get_agent_arn()
        # URL encode agent ARN for use in URL path
        escaped_arn = urllib.parse.quote(agent_arn, safe="")
        
        # Build Bedrock Runtime endpoint URL
        return f"https://bedrock-agentcore.{self._region}.amazonaws.com/runtimes/{escaped_arn}/invocations"
    
    def get_endpoint_name(self) -> str:
        """
        Get endpoint qualifier name (default: "DEFAULT").
        
        Returns:
            Endpoint name string
        """
        if self._endpoint_name is None:
            try:
                self._endpoint_name = get_ssm_parameter("/app/cookassistant/runtime/endpoint_name")
            except Exception:
                self._endpoint_name = "DEFAULT"
        
        return self._endpoint_name
    
    def get_region(self) -> str:
        """Get AWS region"""
        if self._region is None:
            self._region = get_aws_region()
        return self._region

