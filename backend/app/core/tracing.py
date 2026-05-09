import logging
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)
_OPIK_CONFIGURED = False


def is_opik_enabled() -> bool:
    return bool(settings.opik_enabled)


def create_opik_tracer(thread_id: str | None = None):
    global _OPIK_CONFIGURED

    if not is_opik_enabled():
        return None

    try:
        import os

        import opik
        from opik.integrations.langchain import OpikTracer

        if settings.opik_api_key:
            os.environ.setdefault("OPIK_API_KEY", settings.opik_api_key)
        if settings.opik_base_url:
            os.environ.setdefault("OPIK_BASE_URL", settings.opik_base_url)
        if settings.opik_workspace:
            os.environ.setdefault("OPIK_WORKSPACE", settings.opik_workspace)

        if not _OPIK_CONFIGURED:
            opik.configure(project_name=settings.opik_project_name)
            _OPIK_CONFIGURED = True
        kwargs: dict[str, Any] = {
            "project_name": settings.opik_project_name,
            "tags": ["phase3", "rag", "z3", "backend"],
            "metadata": {
                "service": "qa-quy-che-hcmus",
                "embedding_provider": settings.embedding_provider,
                "llm_provider": settings.llm_provider,
                "llm_model": settings.openai_model
                if settings.llm_provider == "openai"
                else settings.google_model
                if settings.llm_provider == "google"
                else settings.anthropic_model,
            },
        }
        if thread_id:
            kwargs["thread_id"] = thread_id
        return OpikTracer(**kwargs)
    except Exception as exc:
        logger.warning("Opik tracing disabled for this request: %s", exc)
        return None


def graph_config_for_tracer(tracer) -> dict | None:
    if tracer is None:
        return None
    return {"callbacks": [tracer]}


def track_openai_client(client):
    if not is_opik_enabled():
        return client

    try:
        from opik.integrations.openai import track_openai

        return track_openai(client, project_name=settings.opik_project_name)
    except Exception as exc:
        logger.warning("OpenAI Opik tracking unavailable: %s", exc)
        return client


def log_answer_feedback(tracer, response: dict) -> None:
    if tracer is None:
        return

    try:
        traces = tracer.created_traces()
    except Exception as exc:
        logger.debug("Could not access Opik traces: %s", exc)
        return

    citations = response.get("citations") or []
    z3_result = response.get("z3_result")
    question_type = response.get("question_type")
    scores = {
        "answer_not_empty": 1.0 if response.get("answer") else 0.0,
        "has_citation": 1.0 if citations else 0.0,
        "has_pdf_url": 1.0 if any(citation.get("pdf_url") for citation in citations) else 0.0,
        "confidence": float(response.get("confidence") or 0.0),
    }
    if question_type == "logical":
        scores["z3_present_for_logical"] = 1.0 if z3_result else 0.0
        scores["z3_verified"] = 1.0 if z3_result and z3_result.get("verified") else 0.0

    for trace in traces:
        for name, value in scores.items():
            try:
                trace.log_feedback_score(name=name, value=value)
            except TypeError:
                trace.log_feedback_score(name, value)

    try:
        tracer.flush()
    except Exception:
        pass
