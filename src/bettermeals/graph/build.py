from pathlib import Path
from langgraph_supervisor import create_supervisor
from ..llms.groq import supervisor_llm
from .workers import recommender, scorer, order_agent, onboarding, cook_update

PROMPT = (Path(__file__).parent / "prompts" / "supervisor_prompt.txt").read_text()

def build_graph(checkpointer=None, store=None):
    workflow = create_supervisor(
        [onboarding, recommender, scorer, order_agent, cook_update],
        model=supervisor_llm(),
        prompt=PROMPT,
        # optional knobs:
        # output_mode="last_message",
        # handoff_tool_prefix="delegate_to",
    )
    return workflow.compile(checkpointer=checkpointer, store=store)
