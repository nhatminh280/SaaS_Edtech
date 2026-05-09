import logging

from langgraph.graph import END, StateGraph

from app.graph.nodes.generate import generate_node
from app.graph.nodes.reason import reason_node
from app.graph.nodes.retrieve import retrieve_node
from app.graph.state import GraphState

logger = logging.getLogger(__name__)


def should_run_z3(state: GraphState) -> str:
    """Run Z3 only for logical questions with provided user facts."""
    if state.get("question_type") == "logical" and state.get("user_facts"):
        return "reason"
    return "generate"


def build_graph():
    """Build and compile the LangGraph workflow."""
    workflow = StateGraph(GraphState)

    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("reason", reason_node)
    workflow.add_node("generate", generate_node)

    workflow.set_entry_point("retrieve")
    workflow.add_conditional_edges(
        "retrieve",
        should_run_z3,
        {
            "reason": "reason",
            "generate": "generate",
        },
    )
    workflow.add_edge("reason", "generate")
    workflow.add_edge("generate", END)

    return workflow.compile()


graph = build_graph()
