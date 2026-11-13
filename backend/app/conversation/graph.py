"""Graphe borné à deux nœuds, sans boucle d'agent ni exécution arbitraire."""
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph


class Turn(TypedDict, total=False):
    message: str
    context: dict
    access: Any
    language: str
    intent: Any
    response: dict


def build_graph(interpret, execute):
    graph = StateGraph(Turn)
    graph.add_node('interpret',interpret)
    graph.add_node('execute_authorized_tool',execute)
    graph.add_edge(START,'interpret')
    graph.add_edge('interpret','execute_authorized_tool')
    graph.add_edge('execute_authorized_tool',END)
    return graph.compile()
