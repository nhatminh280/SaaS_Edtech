import logging
import time

from fastapi import APIRouter, HTTPException

from app.core.schema import AskRequest, AskResponse, Citation, QuestionType, Z3Result
from app.graph.graph import graph
from app.graph.state import initial_state

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health")
def health_check():
    return {"status": "ok", "service": "QA Quy chế HCMUS"}


@router.post("/ask", response_model=AskResponse)
async def ask_question(request: AskRequest):
    start_time = time.time()

    try:
        state = initial_state(
            question=request.question,
            user_facts=request.user_facts,
        )

        result = graph.invoke(state)
        citations = [Citation(**citation) for citation in result.get("citations", [])]

        z3_result = None
        if result.get("z3_result"):
            z3_result = Z3Result(**result["z3_result"])

        question_type = QuestionType(result.get("question_type", "factual"))
        processing_time = int((time.time() - start_time) * 1000)

        return AskResponse(
            answer=result.get("answer", "Không thể trả lời câu hỏi này."),
            question_type=question_type,
            citations=citations,
            confidence=result.get("confidence", 0.5),
            z3_result=z3_result,
            processing_time_ms=processing_time,
        )

    except Exception as exc:
        logger.error("Error processing question: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
