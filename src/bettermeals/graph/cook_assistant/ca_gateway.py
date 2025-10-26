#!/usr/bin/python

import asyncio
import click
from bedrock_agentcore.identity.auth import requires_access_token
from strands.tools.mcp import MCPClient
from mcp.client.streamable_http import streamablehttp_client
from strands import Agent
from strands.models import BedrockModel
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils import get_ssm_parameter

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


@click.command()
@click.option("--prompt", "-p", required=True, help="Prompt to send to the Cook Assistant agent (e.g., 'What meal can I make with chicken?')")
def main(prompt: str):
    """CLI tool to interact with the Cook Assistant MCP Agent using a prompt."""

    # Fetch access token
    asyncio.run(_get_access_token_manually(access_token=""))

    # Load gateway configuration from SSM parameters
    try:
        gateway_url = get_ssm_parameter("/app/cookassistant/agentcore/gateway_url")
    except Exception as e:
        print(f"❌ Error reading gateway URL from SSM: {str(e)}")
        sys.exit(1)

    print(f"Gateway Endpoint - MCP URL: {gateway_url}")

    # Set up MCP client
    client = MCPClient(
        lambda: streamablehttp_client(
            gateway_url,
            headers={"Authorization": f"Bearer {gateway_access_token}"},
        )
    )

    with client:
        # Create explicit model and system prompt for Cook Assistant
        model = BedrockModel(model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0")
        
        system_prompt = """
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
        
        agent = Agent(
            model=model,
            system_prompt=system_prompt,
            tools=client.list_tools_sync()
        )
        response = agent(prompt)
        print(str(response))


if __name__ == "__main__":
    main()
