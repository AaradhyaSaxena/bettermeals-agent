from langgraph.prebuilt import create_react_agent
from ..llms.groq import supervisor_llm
from .workers import recommender, scorer, order_agent, onboarding, cook_update

supervisor = create_react_agent(
    model=supervisor_llm(),
    # tools=[onboarding, recommender, scorer, order_agent, cook_update],
    name="supervisor",
    prompt=open(__file__.replace("supervisor.py","prompts/supervisor_prompt.txt")).read()
)
