import logging

from app.graph.state import GraphState
from app.z3_engine.rules import run_z3_check

logger = logging.getLogger(__name__)


def reason_node(state: GraphState) -> GraphState:
    if state.get("question_type") != "logical":
        return state

    user_facts = state.get("user_facts")
    if not user_facts:
        logger.info("[reason] no user_facts, skipping Z3")
        return state

    z3_result = run_z3_check(state["question"], user_facts)
    if z3_result is None:
        logger.info("[reason] no matching Z3 rule")
        return state

    confidence = state["confidence"]
    if z3_result.get("verified"):
        confidence = min(confidence + 0.13, 0.98)
    else:
        confidence = min(confidence + 0.05, 0.92)

    return {
        **state,
        "z3_result": z3_result,
        "confidence": round(confidence, 3),
    }
