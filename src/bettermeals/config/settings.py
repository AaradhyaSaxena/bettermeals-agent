from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings
from typing import Optional
import os
import logging
from .secrets_manager import secrets_client

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    groq_api_key: Optional[str] = None
    claude_api_key: Optional[str] = None
    tavily_api_key: Optional[str] = None
    bm_api_base: AnyHttpUrl = "http://staging-bm.eba-n3mspgd3.ap-south-1.elasticbeanstalk.com"
    
    # AWS Secrets Manager configuration
    secrets_manager_secret_name: Optional[str] = "prod/bettermeals-backend/env"
    aws_region: str = "ap-south-1"

    class Config:
        env_file = ".env"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._load_secrets_from_aws()

    def _load_secrets_from_aws(self):
        """Load secrets from AWS Secrets Manager if configured."""
        if not self.secrets_manager_secret_name:
            logger.info("No AWS Secrets Manager secret name configured, using environment variables")
            return
            
        logger.info(f"Loading secrets from AWS Secrets Manager: {self.secrets_manager_secret_name}")
        secrets = secrets_client.get_secret(self.secrets_manager_secret_name)
        
        if secrets:
            # Override settings with values from Secrets Manager
            self.groq_api_key = secrets.get('GROQ_API_KEY', self.groq_api_key)
            self.claude_api_key = secrets.get('CLAUDE_API_KEY', self.claude_api_key)
            self.tavily_api_key = secrets.get('TAVILY_API_KEY', self.tavily_api_key)
            
            # Update BM_API_BASE if provided
            if 'BM_API_BASE' in secrets:
                self.bm_api_base = secrets['BM_API_BASE']
                
            logger.info("Successfully loaded secrets from AWS Secrets Manager")
        else:
            logger.warning("Failed to load secrets from AWS Secrets Manager, falling back to environment variables")

settings = Settings()
