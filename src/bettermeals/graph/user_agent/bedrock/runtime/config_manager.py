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
from ...utils import get_ssm_parameter, put_ssm_parameter, get_aws_region, read_config

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
        Get agent ARN from config file, SSM parameter, or .env file.
        
        Tries in order:
        1. Config file (if agent_name provided)
        2. SSM parameter
        3. .env file (automatically syncs to SSM if found)
        
        Returns:
            Agent ARN string
            
        Raises:
            ValueError: If agent ARN cannot be found from any source
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
                    self._agent_arn = get_ssm_parameter("/app/useragent/runtime/agent_arn")
                    logger.info(f"Found agent ARN from SSM parameter")
                except Exception as e:
                    # Try to sync from .env as last resort
                    try:
                        logger.info("SSM parameter not found, attempting to sync from .env...")
                        self._agent_arn = RuntimeConfigManager.sync_agent_arn_from_env()
                        logger.info("Successfully synced agent_arn from .env to SSM")
                    except Exception as sync_error:
                        raise ValueError(
                            f"Could not find agent ARN. "
                            f"Either provide agent_name for config file lookup, set SSM parameter "
                            f"/app/useragent/runtime/agent_arn, or ensure .env contains agent_arn. "
                            f"SSM error: {e}, Sync error: {sync_error}"
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
                self._endpoint_name = get_ssm_parameter("/app/useragent/runtime/endpoint_name")
            except Exception:
                self._endpoint_name = "DEFAULT"
        
        return self._endpoint_name
    
    def get_region(self) -> str:
        """Get AWS region"""
        if self._region is None:
            self._region = get_aws_region()
        return self._region
    
    @classmethod
    def sync_agent_arn_from_env(cls, env_file_path: Optional[str] = None) -> str:
        """
        Sync agent ARN from .env file to SSM Parameter Store.
        
        Args:
            env_file_path: Path to .env file. If None, looks for .env in project root.
        
        Returns:
            Agent ARN string that was stored in SSM
        
        Raises:
            FileNotFoundError: If .env file not found
            ValueError: If agent_arn not found in .env file
        """
        if env_file_path is None:
            # Look for .env in user_agent directory (3 levels up from this file)
            # From bedrock/runtime/config_manager.py -> bedrock -> user_agent
            useragent_root = Path(__file__).parent.parent.parent
            env_file_path = useragent_root / ".env"
        
        if not os.path.exists(env_file_path):
            raise FileNotFoundError(f".env file not found at {env_file_path}")
        
        # Read .env file
        env_vars = {}
        with open(env_file_path, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                # Parse KEY=VALUE format
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")  # Remove quotes if present
                    env_vars[key] = value
        
        # Look for agent_arn (case-insensitive, check common variations)
        agent_arn = None
        for key, value in env_vars.items():
            key_upper = key.upper()
            if key_upper in ['AGENT_ARN', 'USER_AGENT_AGENT_ARN', 'BEDROCK_AGENT_ARN', 'RUNTIME_AGENT_ARN']:
                agent_arn = value
                logger.info(f"Found agent_arn in .env as {key}")
                break
        
        if not agent_arn:
            raise ValueError(
                f"agent_arn not found in .env file. "
                f"Expected one of: AGENT_ARN, USER_AGENT_AGENT_ARN, BEDROCK_AGENT_ARN, RUNTIME_AGENT_ARN. "
                f"Available keys: {list(env_vars.keys())}"
            )
        
        # Store in SSM
        ssm_param_name = "/app/useragent/runtime/agent_arn"
        put_ssm_parameter(ssm_param_name, agent_arn)
        logger.info(f"Synced agent_arn from .env to SSM: {ssm_param_name}")
        
        return agent_arn

