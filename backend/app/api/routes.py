import logging
import time
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from app.core.schema import AskRequest, AskResponse, Citation, QuestionType, Z3Result
from app.core.tracing import create_opik_tracer, graph_config_for_tracer, log_answer_feedback
from app.graph.graph import graph
from app.graph.state import initial_state
from app.rag.retriever import get_collection_stats

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "QA Quy chế HCMUS",
        "chroma": get_collection_stats(),
    }


@router.post("/ask", response_model=AskResponse)
async def ask_question(request: AskRequest):
    start_time = time.time()

    try:
        state = initial_state(question=request.question, user_facts=request.user_facts)
        tracer = create_opik_tracer(thread_id=request.question[:80])
        graph_config = graph_config_for_tracer(tracer)
        result = graph.invoke(state, config=graph_config) if graph_config else graph.invoke(state)

        citations = [Citation(**citation) for citation in result.get("citations", [])]
        z3_result = Z3Result(**result["z3_result"]) if result.get("z3_result") else None
        question_type = QuestionType(result.get("question_type", "factual"))

        response = AskResponse(
            answer=result.get("answer", "Không thể trả lời."),
            question_type=question_type,
            citations=citations,
            confidence=result.get("confidence", 0.5),
            z3_result=z3_result,
            processing_time_ms=int((time.time() - start_time) * 1000),
        )
        log_answer_feedback(tracer, response.model_dump())
        return response

    except Exception as exc:
        logger.error("/ask error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/collection/stats")
def collection_stats():
    """Debug endpoint for ChromaDB collection size and name."""
    return get_collection_stats()


@router.post("/collection/ingest")
async def ingest_collection(
    pdf_path: str = Query(..., description="Path đến file PDF trong server"),
    reset: bool = Query(False, description="Xóa collection cũ trước khi ingest"),
):
    """Admin endpoint to ingest a PDF without restarting the backend."""
    from app.rag.ingest import ingest_pdf

    path = Path(pdf_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"File không tồn tại: {pdf_path}")

    total = ingest_pdf(str(path), reset=reset)
    return {"ingested_chunks": total, "pdf": str(path), "reset": reset}
