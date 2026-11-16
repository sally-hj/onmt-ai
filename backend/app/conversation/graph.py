"""Coordination bornée des spécialistes et de leurs outils autorisés."""
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph


class Turn(TypedDict, total=False):
    message: str
    context: dict
    access: Any
    language: str
    intent: Any
    response: dict
    prepared: list
    specialist_trace: list
    seasonal: dict
    evidence_result: Any
    request_id: str


def build_graph(interpret, execute, specialists):
    graph = StateGraph(Turn)
    for name,function in [('planification',interpret),('territorial',specialists.territorial),
        ('marches',specialists.markets),('saisonnalite',specialists.seasonality),
        ('budget_performance',specialists.budget),('recherche',specialists.research),
        ('comex',execute),('verification',specialists.verify)]:
        graph.add_node(name,function)
    graph.add_edge(START,'planification'); graph.add_edge('planification','territorial')
    graph.add_conditional_edges('territorial',specialists.route,{'markets':'marches','seasonality':'saisonnalite','budget':'budget_performance','research':'recherche','execute':'comex'})
    graph.add_conditional_edges('marches',lambda t:'saisonnalite' if t['intent'].action=='briefing' else 'comex')
    graph.add_conditional_edges('saisonnalite',lambda t:'budget_performance' if t.get('seasonal',{}).get('needs_budget') or t['intent'].action=='briefing' else 'comex')
    graph.add_edge('budget_performance','recherche'); graph.add_edge('recherche','comex')
    graph.add_edge('comex','verification'); graph.add_edge('verification',END)
    return graph.compile()
