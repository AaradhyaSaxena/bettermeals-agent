"""AWS Secrets Manager integration for secure configuration management."""
import json
import logging
from typing import Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

logger = logging.getLogger(__name__)


class SecretsManagerClient:
    """Client for retrieving secrets from AWS Secrets Manager."""
    
    def __init__(self, region_name: str = "ap-south-1"):
        """Initialize the Secrets Manager client."""
        try:
            self.client = boto3.client('secretsmanager', region_name=region_name)
            logger.info("AWS Secrets Manager client initialized successfully")
        except NoCredentialsError:
            logger.warning("AWS credentials not found. Secrets Manager will not be available.")
            self.client = None
    
    def get_secret(self, secret_name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a secret from AWS Secrets Manager.
        
        Args:
            secret_name: The name/ARN of the secret
            
        Returns:
            Dictionary containing the secret values, or None if not found
        """
        if not self.client:
            logger.warning("Secrets Manager client not available")
            return None
            
        try:
            response = self.client.get_secret_value(SecretId=secret_name)
            
            # Parse the secret string as JSON
            secret_data = json.loads(response['SecretString'])
            logger.info(f"Successfully retrieved secret: {secret_name}")
            return secret_data
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ResourceNotFoundException':
                logger.error(f"Secret {secret_name} not found")
            elif error_code == 'InvalidRequestException':
                logger.error(f"Invalid request for secret {secret_name}")
            elif error_code == 'InvalidParameterException':
                logger.error(f"Invalid parameter for secret {secret_name}")
            elif error_code == 'DecryptionFailureException':
                logger.error(f"Failed to decrypt secret {secret_name}")
            elif error_code == 'InternalServiceErrorException':
                logger.error(f"AWS internal service error for secret {secret_name}")
            else:
                logger.error(f"Unexpected error retrieving secret {secret_name}: {e}")
            return None
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse secret {secret_name} as JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error retrieving secret {secret_name}: {e}")
            return None
    
    def get_secret_value(self, secret_name: str, key: str = None) -> Optional[str]:
        """
        Get a specific value from a secret.
        
        Args:
            secret_name: The name/ARN of the secret
            key: The key within the secret (if None, returns the entire secret as string)
            
        Returns:
            The secret value as string, or None if not found
        """
        secret_data = self.get_secret(secret_name)
        if not secret_data:
            return None
            
        if key is None:
            # Return the entire secret as a string
            return json.dumps(secret_data)
        
        return secret_data.get(key)


# Global instance
secrets_client = SecretsManagerClient()
