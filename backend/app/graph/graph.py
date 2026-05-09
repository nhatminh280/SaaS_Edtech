import logging

from langgraph.graph import END, StateGraph

from app.graph.nodes.generate import generate_node
from app.graph.nodes.reason import reason_node
from app.graph.nodes.retrieve import retrieve_node
from app.graph.state import GraphState

logger = logging.getLogger(__name__)


def route_after_retrieve(state: GraphState) -> str:
    """
    After retrieve, decide if Z3 should run.
    Z3 runs only for logical questions with user facts and retrieved evidence.
    """
    is_logical = state.get("question_type") == "logical"
    has_facts = bool(state.get("user_facts"))
    has_chunks = bool(state.get("retrieved_chunks"))

    if is_logical and has_facts and has_chunks:
        logger.info("[router] -> reason (Z3)")
        return "reason"

    logger.info("[router] -> generate (skip Z3)")
    return "generate"


def build_graph():
    workflow = StateGraph(GraphState)

    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("reason", reason_node)
    workflow.add_node("generate", generate_node)

    workflow.set_entry_point("retrieve")
    workflow.add_conditional_edges(
        "retrieve",
        route_after_retrieve,
        {"reason": "reason", "generate": "generate"},
    )
    workflow.add_edge("reason", "generate")
    workflow.add_edge("generate", END)

    return workflow.compile()


graph = build_graph()
