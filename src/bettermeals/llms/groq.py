import os
from langchain_groq import ChatGroq

def supervisor_llm():
    # strong router for instruction-following
    return ChatGroq(model="openai/gpt-oss-120b", temperature=0, api_key=os.getenv("GROQ_API_KEY"))

def worker_llm_fast():
    # fast, capable worker for tool-calling
    return ChatGroq(model="openai/gpt-oss-20b", temperature=0, api_key=os.getenv("GROQ_API_KEY"))
