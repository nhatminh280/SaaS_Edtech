import operator
from typing import Annotated, Optional, TypedDict


class GraphState(TypedDict):
    question: str
    question_type: Optional[str]
    user_facts: Optional[dict]
    retrieved_chunks: Annotated[list, operator.add]
    citations: list
    z3_result: Optional[dict]
    answer: Optional[str]
    confidence: float
    error: Optional[str]


def initial_state(question: str, user_facts: Optional[dict] = None) -> GraphState:
    return {
        "question": question,
        "question_type": None,
        "user_facts": user_facts,
        "retrieved_chunks": [],
        "citations": [],
        "z3_result": None,
        "answer": None,
        "confidence": 0.0,
        "error": None,
    }
