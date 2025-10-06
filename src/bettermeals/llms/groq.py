from langchain_groq import ChatGroq
from ..config.settings import settings

def supervisor_llm():
    # strong router for instruction-following
    return ChatGroq(model="openai/gpt-oss-20b", temperature=0, api_key=settings.groq_api_key)

def worker_llm_fast():
    # fast, capable worker for tool-calling
    return ChatGroq(model="openai/gpt-oss-20b", temperature=0, api_key=settings.groq_api_key)
