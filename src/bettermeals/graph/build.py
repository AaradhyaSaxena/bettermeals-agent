from langgraph.graph import StateGraph, START, END
from .state import State
from .supervisor import supervisor
from .workers import recommender, scorer, order_agent, onboarding, cook_update

def build_graph(checkpointer=None, store=None):
    g = StateGraph(State)
    g.add_node("supervisor", supervisor)
    g.add_node("meal_recommender", recommender)
    g.add_node("meal_scorer", scorer)
    g.add_node("order", order_agent)
    g.add_node("onboarding", onboarding)
    g.add_node("cook_update", cook_update)

    g.add_edge(START, "supervisor")
    for w in ["meal_recommender","meal_scorer","order","onboarding","cook_update"]:
        g.add_edge(w, "supervisor")
    g.add_edge("supervisor", END)

    return g.compile(checkpointer=checkpointer, store=store)
