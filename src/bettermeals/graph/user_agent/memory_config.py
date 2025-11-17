"""
Memory configuration for User Agent AgentCore integration.

This module handles memory resource initialization and SSM parameter management
for the user agent's semantic memory strategy.
"""

import logging
from typing import Optional
from bedrock_agentcore.memory import MemoryClient
from .utils import get_ssm_parameter, put_ssm_parameter, get_aws_region

logger = logging.getLogger(__name__)

MEMORY_ID_SSM_PARAM = "/app/useragent/agentcore/memory_id"
MEMORY_NAME = "UserAgentMemory"
MEMORY_DESCRIPTION = "Memory resource for user agent with semantic memory strategy"


def create_memory_client() -> MemoryClient:
    """Create and return a MemoryClient instance"""
    region = get_aws_region()
    return MemoryClient(region_name=region)


def get_or_create_memory_resource() -> str:
    """
    Get existing memory resource ID from SSM or create a new one.
    Returns the memory resource ID.
    """
    try:
        # Try to get existing memory ID from SSM
        memory_id = get_ssm_parameter(MEMORY_ID_SSM_PARAM)
        if memory_id:
            logger.info(f"Using existing memory resource: {memory_id}")
            return memory_id
    except Exception as e:
        logger.info(f"No existing memory ID found in SSM: {e}")
    
    # Create new memory resource
    logger.info("Creating new memory resource")
    client = create_memory_client()
    
    memory_config = {
        "name": MEMORY_NAME,
        "description": MEMORY_DESCRIPTION,
        "strategies": [
            {
                "semanticMemoryStrategy": {
                    "name": "UserAgentSemanticMemory",
                    "namespaces": ["/facts/{actorId}"]
                }
            }
        ],
        "eventExpiryDuration": 30  # 30 days retention for compliance
    }
    
    try:
        memory = client.create_memory(**memory_config)
        memory_id = memory.get('id')
        
        if memory_id:
            # Store memory ID in SSM for future use
            put_ssm_parameter(
                name=MEMORY_ID_SSM_PARAM,
                value=memory_id,
                parameter_type="String"
            )
            logger.info(f"Created and stored memory resource: {memory_id}")
            return memory_id
        else:
            raise ValueError("Failed to create memory resource: no ID returned")
            
    except Exception as e:
        logger.error(f"Error creating memory resource: {str(e)}")
        raise


def get_memory_resource_id() -> str:
    """Get the memory resource ID from SSM or create a new one"""
    return get_or_create_memory_resource()
