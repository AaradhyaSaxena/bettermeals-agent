#!/usr/bin/env python
"""
CLI tool to interact with the User Agent MCP Agent

Usage:
    python tests/user_agent_cli.py --prompt "Show my profile"
    python tests/user_agent_cli.py --prompt "What meals do I have?" --context '{"user_id": "123", "household_id": "456"}'
"""

import asyncio
import click
import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from bettermeals.graph.user_agent.bedrock import invoke_user_agent


def ensure_session_id_length(session_id: str, actor_id: str) -> str:
    """
    Ensure session ID is at least 33 characters (Bedrock Runtime requirement).
    If too short, pad with deterministic hash suffix.
    """
    if len(session_id) >= 33:
        return session_id
    
    # Generate deterministic suffix based on session_id + actor_id
    base = f"{session_id}_{actor_id}"
    hash_digest = hashlib.sha256(base.encode()).hexdigest()
    padding_needed = 33 - len(session_id) - 1  # -1 for underscore
    hash_suffix = hash_digest[:max(16, padding_needed)]
    
    return f"{session_id}_{hash_suffix}"


@click.command()
@click.option("--prompt", "-p", required=True, help="Prompt to send to the User Agent agent")
@click.option("--actor-id", "-a", default="test_actor", help="Actor ID (phone number) for the agent")
@click.option("--session-id", "-s", default=None, help="Session ID for the agent (defaults to test_session_YYYYMMDD)")
@click.option("--context", "-c", default=None, help="JSON string of context values (e.g., '{\"user_id\": \"123\", \"household_id\": \"456\"}')")
@click.option("--implementation", "-i", default=None, help="Implementation: 'mcp' or 'runtime' (defaults to env/SSM config)")
@click.option("--agent-name", "-n", default=None, help="Agent name for Runtime config file lookup")
def main(prompt: str, actor_id: str, session_id: str, context: str, implementation: str, agent_name: str):
    """CLI tool to interact with the User Agent Agent using a prompt."""
    try:
        # Parse context if provided
        context_dict = None
        if context:
            try:
                context_dict = json.loads(context)
            except json.JSONDecodeError as e:
                print(f"Error parsing context JSON: {e}")
                sys.exit(1)
        
        # Generate default session_id if not provided (with date for uniqueness)
        if session_id is None:
            date_str = datetime.now().strftime("%Y%m%d")
            session_id = f"test_session_{date_str}"
        
        # Ensure session_id meets Bedrock Runtime minimum length (33 chars)
        session_id = ensure_session_id_length(session_id, actor_id)
        
        response = asyncio.run(invoke_user_agent(
            prompt, 
            actor_id, 
            session_id, 
            context_dict, 
            implementation=implementation,
            agent_name=agent_name
        ))
        print(str(response))
    except Exception as e:
        print(f"❌ Error invoking User Agent: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()


# python3 tests/user_agent_cli.py \
#   --implementation runtime \
#   --agent-name cookassistant_v1 \
#   --prompt "What are the ingredients for meal yt_F_S9g8V3h_8#dinner?"