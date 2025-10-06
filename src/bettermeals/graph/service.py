"""Graph service for dependency injection."""
from typing import Optional
from .build import build_graph
from .persistence import make_checkpointer


class GraphService:
    """Service class to manage the LangGraph instance."""
    
    def __init__(self):
        self._graph: Optional[object] = None
    
    def get_graph(self):
        """Get the graph instance, building it if necessary."""
        if self._graph is None:
            self._graph = build_graph(checkpointer=make_checkpointer())
        return self._graph
    
    def build_graph(self):
        """Explicitly build the graph (useful for startup)."""
        self._graph = build_graph(checkpointer=make_checkpointer())
        return self._graph


# Global service instance
graph_service = GraphService()
