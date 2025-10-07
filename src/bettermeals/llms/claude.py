from langchain_anthropic import ChatAnthropic
from ..config.settings import settings

def supervisor_llm():
    # strong router for instruction-following
    return ChatAnthropic(
        model="claude-3-5-sonnet-20241022", 
        temperature=0, 
        api_key=settings.claude_api_key
    )

def worker_llm_fast():
    # fast, capable worker for tool-calling
    return ChatAnthropic(
        model="claude-3-5-sonnet-20241022", 
        temperature=0, 
        api_key=settings.claude_api_key
    )
