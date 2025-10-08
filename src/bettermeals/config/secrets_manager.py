import boto3
import json
import os
from botocore.exceptions import ClientError
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class SecretsManager:
    """
    Centralized secrets management for SuperMeals backend.
    Uses AWS Secrets Manager in production and environment variables for local development.
    """
    
    def __init__(self):
        self.secret_name = "prod/bettermeals-backend/env"
        self.region_name = "ap-south-1"
        self.secrets_cache: Optional[Dict[str, Any]] = None
        
    def _get_secrets_from_aws(self) -> Dict[str, Any]:
        """Get secrets from AWS Secrets Manager"""
        logger.info(f"Starting AWS Secrets Manager connection...")
        
        try:
            logger.info("Creating AWS session...")
            session = boto3.Session()
            client = session.client(
                service_name='secretsmanager',
                region_name=self.region_name
            )
            
            get_secret_value_response = client.get_secret_value(
                SecretId=self.secret_name
            )
            
            secret_string = get_secret_value_response['SecretString']
            secrets = json.loads(secret_string)
            logger.info(f"Successfully loaded secrets from AWS Secrets Manager")
            
            return secrets
            
        except ClientError as e:
            logger.error(f"Error getting secrets from AWS Secrets Manager: {e}")
            raise e
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing secrets JSON: {e}")
            raise e
    
    def _load_secrets(self) -> Dict[str, Any]:
        """Load secrets with caching"""
        if self.secrets_cache is None:
            try:
                # Try AWS Secrets Manager first (for production)
                self.secrets_cache = self._get_secrets_from_aws()
            except Exception as e:
                logger.warning(f"Failed to load from AWS Secrets Manager: {e}")
                logger.info("Falling back to environment variables for local development")
                # Fallback to environment variables (for local development)
                self.secrets_cache = {}
        else:
            logger.info("Using cached secrets")
        
        return self.secrets_cache
    
    def get_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get a secret value by key.
        
        Args:
            key: The secret key name
            default: Default value if key is not found
            
        Returns:
            The secret value or default
        """
        secrets = self._load_secrets()
        
        # First try from AWS Secrets Manager
        if key in secrets:
            return secrets[key]
        
        # Fallback to environment variables
        env_value = os.getenv(key, default)
        if env_value:
            logger.info(f"Using environment variable for {key}")
            return env_value
        
        logger.warning(f"Secret '{key}' not found in AWS Secrets Manager or environment variables")
        return default
    
    def get_required_secret(self, key: str) -> str:
        """
        Get a required secret value. Raises an exception if not found.
        
        Args:
            key: The secret key name
            
        Returns:
            The secret value
            
        Raises:
            ValueError: If the secret is not found
        """
        value = self.get_secret(key)
        if value is None:
            raise ValueError(f"Required secret '{key}' not found in AWS Secrets Manager or environment variables")
        return value
    
    def get_firebase_credentials(self) -> Dict[str, Any]:
        """
        Get Firebase service account credentials.
        
        Returns:
            Firebase service account credentials as a dictionary
        """
        # TODO: Add key name for Firebase service account JSON
        firebase_json = self.get_required_secret("FIREBASE_SERVICE_ACCOUNT_KEY")
        
        try:
            # If it's base64 encoded, decode it
            import base64
            if firebase_json.startswith('{'):
                # Already JSON
                return json.loads(firebase_json)
            else:
                # Base64 encoded
                decoded = base64.b64decode(firebase_json).decode('utf-8')
                return json.loads(decoded)
        except Exception as e:
            logger.error(f"Error parsing Firebase credentials: {e}")
            raise ValueError("Invalid Firebase credentials format")


    def get_google_service_account_key(self) -> Dict[str, Any]:
        """
        Get Google service account key.
        
        Returns:
            Google service account key as a dictionary
        """
        google_service_account_key = self.get_required_secret("GOOGLE_SERVICE_ACCOUNT_KEY")
        try:
            # If it's base64 encoded, decode it
            import base64
            if google_service_account_key.startswith('{'):
                # Already JSON
                return json.loads(google_service_account_key)
            else:
                # Base64 encoded
                decoded = base64.b64decode(google_service_account_key).decode('utf-8')
                return json.loads(decoded)
        except Exception as e:
            logger.error(f"Error parsing Google service account key: {e}")
            raise ValueError("Invalid Google service account key format")

    def get_sarvam_api_key(self) -> str:
        """
        Get Sarvam API key.
        
        Returns:
            Sarvam API key as a string
        """
        return self.get_required_secret("SARVAM_API_KEY")

    def get_google_api_key(self) -> str:
        """
        Get Google API key.
        
        Returns:
            Google API key as a string
        """ 
        return self.get_required_secret("GOOGLE_API_KEY")

# Global instance
secrets_manager = SecretsManager()
