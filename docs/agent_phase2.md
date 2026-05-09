# Agent Instructions — Phase 2: Core Pipeline (45'–2h)

> Build phần core của hệ thống: hoàn thiện LangGraph 3-node, cải thiện RAG chunking, bổ sung Z3 rules, và wire toàn bộ pipeline end-to-end.
> Phase 1 phải xong trước. Đọc hết file này trước khi code.

---

## Mục tiêu Phase 2

Sau phase này, pipeline phải:

1. LangGraph chạy end-to-end: câu hỏi vào → answer + citation ra
2. RAG tìm đúng điều khoản với cosine similarity >= 0.7
3. Z3 xác minh được ít nhất 3 rule logic phức tạp
4. LLM sinh câu trả lời có trích dẫn đúng format `[Điều X, Khoản Y]`
5. Confidence score phản ánh thực tế (RAG score + Z3 gate)
6. Frontend render citation + Z3 badge đẹp, không crash

---

## 2.1 Cải thiện chunking — `app/rag/ingest.py`

> Vấn đề Phase 1: chunk theo regex `Điều X` đơn giản, dễ split sai với quy chế thực tế.
> Phase 2: chunking thông minh hơn — sliding window + overlap + metadata phong phú.

```python
import fitz
import chromadb
from chromadb.utils import embedding_functions
from app.core.config import settings
from pathlib import Path
import re
import hashlib
import logging

logger = logging.getLogger(__name__)


def get_chroma_collection():
    client = chromadb.PersistentClient(path=settings.chroma_persist_dir)

    if settings.embedding_provider == "openai":
        ef = embedding_functions.OpenAIEmbeddingFunction(
            api_key=settings.openai_api_key,
            model_name=settings.embedding_model,
        )
    elif settings.embedding_provider == "google":
        ef = embedding_functions.GoogleGenerativeAiEmbeddingFunction(
            api_key=settings.google_api_key,
            model_name="models/text-embedding-004",
        )
    else:
        ef = embedding_functions.DefaultEmbeddingFunction()

    return client.get_or_create_collection(
        name=settings.chroma_collection,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},
    )


def extract_text_with_pages(pdf_path: str) -> list[dict]:
    """Extract text theo từng trang, giữ page number cho citation"""
    doc = fitz.open(pdf_path)
    pages = []
    for i, page in enumerate(doc):
        text = page.get_text("text")
        pages.append({"page": i + 1, "text": text})
    doc.close()
    return pages


def detect_article_boundaries(text: str) -> list[dict]:
    """
    Detect ranh giới điều khoản trong văn bản quy chế.
    Handle nhiều format: 'Điều 1.', 'Điều 1:', 'ĐIỀU 1', 'Chương I', 'Mục 1'
    """
    patterns = [
        (r'(?:^|\n)((?:CHƯƠNG|Chương)\s+[IVXLCDM\d]+[.:]\s*.+?)(?=\n)', 'chapter'),
        (r'(?:^|\n)((?:Điều|ĐIỀU)\s+\d+[.:]\s*.+?)(?=\n)', 'article'),
        (r'(?:^|\n)((?:Mục|MỤC)\s+\d+[.:]\s*.+?)(?=\n)', 'section'),
    ]

    boundaries = []
    for pattern, boundary_type in patterns:
        for match in re.finditer(pattern, text, re.MULTILINE):
            boundaries.append({
                "pos": match.start(),
                "header": match.group(1).strip(),
                "type": boundary_type,
            })

    boundaries.sort(key=lambda x: x["pos"])
    return boundaries


def sliding_window_chunks(text: str, chunk_size: int = 500, overlap: int = 100) -> list[str]:
    """Sliding window chunking cho đoạn text không có cấu trúc rõ"""
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk_words = words[i:i + chunk_size]
        chunks.append(" ".join(chunk_words))
        i += chunk_size - overlap
    return chunks


def parse_pdf_smart(pdf_path: str) -> list[dict]:
    """
    Smart chunking: ưu tiên split theo điều khoản, fallback sliding window.
    Mỗi chunk có metadata: dieu_khoan, chuong, trang, nguon, chunk_hash
    """
    pages = extract_text_with_pages(pdf_path)
    full_text = "\n".join(p["text"] for p in pages)
    nguon = Path(pdf_path).stem

    boundaries = detect_article_boundaries(full_text)

    chunks = []

    if len(boundaries) >= 3:
        # Có đủ cấu trúc điều khoản → split theo ranh giới
        current_chapter = "Chưa xác định"
        current_article = "Mở đầu"

        for i, boundary in enumerate(boundaries):
            # Lấy text từ boundary này đến boundary tiếp theo
            start = boundary["pos"]
            end = boundaries[i + 1]["pos"] if i + 1 < len(boundaries) else len(full_text)
            segment_text = full_text[start:end].strip()

            if boundary["type"] == "chapter":
                current_chapter = boundary["header"]
                continue
            if boundary["type"] == "article":
                current_article = boundary["header"]

            if len(segment_text) < 50:
                continue

            # Nếu segment quá dài → chia tiếp theo khoản
            if len(segment_text) > 800:
                khoan_pattern = r'\n\s*(\d+\.\s)'
                sub_parts = re.split(khoan_pattern, segment_text)
                khoan_idx = 0
                for j in range(0, len(sub_parts), 2):
                    part = sub_parts[j].strip()
                    if j + 1 < len(sub_parts):
                        part = sub_parts[j + 1] + part
                    if len(part) > 40:
                        khoan_idx += 1
                        chunk_text = f"{current_article}, Khoản {khoan_idx}: {part}"
                        chunks.append({
                            "text": chunk_text,
                            "dieu_khoan": f"{current_article}, Khoản {khoan_idx}",
                            "chuong": current_chapter,
                            "nguon": nguon,
                            "chunk_hash": hashlib.md5(chunk_text.encode()).hexdigest()[:8],
                        })
            else:
                chunks.append({
                    "text": segment_text,
                    "dieu_khoan": current_article,
                    "chuong": current_chapter,
                    "nguon": nguon,
                    "chunk_hash": hashlib.md5(segment_text.encode()).hexdigest()[:8],
                })
    else:
        # Fallback: sliding window
        logger.warning("Không detect được cấu trúc điều khoản, dùng sliding window")
        sub_chunks = sliding_window_chunks(full_text, chunk_size=400, overlap=80)
        for i, text in enumerate(sub_chunks):
            chunks.append({
                "text": text,
                "dieu_khoan": f"Đoạn {i + 1}",
                "chuong": "Không xác định",
                "nguon": nguon,
                "chunk_hash": hashlib.md5(text.encode()).hexdigest()[:8],
            })

    logger.info(f"Smart parse: {len(chunks)} chunks từ {pdf_path}")
    return chunks


def ingest_pdf(pdf_path: str, reset: bool = False) -> int:
    """
    Ingest PDF vào ChromaDB.
    reset=True: xóa collection cũ trước khi ingest.
    """
    chunks = parse_pdf_smart(pdf_path)
    collection = get_chroma_collection()

    if reset:
        client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
        client.delete_collection(settings.chroma_collection)
        collection = get_chroma_collection()
        logger.info("Reset collection xong")

    batch_size = 50
    total = 0
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        collection.upsert(
            ids=[f"{c['chunk_hash']}_{i+j}" for j, c in enumerate(batch)],
            documents=[c["text"] for c in batch],
            metadatas=[{
                "dieu_khoan": c["dieu_khoan"],
                "chuong": c["chuong"],
                "nguon": c["nguon"],
            } for c in batch],
        )
        total += len(batch)

    logger.info(f"Ingest xong: {total} chunks")
    return total
```

---

## 2.2 Retriever với reranking — `app/rag/retriever.py`

```python
from app.rag.ingest import get_chroma_collection
import logging

logger = logging.getLogger(__name__)


def search_chunks(query: str, n_results: int = 5, min_score: float = 0.3) -> list[dict]:
    """
    Tìm chunks liên quan.
    - Lấy top n_results từ ChromaDB
    - Filter bỏ chunk có distance quá cao (không liên quan)
    - Trả về list dict chuẩn
    """
    try:
        collection = get_chroma_collection()

        # ChromaDB cosine distance: 0 = identical, 2 = opposite
        # Score thực = 1 - distance/2 (normalize về 0-1)
        results = collection.query(
            query_texts=[query],
            n_results=min(n_results, collection.count() or 1),
            include=["documents", "metadatas", "distances"],
        )

        chunks = []
        for i in range(len(results["ids"][0])):
            distance = results["distances"][0][i]
            score = max(0.0, 1.0 - distance / 2.0)

            if score < min_score:
                continue

            chunks.append({
                "id": results["ids"][0][i],
                "document": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "score": round(score, 3),
            })

        # Sort by score descending
        chunks.sort(key=lambda x: x["score"], reverse=True)

        # Giữ top 3 sau filter
        chunks = chunks[:3]

        logger.info(f"Retrieved {len(chunks)} chunks (scores: {[c['score'] for c in chunks]})")
        return chunks

    except Exception as e:
        logger.error(f"ChromaDB error: {e}")
        return []


def get_collection_stats() -> dict:
    """Trả về thống kê collection để debug"""
    try:
        col = get_chroma_collection()
        return {"total_chunks": col.count(), "collection": col.name}
    except Exception as e:
        return {"error": str(e)}
```

---

## 2.3 LangGraph Node 1 — `app/graph/nodes/retrieve.py` (hoàn chỉnh)

```python
from app.graph.state import GraphState
from app.rag.retriever import search_chunks
import logging

logger = logging.getLogger(__name__)

# Keywords phân loại câu hỏi
LOGICAL_KEYWORDS = [
    "nếu", "nếu như", "có được", "có thể không", "đủ điều kiện",
    "được phép", "có đủ", "bao nhiêu tín chỉ", "điều kiện",
    "có bị", "sẽ bị", "có được xét", "liệu tôi",
]

PROCEDURAL_KEYWORDS = [
    "quy trình", "thủ tục", "làm thế nào", "cách", "bước",
    "nộp đơn", "đăng ký", "xin", "làm đơn",
]


def classify_question(question: str) -> str:
    q = question.lower()
    if any(kw in q for kw in LOGICAL_KEYWORDS):
        return "logical"
    if any(kw in q for kw in PROCEDURAL_KEYWORDS):
        return "procedural"
    return "factual"


def retrieve_node(state: GraphState) -> GraphState:
    question = state["question"]
    question_type = classify_question(question)

    logger.info(f"[retrieve] type={question_type} | q={question[:60]}...")

    chunks = search_chunks(question, n_results=5, min_score=0.25)

    # Build citations
    citations = []
    avg_score = 0.0
    for chunk in chunks:
        meta = chunk.get("metadata", {})
        citations.append({
            "dieu_khoan": meta.get("dieu_khoan", "Không xác định"),
            "noi_dung": chunk["document"][:400],
            "nguon": meta.get("nguon", "Quy chế HCMUS"),
            "chunk_id": chunk["id"],
        })
        avg_score += chunk.get("score", 0)

    if chunks:
        avg_score /= len(chunks)

    # Confidence ban đầu từ RAG score
    confidence = min(0.4 + avg_score * 0.5, 0.85)

    return {
        **state,
        "question_type": question_type,
        "retrieved_chunks": chunks,
        "citations": citations,
        "confidence": round(confidence, 3),
    }
```

---

## 2.4 LangGraph Node 2 — `app/graph/nodes/reason.py` (hoàn chỉnh)

```python
from app.graph.state import GraphState
from app.z3_engine.rules import run_z3_check
import logging

logger = logging.getLogger(__name__)


def reason_node(state: GraphState) -> GraphState:
    if state.get("question_type") != "logical":
        return state

    user_facts = state.get("user_facts")
    if not user_facts:
        logger.info("[reason] no user_facts → skip Z3")
        return state

    z3_result = run_z3_check(state["question"], user_facts)

    if z3_result is None:
        logger.info("[reason] no matching Z3 rule")
        return state

    # Z3 verified → boost confidence đáng kể
    confidence = state["confidence"]
    if z3_result.get("verified"):
        confidence = min(confidence + 0.13, 0.98)
    else:
        # Z3 kết luận rõ ràng (dù negative) → vẫn boost nhẹ (có answer rõ ràng)
        confidence = min(confidence + 0.05, 0.92)

    return {
        **state,
        "z3_result": z3_result,
        "confidence": round(confidence, 3),
    }
```

---

## 2.5 LangGraph Node 3 — `app/graph/nodes/generate.py` (hoàn chỉnh)

```python
from app.graph.state import GraphState
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Bạn là trợ lý tư vấn học vụ chính thức của Trường Đại học Khoa học Tự nhiên (HCMUS).

NHIỆM VỤ: Trả lời câu hỏi của sinh viên dựa CHÍNH XÁC trên các điều khoản quy chế được cung cấp.

QUY TẮC BẮT BUỘC:
1. Chỉ dùng thông tin từ context. Không tự suy diễn thêm ngoài điều khoản.
2. Trích dẫn cụ thể: viết [Điều X, Khoản Y] sau mỗi thông tin quan trọng.
3. Nếu context không đủ → nói "Tôi không tìm thấy điều khoản cụ thể, sinh viên nên liên hệ Phòng Đào tạo."
4. Nếu có kết quả Z3 → đề cập ở cuối với badge rõ ràng.
5. Ngắn gọn, súc tích. Tối đa 200 từ.
6. Dùng tiếng Việt tự nhiên, tránh văn phong hành chính cứng nhắc.

FORMAT TRẢ LỜI:
[Câu trả lời chính, 2-4 câu, có trích dẫn [Điều X]]

Điều khoản áp dụng: [Điều X, Khoản Y]; [Điều Z]
[Nếu có kết quả Z3]: ✓ Đã xác minh bằng logic hình thức / ✗ Chưa đủ điều kiện theo [Điều X]
"""


def _build_context(chunks: list[dict]) -> str:
    parts = []
    for chunk in chunks:
        meta = chunk.get("metadata", {})
        label = meta.get("dieu_khoan", "Đoạn văn")
        score = chunk.get("score", 0)
        parts.append(f"[{label}] (độ liên quan: {score:.0%})\n{chunk.get('document', '')}")
    return "\n\n---\n\n".join(parts)


def _call_llm(system: str, user: str) -> str:
    provider = settings.llm_provider
    try:
        if provider == "openai":
            from openai import OpenAI
            client = OpenAI(api_key=settings.openai_api_key)
            r = client.chat.completions.create(
                model=settings.openai_model,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                max_tokens=600,
                temperature=0.1,
            )
            return r.choices[0].message.content

        elif provider == "google":
            import google.generativeai as genai
            genai.configure(api_key=settings.google_api_key)
            model = genai.GenerativeModel(settings.google_model, system_instruction=system)
            return model.generate_content(user).text

        elif provider == "anthropic":
            import anthropic
            client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
            r = client.messages.create(
                model=settings.anthropic_model,
                max_tokens=600,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
            return r.content[0].text

    except Exception as e:
        logger.error(f"LLM error ({provider}): {e}")
        return f"[Lỗi kết nối LLM: {e}. Kiểm tra API key trong .env]"

    return "[LLM provider không hợp lệ]"


def generate_node(state: GraphState) -> GraphState:
    question = state["question"]
    chunks = state["retrieved_chunks"]
    z3_result = state.get("z3_result")

    context = _build_context(chunks) if chunks else "Không tìm thấy điều khoản liên quan."

    z3_section = ""
    if z3_result:
        status = "ĐÃ XÁC MINH (verified=True)" if z3_result.get("verified") else "KHÔNG ĐỦ ĐIỀU KIỆN (verified=False)"
        z3_section = f"\n\nKẾT QUẢ XÁC MINH LOGIC Z3 ({status}):\n{z3_result.get('explanation', '')}\nRule áp dụng: {z3_result.get('rule_applied', '')}"

    user_prompt = f"""Câu hỏi: {question}

Điều khoản liên quan từ quy chế:
{context}
{z3_section}

Hãy trả lời câu hỏi theo format đã hướng dẫn."""

    answer = _call_llm(SYSTEM_PROMPT, user_prompt)

    return {
        **state,
        "answer": answer,
    }
```

---

## 2.6 LangGraph Graph — `app/graph/graph.py` (hoàn chỉnh)

```python
from langgraph.graph import StateGraph, END
from app.graph.state import GraphState, initial_state
from app.graph.nodes.retrieve import retrieve_node
from app.graph.nodes.reason import reason_node
from app.graph.nodes.generate import generate_node
import logging

logger = logging.getLogger(__name__)


def route_after_retrieve(state: GraphState) -> str:
    """
    Sau retrieve: quyết định có cần chạy Z3 không.
    Chạy Z3 khi: logical question VÀ có user_facts VÀ có retrieved chunks.
    """
    is_logical = state.get("question_type") == "logical"
    has_facts = bool(state.get("user_facts"))
    has_chunks = bool(state.get("retrieved_chunks"))

    if is_logical and has_facts and has_chunks:
        logger.info("[router] → reason (Z3)")
        return "reason"

    logger.info("[router] → generate (skip Z3)")
    return "generate"


def route_after_reason(state: GraphState) -> str:
    """Sau reason luôn đi generate"""
    return "generate"


def build_graph():
    workflow = StateGraph(GraphState)

    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("reason", reason_node)
    workflow.add_node("generate", generate_node)

    workflow.set_entry_point("retrieve")

    workflow.add_conditional_edges(
        "retrieve",
        route_after_retrieve,
        {"reason": "reason", "generate": "generate"},
    )

    workflow.add_edge("reason", "generate")
    workflow.add_edge("generate", END)

    return workflow.compile()


# Singleton — import ở chỗ khác
graph = build_graph()
```

---

## 2.7 Z3 Rules đầy đủ — `app/z3_engine/rules.py`

```python
from z3 import *
import logging

logger = logging.getLogger(__name__)

# ============================================================
# Phase 2: 6 rules Z3 cover các case demo chính
# ============================================================


def check_graduation(facts: dict) -> dict:
    """Điều kiện tốt nghiệp đại học hệ chính quy"""
    s = Solver()
    tc = Int('tin_chi')
    dtb = Real('diem_tb')
    no_mon = Bool('no_mon')
    hoan_thanh_tttn = Bool('hoan_thanh_tttn')

    s.add(tc == facts.get("tin_chi_tich_luy", 0))
    s.add(dtb == facts.get("diem_tb", 0.0))
    s.add(no_mon == facts.get("no_mon", True))
    s.add(hoan_thanh_tttn == facts.get("hoan_thanh_tttn", False))

    # Rule: Điều 30 — Điều kiện tốt nghiệp
    rule = And(tc >= 120, dtb >= 2.0, no_mon == False, hoan_thanh_tttn == True)
    s.add(rule)

    if s.check() == sat:
        return {
            "verified": True,
            "rule_applied": "Điều 30, Khoản 1 — Điều kiện tốt nghiệp",
            "explanation": (
                f"✓ Đủ điều kiện tốt nghiệp: "
                f"{facts.get('tin_chi_tich_luy')} TC (≥120), "
                f"ĐTB {facts.get('diem_tb')} (≥2.0), "
                f"không nợ môn, đã hoàn thành thực tập."
            ),
        }

    # Phân tích lý do chưa đủ
    missing = []
    if facts.get("tin_chi_tich_luy", 0) < 120:
        missing.append(f"thiếu {120 - facts.get('tin_chi_tich_luy', 0)} TC")
    if facts.get("diem_tb", 0) < 2.0:
        missing.append(f"ĐTB {facts.get('diem_tb')} < 2.0")
    if facts.get("no_mon", True):
        missing.append("còn nợ môn học")
    if not facts.get("hoan_thanh_tttn", False):
        missing.append("chưa hoàn thành thực tập/ĐATN")

    return {
        "verified": False,
        "rule_applied": "Điều 30, Khoản 1 — Điều kiện tốt nghiệp",
        "explanation": f"✗ Chưa đủ điều kiện tốt nghiệp: {'; '.join(missing)}.",
    }


def check_canh_cao(facts: dict) -> dict:
    """Cảnh cáo học vụ"""
    s = Solver()
    dtb_hk = Real('dtb_hk')
    dtb_tl = Real('dtb_tl')

    s.add(dtb_hk == facts.get("diem_tb_hoc_ky", 2.0))
    s.add(dtb_tl == facts.get("diem_tb_tich_luy", 2.0))

    # Điều 22: bị cảnh cáo khi ĐTB HK < 1.0 HOẶC ĐTB TL < 1.2
    rule = Or(dtb_hk < 1.0, dtb_tl < 1.2)
    s.add(rule)

    if s.check() == sat:
        reasons = []
        if facts.get("diem_tb_hoc_ky", 2.0) < 1.0:
            reasons.append(f"ĐTB học kỳ {facts.get('diem_tb_hoc_ky')} < 1.0")
        if facts.get("diem_tb_tich_luy", 2.0) < 1.2:
            reasons.append(f"ĐTB tích lũy {facts.get('diem_tb_tich_luy')} < 1.2")
        return {
            "verified": True,
            "rule_applied": "Điều 22 — Cảnh cáo học vụ",
            "explanation": f"✓ Thuộc diện cảnh cáo học vụ: {'; '.join(reasons)}.",
        }

    return {
        "verified": False,
        "rule_applied": "Điều 22 — Cảnh cáo học vụ",
        "explanation": "✓ Không thuộc diện cảnh cáo học vụ.",
    }


def check_dinh_chi(facts: dict) -> dict:
    """Bị đình chỉ học tập"""
    s = Solver()
    so_lan_canh_cao = Int('so_lan_canh_cao')
    dtb_tl = Real('dtb_tl')

    s.add(so_lan_canh_cao == facts.get("so_lan_canh_cao", 0))
    s.add(dtb_tl == facts.get("diem_tb_tich_luy", 2.0))

    # Điều 23: đình chỉ khi ≥ 2 lần cảnh cáo HOẶC ĐTB TL < 0.8
    rule = Or(so_lan_canh_cao >= 2, dtb_tl < 0.8)
    s.add(rule)

    if s.check() == sat:
        return {
            "verified": True,
            "rule_applied": "Điều 23 — Đình chỉ học tập",
            "explanation": (
                f"✓ Thuộc diện đình chỉ: "
                f"{facts.get('so_lan_canh_cao')} lần cảnh cáo (≥2) "
                f"hoặc ĐTB {facts.get('diem_tb_tich_luy')} < 0.8."
            ),
        }
    return {
        "verified": False,
        "rule_applied": "Điều 23 — Đình chỉ học tập",
        "explanation": "✓ Không thuộc diện đình chỉ học tập.",
    }


def check_hoc_bong(facts: dict) -> dict:
    """Học bổng khuyến khích học tập"""
    s = Solver()
    dtb = Real('dtb')
    no_mon = Bool('no_mon')
    diem_rl = Int('diem_rl')

    s.add(dtb == facts.get("diem_tb", 0.0))
    s.add(no_mon == facts.get("no_mon", True))
    s.add(diem_rl == facts.get("diem_ren_luyen", 0))

    # Điều 25: ĐTB ≥ 3.2, không nợ môn, điểm rèn luyện ≥ 80
    rule = And(dtb >= 3.2, no_mon == False, diem_rl >= 80)
    s.add(rule)

    if s.check() == sat:
        return {
            "verified": True,
            "rule_applied": "Điều 25 — Học bổng khuyến khích",
            "explanation": (
                f"✓ Đủ điều kiện học bổng: "
                f"ĐTB {facts.get('diem_tb')} ≥ 3.2, "
                f"điểm rèn luyện {facts.get('diem_ren_luyen')} ≥ 80, "
                f"không nợ môn."
            ),
        }

    missing = []
    if facts.get("diem_tb", 0) < 3.2:
        missing.append(f"ĐTB {facts.get('diem_tb')} < 3.2")
    if facts.get("no_mon", True):
        missing.append("còn nợ môn")
    if facts.get("diem_ren_luyen", 0) < 80:
        missing.append(f"điểm rèn luyện {facts.get('diem_ren_luyen')} < 80")

    return {
        "verified": False,
        "rule_applied": "Điều 25 — Học bổng khuyến khích",
        "explanation": f"✗ Chưa đủ điều kiện học bổng: {'; '.join(missing)}.",
    }


def check_dang_ky_mon(facts: dict) -> dict:
    """Điều kiện đăng ký môn học"""
    s = Solver()
    hoan_thanh_tien_quyet = Bool('hoan_thanh_tien_quyet')
    khong_bi_cam = Bool('khong_bi_cam')
    dang_trong_thoi_gian_dk = Bool('dang_trong_thoi_gian_dk')

    s.add(hoan_thanh_tien_quyet == facts.get("hoan_thanh_tien_quyet", False))
    s.add(khong_bi_cam == facts.get("khong_bi_cam", True))
    s.add(dang_trong_thoi_gian_dk == facts.get("trong_thoi_gian_dang_ky", False))

    rule = And(hoan_thanh_tien_quyet == True, khong_bi_cam == True, dang_trong_thoi_gian_dk == True)
    s.add(rule)

    if s.check() == sat:
        return {
            "verified": True,
            "rule_applied": "Điều 10 — Đăng ký học phần",
            "explanation": "✓ Đủ điều kiện đăng ký môn học.",
        }

    missing = []
    if not facts.get("hoan_thanh_tien_quyet", False):
        missing.append("chưa hoàn thành môn tiên quyết")
    if not facts.get("khong_bi_cam", True):
        missing.append("đang bị cấm đăng ký")
    if not facts.get("trong_thoi_gian_dang_ky", False):
        missing.append("ngoài thời gian đăng ký")

    return {
        "verified": False,
        "rule_applied": "Điều 10 — Đăng ký học phần",
        "explanation": f"✗ Không đủ điều kiện đăng ký: {'; '.join(missing)}.",
    }


def check_bao_luu(facts: dict) -> dict:
    """Điều kiện bảo lưu kết quả học tập"""
    s = Solver()
    ly_do_hop_le = Bool('ly_do_hop_le')
    da_hoc_it_nhat_1_hk = Bool('da_hoc_it_nhat_1_hk')

    s.add(ly_do_hop_le == facts.get("ly_do_hop_le", False))
    s.add(da_hoc_it_nhat_1_hk == facts.get("da_hoc_it_nhat_1_hk", False))

    rule = And(ly_do_hop_le == True, da_hoc_it_nhat_1_hk == True)
    s.add(rule)

    if s.check() == sat:
        return {
            "verified": True,
            "rule_applied": "Điều 35 — Bảo lưu kết quả",
            "explanation": "✓ Đủ điều kiện bảo lưu kết quả học tập.",
        }

    return {
        "verified": False,
        "rule_applied": "Điều 35 — Bảo lưu kết quả",
        "explanation": "✗ Chưa đủ điều kiện bảo lưu: cần lý do hợp lệ và đã học ≥ 1 học kỳ.",
    }


# ============================================================
# Keyword router
# ============================================================

RULE_MAP = {
    "graduation": {
        "keywords": ["tốt nghiệp", "ra trường", "hoàn thành chương trình", "bằng tốt nghiệp"],
        "fn": check_graduation,
    },
    "canh_cao": {
        "keywords": ["cảnh cáo", "học vụ", "xếp loại yếu"],
        "fn": check_canh_cao,
    },
    "dinh_chi": {
        "keywords": ["đình chỉ", "bị đuổi", "thôi học", "buộc thôi học"],
        "fn": check_dinh_chi,
    },
    "hoc_bong": {
        "keywords": ["học bổng", "khuyến khích", "hỗ trợ học tập"],
        "fn": check_hoc_bong,
    },
    "dang_ky_mon": {
        "keywords": ["đăng ký môn", "đăng ký học phần", "đăng ký tín chỉ"],
        "fn": check_dang_ky_mon,
    },
    "bao_luu": {
        "keywords": ["bảo lưu", "tạm dừng học", "nghỉ học"],
        "fn": check_bao_luu,
    },
}


def run_z3_check(question: str, user_facts: dict) -> dict | None:
    q = question.lower()
    for rule_key, config in RULE_MAP.items():
        if any(kw in q for kw in config["keywords"]):
            logger.info(f"[Z3] matched rule: {rule_key}")
            try:
                return config["fn"](user_facts)
            except Exception as e:
                logger.error(f"[Z3] error in {rule_key}: {e}")
                return None
    return None
```

---

## 2.8 API routes nâng cao — `app/api/routes.py`

```python
from fastapi import APIRouter, HTTPException, Query
from app.core.schema import AskRequest, AskResponse, Citation, Z3Result, QuestionType
from app.graph.graph import graph
from app.graph.state import initial_state
from app.rag.retriever import get_collection_stats
import time
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health")
def health():
    stats = get_collection_stats()
    return {
        "status": "ok",
        "service": "QA Quy chế HCMUS",
        "chroma": stats,
    }


@router.post("/ask", response_model=AskResponse)
async def ask(request: AskRequest):
    t0 = time.time()
    try:
        state = initial_state(question=request.question, user_facts=request.user_facts)
        result = graph.invoke(state)

        citations = [Citation(**c) for c in result.get("citations", [])]
        z3_result = Z3Result(**result["z3_result"]) if result.get("z3_result") else None
        q_type = QuestionType(result.get("question_type", "factual"))

        return AskResponse(
            answer=result.get("answer", "Không thể trả lời."),
            question_type=q_type,
            citations=citations,
            confidence=result.get("confidence", 0.5),
            z3_result=z3_result,
            processing_time_ms=int((time.time() - t0) * 1000),
        )
    except Exception as e:
        logger.error(f"/ask error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/collection/stats")
def collection_stats():
    """Debug endpoint: xem ChromaDB có bao nhiêu chunks"""
    return get_collection_stats()


@router.post("/collection/ingest")
async def ingest(pdf_path: str = Query(..., description="Path đến file PDF trong server")):
    """Admin endpoint để ingest thêm PDF không cần restart"""
    from app.rag.ingest import ingest_pdf
    from pathlib import Path
    if not Path(pdf_path).exists():
        raise HTTPException(status_code=404, detail=f"File không tồn tại: {pdf_path}")
    total = ingest_pdf(pdf_path)
    return {"ingested_chunks": total, "pdf": pdf_path}
```

---

## 2.9 Test nhanh pipeline (chạy sau khi xong Phase 2)

```bash
# Test 1: Câu hỏi factual — không cần user_facts
curl -X POST http://localhost:8000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Sinh viên bị cảnh cáo học vụ khi nào?"
  }'

# Test 2: Câu hỏi logical + user_facts → Z3 chạy
curl -X POST http://localhost:8000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Tôi có đủ điều kiện tốt nghiệp không?",
    "user_facts": {
      "tin_chi_tich_luy": 125,
      "diem_tb": 2.8,
      "no_mon": false,
      "hoan_thanh_tttn": true
    }
  }'

# Test 3: Câu hỏi học bổng
curl -X POST http://localhost:8000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Tôi có được học bổng khuyến khích không?",
    "user_facts": {
      "diem_tb": 3.5,
      "no_mon": false,
      "diem_ren_luyen": 85
    }
  }'

# Check collection stats
curl http://localhost:8000/api/v1/collection/stats
```

---

## Checklist Phase 2 Done ✅

- [ ] Smart chunking detect được điều khoản trong PDF thật
- [ ] RAG trả về chunks có score >= 0.5 cho câu hỏi liên quan
- [ ] Z3 chạy đúng với test 2 (tốt nghiệp) và test 3 (học bổng)
- [ ] LLM trả lời có trích dẫn `[Điều X, Khoản Y]` trong text
- [ ] `/health` trả về số chunk trong ChromaDB > 0
- [ ] Pipeline không crash với câu hỏi không có user_facts

---

*Sang Phase 3: Wire FE ↔ BE, smoke test 5 câu demo, deploy ngrok.*
