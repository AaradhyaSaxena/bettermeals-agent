from langgraph.checkpoint.memory import InMemorySaver
# Swap to Redis/SQLite checkpointer later if desired

def make_checkpointer():
    """Return a checkpointer for durable execution (dev: in-memory)."""
    return InMemorySaver()
