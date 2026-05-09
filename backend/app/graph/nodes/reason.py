import logging

from app.graph.state import GraphState
from app.z3_engine.rules import run_z3_check

logger = logging.getLogger(__name__)


def reason_node(state: GraphState) -> GraphState:
    """
    Node 2: run Z3 when the question is logical and user facts are available.
    """
    if state.get("question_type") != "logical":
        logger.info("[reason_node] not logical question, skipping Z3")
        return state

    user_facts = state.get("user_facts")
    if not user_facts:
        logger.info("[reason_node] no user_facts provided, skipping Z3")
        return state

    z3_result = run_z3_check(state["question"], user_facts)

    if z3_result and z3_result.get("verified"):
        confidence = min(state["confidence"] + 0.15, 0.98)
    else:
        confidence = state["confidence"]

    return {
        **state,
        "z3_result": z3_result,
        "confidence": confidence,
    }
