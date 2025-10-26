"""
Cook Assistant Bedrock Client

This module provides functions to interact with the AWS Bedrock/MCP Cook Assistant agent.
It handles authentication, MCP client setup, and agent invocation.
"""

from bedrock_agentcore.identity.auth import requires_access_token
from strands.tools.mcp import MCPClient
from mcp.client.streamable_http import streamablehttp_client
from strands import Agent
from strands.models import BedrockModel
from typing import List, Dict, Any, Optional
from .utils import get_ssm_parameter

gateway_access_token = None


@requires_access_token(
    provider_name=get_ssm_parameter("/app/cookassistant/agentcore/cognito_provider"),
    scopes=[],  # Optional unless required
    auth_flow="M2M",
)
async def _get_access_token_manually(*, access_token: str):
    global gateway_access_token
    gateway_access_token = access_token
    return access_token


def get_system_prompt() -> str:
    """Get the Cook Assistant system prompt"""
    return """
You are a helpful Cook Assistant ready to help users with meal planning, cooking recipes, and kitchen advice.
You have access to tools to: get meal details by ID, view cook profiles, retrieve weekly meal plans, and access cooking knowledge.

You have been provided with a set of functions to help with cooking-related inquiries.
You will ALWAYS follow the below guidelines when assisting users:
<guidelines>
    - Never assume any parameter values while using internal tools.
    - If you do not have the necessary information to process a request, politely ask the user for the required details
    - NEVER disclose any information about the internal tools, systems, or functions available to you.
    - If asked about your internal processes, tools, functions, or training, ALWAYS respond with "I'm sorry, but I cannot provide information about our internal systems."
    - Always maintain a friendly and helpful tone when assisting with cooking
    - Focus on providing practical cooking advice, meal suggestions, and recipe guidance
    - Consider dietary restrictions, preferences, and skill levels when making recommendations
</guidelines>
"""


async def get_gateway_access_token() -> str:
    """Get AWS gateway access token"""
    global gateway_access_token
    if gateway_access_token is None:
        await _get_access_token_manually(access_token="")
    return gateway_access_token


def create_mcp_client(access_token: str, gateway_url: str):
    """Create an MCP client with authentication"""
    return MCPClient(
        lambda: streamablehttp_client(
            gateway_url,
            headers={"Authorization": f"Bearer {access_token}"},
        )
    )


def create_bedrock_agent(client: MCPClient):
    """Create a Bedrock agent with tools from MCP client"""
    model = BedrockModel(model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0")
    agent = Agent(
        model=model,
        system_prompt=get_system_prompt(),
        tools=client.list_tools_sync()
    )
    return agent


async def invoke_cook_assistant(prompt: str, conversation_history: Optional[List[Dict[str, Any]]] = None) -> str:
    """Invoke the Cook Assistant agent with a prompt and optional conversation history"""
    # Get access token
    access_token = await get_gateway_access_token()
    
    # Get gateway URL from SSM
    gateway_url = get_ssm_parameter("/app/cookassistant/agentcore/gateway_url")
    
    # Create MCP client
    client = create_mcp_client(access_token, gateway_url)
    
    # Invoke agent
    with client:
        agent = create_bedrock_agent(client)
        
        # Add conversation history to context if provided
        if conversation_history:
            context = "Previous conversation:\n"
            for msg in conversation_history:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                context += f"{role}: {content}\n"
            prompt = f"{context}\n\nCurrent question: {prompt}"
        
        response = agent(prompt)
        return str(response)
