import logging

from app.graph.state import GraphState
from app.rag.retriever import search_chunks

logger = logging.getLogger(__name__)


def retrieve_node(state: GraphState) -> GraphState:
    """
    Node 1: embed/search ChromaDB for top chunks and classify question type.
    Phase 2 can replace keyword classification with LLM routing.
    """
    question = state["question"]
    logger.info("[retrieve_node] question: %s...", question[:80])

    question_lower = question.lower()
    logical_keywords = [
        "nếu",
        "nếu như",
        "có được",
        "có thể",
        "đủ điều kiện",
        "được phép",
        "có đủ",
        "bao nhiêu tín chỉ",
        "điều kiện",
    ]
    procedural_keywords = ["quy trình", "thủ tục", "đăng ký", "nộp", "bảo lưu"]

    if any(keyword in question_lower for keyword in logical_keywords):
        question_type = "logical"
    elif any(keyword in question_lower for keyword in procedural_keywords):
        question_type = "procedural"
    else:
        question_type = "factual"

    chunks = search_chunks(question, n_results=3)

    citations = []
    for chunk in chunks:
        metadata = chunk.get("metadata") or {}
        citations.append(
            {
                "dieu_khoan": metadata.get("dieu_khoan", "Không xác định"),
                "noi_dung": chunk.get("document", "")[:300],
                "nguon": metadata.get("nguon", "Quy chế HCMUS"),
                "chunk_id": chunk.get("id"),
            }
        )

    return {
        **state,
        "question_type": question_type,
        "retrieved_chunks": chunks,
        "citations": citations,
        "confidence": min(0.5 + len(chunks) * 0.1, 0.85),
    }
