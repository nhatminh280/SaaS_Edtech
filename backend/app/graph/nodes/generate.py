import logging

from app.core.config import settings
from app.graph.state import GraphState

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Bạn là trợ lý tư vấn học vụ của HCMUS. Nhiệm vụ của bạn là trả lời câu hỏi của sinh viên dựa trên các điều khoản quy chế được cung cấp.

Quy tắc bắt buộc:
1. CHỈ trả lời dựa trên các điều khoản được cung cấp trong context. Không tự bịa thêm.
2. Mỗi thông tin quan trọng PHẢI có trích dẫn điều khoản cụ thể dạng [Điều X, Khoản Y].
3. Nếu context không đủ thông tin -> nói rõ "Tôi không tìm thấy điều khoản cụ thể về vấn đề này".
4. Câu trả lời ngắn gọn, rõ ràng, dùng tiếng Việt tự nhiên.
5. Nếu có kết quả xác minh Z3 -> đề cập ở cuối câu trả lời.
"""


def generate_node(state: GraphState) -> GraphState:
    """
    Node 3: call LLM with RAG context and optional Z3 result.
    """
    question = state["question"]
    chunks = state["retrieved_chunks"]
    z3_result = state.get("z3_result")

    context_parts = []
    for i, chunk in enumerate(chunks):
        metadata = chunk.get("metadata") or {}
        dieu_khoan = metadata.get("dieu_khoan", f"Đoạn {i + 1}")
        context_parts.append(f"[{dieu_khoan}]: {chunk.get('document', '')}")

    context = "\n\n".join(context_parts)

    z3_note = ""
    if z3_result:
        status = "DA XAC MINH" if z3_result.get("verified") else "KHONG DU DIEU KIEN"
        z3_note = f"\n\nKết quả xác minh logic ({status}): {z3_result.get('explanation', '')}"

    user_prompt = f"""Câu hỏi của sinh viên: {question}

Các điều khoản liên quan từ quy chế:
{context}
{z3_note}

Hãy trả lời câu hỏi dựa trên các điều khoản trên."""

    answer = _call_llm(user_prompt, chunks=chunks, z3_result=z3_result)

    return {
        **state,
        "answer": answer,
    }


def _call_llm(user_prompt: str, chunks: list[dict], z3_result: dict | None = None) -> str:
    """Call the configured LLM provider, with a local fallback for Phase 1 demos."""
    provider = settings.llm_provider

    if not _has_provider_key(provider):
        return _fallback_answer(chunks, z3_result)

    try:
        if provider == "openai":
            from openai import OpenAI

            client = OpenAI(api_key=settings.openai_api_key)
            response = client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=800,
                temperature=0.1,
            )
            return response.choices[0].message.content or ""

        if provider == "google":
            import google.generativeai as genai

            genai.configure(api_key=settings.google_api_key)
            model = genai.GenerativeModel(
                model_name=settings.google_model,
                system_instruction=SYSTEM_PROMPT,
            )
            response = model.generate_content(user_prompt)
            return response.text

        if provider == "anthropic":
            import anthropic

            client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
            response = client.messages.create(
                model=settings.anthropic_model,
                max_tokens=800,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
            )
            return response.content[0].text
    except Exception as exc:
        logger.error("LLM call failed: %s", exc)
        return _fallback_answer(chunks, z3_result)

    return f"LLM provider '{provider}' chưa được hỗ trợ. Vui lòng kiểm tra cấu hình."


def _has_provider_key(provider: str) -> bool:
    if provider == "openai":
        return bool(settings.openai_api_key and settings.openai_api_key != "sk-...")
    if provider == "google":
        return bool(settings.google_api_key and settings.google_api_key != "AIza...")
    if provider == "anthropic":
        return bool(settings.anthropic_api_key and settings.anthropic_api_key != "sk-ant-...")
    return False


def _fallback_answer(chunks: list[dict], z3_result: dict | None) -> str:
    if not chunks and not z3_result:
        return (
            "Tôi chưa tìm thấy điều khoản cụ thể về vấn đề này. "
            "Vui lòng ingest PDF quy chế vào ChromaDB và cấu hình API key LLM để có câu trả lời đầy đủ."
        )

    lines = []
    if chunks:
        first_chunk = chunks[0]
        metadata = first_chunk.get("metadata") or {}
        dieu_khoan = metadata.get("dieu_khoan", "điều khoản liên quan")
        content = first_chunk.get("document", "").strip()
        lines.append(f"Theo [{dieu_khoan}], {content[:500]}")

    if z3_result:
        lines.append(f"Kết quả xác minh logic: {z3_result.get('explanation', '')}")

    return "\n\n".join(lines)
