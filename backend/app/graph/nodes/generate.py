import logging

from app.core.config import settings
from app.graph.state import GraphState

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Bạn là trợ lý tư vấn học vụ chính thức của Trường Đại học Khoa học Tự nhiên (HCMUS).

NHIỆM VỤ: Trả lời câu hỏi của sinh viên dựa CHÍNH XÁC trên các điều khoản quy chế được cung cấp.

QUY TẮC BẮT BUỘC:
1. Chỉ dùng thông tin từ context. Không tự suy diễn thêm ngoài điều khoản.
2. Trích dẫn cụ thể: viết [Điều X, Khoản Y] sau mỗi thông tin quan trọng.
3. Nếu context không đủ -> nói "Tôi không tìm thấy điều khoản cụ thể, sinh viên nên liên hệ Phòng Đào tạo."
4. Nếu có kết quả Z3 -> đề cập ở cuối với badge rõ ràng.
5. Ngắn gọn, súc tích. Tối đa 200 từ.
6. Dùng tiếng Việt tự nhiên, tránh văn phong hành chính cứng nhắc.

FORMAT TRẢ LỜI:
[Câu trả lời chính, 2-4 câu, có trích dẫn [Điều X]]

Điều khoản áp dụng: [Điều X, Khoản Y]; [Điều Z]
[Nếu có kết quả Z3]: Đã xác minh bằng logic hình thức / Chưa đủ điều kiện theo [Điều X]
"""


def _build_context(chunks: list[dict]) -> str:
    parts = []
    for chunk in chunks:
        metadata = chunk.get("metadata") or {}
        label = metadata.get("dieu_khoan", "Đoạn văn")
        score = chunk.get("score", 0.0)
        parts.append(f"[{label}] (độ liên quan: {score:.0%})\n{chunk.get('document', '')}")
    return "\n\n---\n\n".join(parts)


def _has_provider_key(provider: str) -> bool:
    if provider == "openai":
        return bool(settings.openai_api_key and settings.openai_api_key != "sk-...")
    if provider == "google":
        return bool(settings.google_api_key and settings.google_api_key != "AIza...")
    if provider == "anthropic":
        return bool(settings.anthropic_api_key and settings.anthropic_api_key != "sk-ant-...")
    return False


def _call_llm(system: str, user: str, chunks: list[dict], z3_result: dict | None) -> str:
    provider = settings.llm_provider
    if not _has_provider_key(provider):
        return _fallback_answer(chunks, z3_result)

    try:
        if provider == "openai":
            from openai import OpenAI

            client = OpenAI(api_key=settings.openai_api_key)
            response = client.chat.completions.create(
                model=settings.openai_model,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                max_tokens=600,
                temperature=0.1,
            )
            return response.choices[0].message.content or ""

        if provider == "google":
            import google.generativeai as genai

            genai.configure(api_key=settings.google_api_key)
            model = genai.GenerativeModel(settings.google_model, system_instruction=system)
            return model.generate_content(user).text

        if provider == "anthropic":
            import anthropic

            client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
            response = client.messages.create(
                model=settings.anthropic_model,
                max_tokens=600,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
            return response.content[0].text
    except Exception as exc:
        logger.error("LLM error (%s): %s", provider, exc)
        return f"[Lỗi kết nối LLM: {exc}. Kiểm tra API key trong .env]"

    return "[LLM provider không hợp lệ]"


def _fallback_answer(chunks: list[dict], z3_result: dict | None) -> str:
    if not chunks and not z3_result:
        return "Tôi không tìm thấy điều khoản cụ thể, sinh viên nên liên hệ Phòng Đào tạo."

    lines = []
    if chunks:
        first = chunks[0]
        metadata = first.get("metadata") or {}
        label = metadata.get("dieu_khoan", "Điều khoản liên quan")
        content = first.get("document", "").strip()
        lines.append(f"Theo [{label}], {content[:500]}")
        lines.append(f"Điều khoản áp dụng: [{label}]")

    if z3_result:
        status = "Đã xác minh bằng logic hình thức" if z3_result.get("verified") else "Chưa đủ điều kiện"
        lines.append(f"{status}: {z3_result.get('explanation', '')}")
        lines.append(f"Rule áp dụng: {z3_result.get('rule_applied', '')}")

    return "\n\n".join(lines)


def generate_node(state: GraphState) -> GraphState:
    question = state["question"]
    chunks = state["retrieved_chunks"]
    z3_result = state.get("z3_result")

    if not chunks and not z3_result:
        return {
            **state,
            "answer": _fallback_answer(chunks, z3_result),
        }

    context = _build_context(chunks) if chunks else "Không tìm thấy điều khoản liên quan."

    z3_section = ""
    if z3_result:
        status = "ĐÃ XÁC MINH (verified=True)" if z3_result.get("verified") else "KHÔNG ĐỦ ĐIỀU KIỆN (verified=False)"
        z3_section = (
            f"\n\nKẾT QUẢ XÁC MINH LOGIC Z3 ({status}):\n"
            f"{z3_result.get('explanation', '')}\n"
            f"Rule áp dụng: {z3_result.get('rule_applied', '')}"
        )

    user_prompt = f"""Câu hỏi: {question}

Điều khoản liên quan từ quy chế:
{context}
{z3_section}

Hãy trả lời câu hỏi theo format đã hướng dẫn."""

    answer = _call_llm(SYSTEM_PROMPT, user_prompt, chunks, z3_result)

    return {
        **state,
        "answer": answer,
    }
