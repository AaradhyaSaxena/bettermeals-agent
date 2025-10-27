#!/usr/bin/env python
"""
CLI tool to interact with the Cook Assistant MCP Agent

Usage:
    python scripts/cook_assistant_cli.py --prompt "What meal can I make with chicken?"
"""

import asyncio
import click
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from bettermeals.graph.cook_assistant.bedrock_client import invoke_cook_assistant


@click.command()
@click.option("--prompt", "-p", required=True, help="Prompt to send to the Cook Assistant agent")
def main(prompt: str):
    """CLI tool to interact with the Cook Assistant MCP Agent using a prompt."""
    try:
        response = asyncio.run(invoke_cook_assistant(prompt))
        print(str(response))
    except Exception as e:
        print(f"❌ Error invoking Cook Assistant: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()

