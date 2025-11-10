"""
Prompt Enhancement Utilities

Functions for enhancing user prompts with context information for tool calls.
"""

from typing import Dict, Any


def enhance_prompt_with_context(prompt: str, context: Dict[str, Any]) -> str:
    """
    Enhance user prompt with available context values for tool calls.
    
    This is a generic function that works with any context dictionary,
    making it easily extensible when new tools or parameters are added.
    
    Args:
        prompt: Original user prompt
        context: Dictionary of context key-value pairs available for tool calls
        
    Returns:
        Enhanced prompt with context information, or original prompt if context is empty
    """
    if not context:
        return prompt
    
    # Filter out None values
    available_context = {k: v for k, v in context.items() if v is not None}
    
    if not available_context:
        return prompt
    
    # Build context section dynamically
    context_lines = [f"- {key}: {value}" for key, value in sorted(available_context.items())]
    context_section = "\n".join(context_lines)
    
    enhanced = f"""{prompt}

<available_context>
The following context values are available for use with tools:
{context_section}

When calling tools, use these values when the tool parameters match the context keys.
</available_context>"""
    
    return enhanced

