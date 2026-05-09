import logging

from app.graph.state import GraphState
from app.rag.retriever import search_chunks

logger = logging.getLogger(__name__)

LOGICAL_KEYWORDS = [
    "nếu",
    "nếu như",
    "có được",
    "có thể không",
    "đủ điều kiện",
    "được phép",
    "có đủ",
    "bao nhiêu tín chỉ",
    "điều kiện",
    "có bị",
    "sẽ bị",
    "có được xét",
    "liệu tôi",
]

PROCEDURAL_KEYWORDS = [
    "quy trình",
    "thủ tục",
    "làm thế nào",
    "cách",
    "bước",
    "nộp đơn",
    "đăng ký",
    "xin",
    "làm đơn",
]


def classify_question(question: str) -> str:
    question_lower = question.lower()
    if any(keyword in question_lower for keyword in LOGICAL_KEYWORDS):
        return "logical"
    if any(keyword in question_lower for keyword in PROCEDURAL_KEYWORDS):
        return "procedural"
    return "factual"


def retrieve_node(state: GraphState) -> GraphState:
    question = state["question"]
    question_type = classify_question(question)
    logger.info("[retrieve] type=%s | q=%s...", question_type, question[:60])

    chunks = search_chunks(question, n_results=5, min_score=0.25)

    citations = []
    avg_score = 0.0
    for chunk in chunks:
        metadata = chunk.get("metadata") or {}
        dieu_khoan = metadata.get("dieu_khoan", "Không xác định")
        page = metadata.get("trang")
        citations.append(
            {
                "dieu_khoan": dieu_khoan,
                "noi_dung": chunk["document"][:400],
                "nguon": metadata.get("nguon", "Quy chế HCMUS"),
                "chunk_id": chunk["id"],
            }
        )
        if page:
            citations[-1]["noi_dung"] = f"(Trang {page}) {citations[-1]['noi_dung']}"
        avg_score += chunk.get("score", 0.0)

    if chunks:
        avg_score /= len(chunks)

    confidence = min(0.4 + avg_score * 0.5, 0.85)

    return {
        **state,
        "question_type": question_type,
        "retrieved_chunks": chunks,
        "citations": citations,
        "confidence": round(confidence, 3),
    }
