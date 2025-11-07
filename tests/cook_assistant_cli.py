#!/usr/bin/env python
"""
CLI tool to interact with the Cook Assistant MCP Agent

Usage:
    python tests/cook_assistant_cli.py --prompt "What meal can I make with chicken?"
    python tests/cook_assistant_cli.py --prompt "Show my profile" --context '{"cook_id": "123"}'
"""

import asyncio
import click
import sys
import json
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from bettermeals.graph.cook_assistant.bedrock_client import invoke_cook_assistant


@click.command()
@click.option("--prompt", "-p", required=True, help="Prompt to send to the Cook Assistant agent")
@click.option("--actor-id", "-a", default="test_actor", help="Actor ID (phone number) for the agent")
@click.option("--session-id", "-s", default="test_session", help="Session ID for the agent")
@click.option("--context", "-c", default=None, help="JSON string of context values (e.g., '{\"cook_id\": \"123\", \"household_id\": \"456\"}')")
def main(prompt: str, actor_id: str, session_id: str, context: str):
    """CLI tool to interact with the Cook Assistant MCP Agent using a prompt."""
    try:
        # Parse context if provided
        context_dict = None
        if context:
            try:
                context_dict = json.loads(context)
            except json.JSONDecodeError as e:
                print(f"Error parsing context JSON: {e}")
                sys.exit(1)
        
        response = asyncio.run(invoke_cook_assistant(prompt, actor_id, session_id, context_dict))
        print(str(response))
    except Exception as e:
        print(f"❌ Error invoking Cook Assistant: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()

