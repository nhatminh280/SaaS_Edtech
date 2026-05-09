# Agent Instructions — Phase 1: Setup & Scaffold (0–45 phút)

> Đây là file hướng dẫn cho AI agent (Cursor / Windsurf / Claude Code) build phần scaffold ban đầu của hệ thống **QA Quy chế Đại học** với LangGraph + RAG + Z3.
> Đọc hết file này trước khi viết bất kỳ dòng code nào.

---

## Mục tiêu Phase 1

Sau 45 phút, hệ thống phải có:

1. Monorepo cấu trúc rõ ràng, mọi người clone và chạy được ngay
2. Backend FastAPI skeleton với 2 endpoint hoạt động (`POST /ask`, `GET /health`)
3. ChromaDB khởi tạo được, ingest được 1 file PDF mẫu
4. Pydantic schema cho toàn bộ data flow
5. Frontend Vite React với chat UI cơ bản gọi được API
6. `.env.example` đầy đủ, không hardcode key

---

## Cấu trúc thư mục cần tạo

```
project-root/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI entry point
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── routes.py        # POST /ask, GET /health
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py        # Settings từ .env
│   │   │   └── schema.py        # Pydantic models
│   │   ├── graph/
│   │   │   ├── __init__.py
│   │   │   ├── graph.py         # LangGraph definition (stub)
│   │   │   ├── nodes/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── retrieve.py  # RAG node (stub)
│   │   │   │   ├── reason.py    # Z3 node (stub)
│   │   │   │   └── generate.py  # LLM generate node (stub)
│   │   │   └── state.py         # GraphState TypedDict
│   │   ├── rag/
│   │   │   ├── __init__.py
│   │   │   ├── ingest.py        # PDF → chunks → ChromaDB
│   │   │   └── retriever.py     # Query ChromaDB
│   │   └── z3_engine/
│   │       ├── __init__.py
│   │       └── rules.py         # Z3 rule stubs
│   ├── data/
│   │   └── .gitkeep             # Đặt PDF quy chế vào đây
│   ├── chroma_db/
│   │   └── .gitkeep             # ChromaDB persist directory
│   ├── scripts/
│   │   └── ingest_pdf.py        # Script chạy tay để ingest
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   ├── components/
│   │   │   ├── ChatWindow.jsx
│   │   │   ├── MessageBubble.jsx
│   │   │   ├── CitationTag.jsx
│   │   │   └── ConfidenceBadge.jsx
│   │   ├── hooks/
│   │   │   └── useChat.js
│   │   └── api/
│   │       └── client.js
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── docker-compose.yml
└── README.md
```

---

## 1. Backend — `requirements.txt`

```txt
fastapi==0.115.0
uvicorn[standard]==0.30.6
python-dotenv==1.0.1
pydantic==2.9.0
pydantic-settings==2.5.2

# LangGraph + LangChain
langgraph==0.2.35
langchain==0.3.4
langchain-core==0.3.10
langchain-openai==0.2.3
langchain-google-genai==2.0.1

# Vector DB
chromadb==0.5.15

# PDF parsing
pymupdf==1.24.11

# Z3 Solver
z3-solver==4.13.3.0

# HTTP
httpx==0.27.2
```

---

## 2. Backend — `.env.example`

```env
# === LLM Provider (chọn 1) ===
LLM_PROVIDER=openai          # hoặc: google, anthropic

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini

# Google Gemini
GOOGLE_API_KEY=AIza...
GOOGLE_MODEL=gemini-1.5-flash

# Anthropic Claude
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-5-haiku-20241022

# === Embedding ===
EMBEDDING_PROVIDER=openai    # hoặc: google
EMBEDDING_MODEL=text-embedding-3-small

# === ChromaDB ===
CHROMA_PERSIST_DIR=./chroma_db
CHROMA_COLLECTION=quy_che_hcmus

# === App ===
APP_PORT=8000
CORS_ORIGINS=http://localhost:5173
LOG_LEVEL=INFO
```

---

## 3. Backend — `app/core/config.py`

```python
from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    # LLM
    llm_provider: Literal["openai", "google", "anthropic"] = "openai"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    google_api_key: str = ""
    google_model: str = "gemini-1.5-flash"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-3-5-haiku-20241022"

    # Embedding
    embedding_provider: str = "openai"
    embedding_model: str = "text-embedding-3-small"

    # ChromaDB
    chroma_persist_dir: str = "./chroma_db"
    chroma_collection: str = "quy_che_hcmus"

    # App
    app_port: int = 8000
    cors_origins: str = "http://localhost:5173"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
```

---

## 4. Backend — `app/core/schema.py`

> **QUAN TRỌNG:** Đây là contract giữa tất cả các module. Không được thay đổi field name sau khi đã thống nhất.

```python
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class QuestionType(str, Enum):
    FACTUAL = "factual"        # Câu hỏi tra cứu đơn giản
    PROCEDURAL = "procedural"  # Câu hỏi về quy trình
    LOGICAL = "logical"        # Câu hỏi cần suy luận logic (if-then)


class Citation(BaseModel):
    dieu_khoan: str = Field(..., description="Ví dụ: Điều 15, Khoản 2")
    noi_dung: str = Field(..., description="Nội dung điều khoản trích dẫn")
    nguon: str = Field(..., description="Tên văn bản nguồn")
    chunk_id: Optional[str] = None


class Z3Result(BaseModel):
    verified: bool
    rule_applied: str
    explanation: str


class AskRequest(BaseModel):
    question: str = Field(..., min_length=5, max_length=500)
    user_facts: Optional[dict] = Field(
        default=None,
        description="Thông tin sinh viên nếu câu hỏi cần suy luận cá nhân. VD: {'tin_chi_tich_luy': 115, 'diem_tb': 2.3}"
    )


class AskResponse(BaseModel):
    answer: str
    question_type: QuestionType
    citations: list[Citation]
    confidence: float = Field(..., ge=0.0, le=1.0)
    z3_result: Optional[Z3Result] = None
    processing_time_ms: int


class GraphState(BaseModel):
    """State được truyền qua các node trong LangGraph"""
    question: str
    question_type: Optional[QuestionType] = None
    user_facts: Optional[dict] = None
    retrieved_chunks: list[dict] = []
    citations: list[Citation] = []
    z3_result: Optional[Z3Result] = None
    answer: Optional[str] = None
    confidence: float = 0.0
    error: Optional[str] = None
```

---

## 5. Backend — `app/graph/state.py`

```python
from typing import TypedDict, Optional, Annotated
from app.core.schema import QuestionType, Citation, Z3Result
import operator


class GraphState(TypedDict):
    question: str
    question_type: Optional[str]
    user_facts: Optional[dict]
    retrieved_chunks: Annotated[list, operator.add]  # accumulate chunks
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
```

---

## 6. Backend — `app/graph/nodes/retrieve.py`

```python
from app.graph.state import GraphState
from app.rag.retriever import search_chunks
import logging

logger = logging.getLogger(__name__)


def retrieve_node(state: GraphState) -> GraphState:
    """
    Node 1: Nhận câu hỏi → embed → search ChromaDB → trả top-3 chunks.
    Cũng phân loại question_type dựa trên keyword đơn giản.
    """
    question = state["question"]
    logger.info(f"[retrieve_node] question: {question[:80]}...")

    # Simple keyword-based question type classification
    # Phase 2 sẽ dùng LLM để classify chính xác hơn
    logical_keywords = ["nếu", "nếu như", "có được", "có thể", "đủ điều kiện",
                        "được phép", "có đủ", "bao nhiêu tín chỉ", "điều kiện"]
    question_type = "logical" if any(kw in question.lower() for kw in logical_keywords) else "factual"

    # Search ChromaDB
    chunks = search_chunks(question, n_results=3)

    # Build citations từ chunks
    citations = []
    for chunk in chunks:
        meta = chunk.get("metadata", {})
        citations.append({
            "dieu_khoan": meta.get("dieu_khoan", "Không xác định"),
            "noi_dung": chunk.get("document", "")[:300],
            "nguon": meta.get("nguon", "Quy chế HCMUS"),
            "chunk_id": chunk.get("id"),
        })

    return {
        **state,
        "question_type": question_type,
        "retrieved_chunks": chunks,
        "citations": citations,
        "confidence": min(0.5 + len(chunks) * 0.1, 0.85),  # sơ bộ
    }
```

---

## 7. Backend — `app/graph/nodes/reason.py`

```python
from app.graph.state import GraphState
from app.z3_engine.rules import run_z3_check
import logging

logger = logging.getLogger(__name__)


def reason_node(state: GraphState) -> GraphState:
    """
    Node 2: Chạy Z3 nếu question_type == 'logical' VÀ user_facts có đủ data.
    Nếu không đủ điều kiện → skip, trả state nguyên xi.
    """
    if state.get("question_type") != "logical":
        logger.info("[reason_node] not logical question, skipping Z3")
        return state

    user_facts = state.get("user_facts")
    if not user_facts:
        logger.info("[reason_node] no user_facts provided, skipping Z3")
        return state

    question = state["question"]
    z3_result = run_z3_check(question, user_facts)

    # Z3 pass → boost confidence
    if z3_result and z3_result.get("verified"):
        confidence = min(state["confidence"] + 0.15, 0.98)
    else:
        confidence = state["confidence"]

    return {
        **state,
        "z3_result": z3_result,
        "confidence": confidence,
    }
```

---

## 8. Backend — `app/graph/nodes/generate.py`

```python
from app.graph.state import GraphState
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Bạn là trợ lý tư vấn học vụ của HCMUS. Nhiệm vụ của bạn là trả lời câu hỏi của sinh viên dựa trên các điều khoản quy chế được cung cấp.

Quy tắc bắt buộc:
1. CHỈ trả lời dựa trên các điều khoản được cung cấp trong context. Không tự bịa thêm.
2. Mỗi thông tin quan trọng PHẢI có trích dẫn điều khoản cụ thể dạng [Điều X, Khoản Y].
3. Nếu context không đủ thông tin → nói rõ "Tôi không tìm thấy điều khoản cụ thể về vấn đề này".
4. Câu trả lời ngắn gọn, rõ ràng, dùng tiếng Việt tự nhiên.
5. Nếu có kết quả xác minh Z3 → đề cập ở cuối câu trả lời.

Format câu trả lời:
- Đoạn trả lời chính (2-4 câu)
- Điều khoản áp dụng: [liệt kê]
- Lưu ý (nếu có)
"""


def generate_node(state: GraphState) -> GraphState:
    """
    Node 3: Gọi LLM với context từ RAG + kết quả Z3 để sinh câu trả lời cuối.
    """
    question = state["question"]
    chunks = state["retrieved_chunks"]
    z3_result = state.get("z3_result")

    # Build context từ retrieved chunks
    context_parts = []
    for i, chunk in enumerate(chunks):
        meta = chunk.get("metadata", {})
        dieu_khoan = meta.get("dieu_khoan", f"Đoạn {i+1}")
        context_parts.append(f"[{dieu_khoan}]: {chunk.get('document', '')}")

    context = "\n\n".join(context_parts)

    # Thêm Z3 result nếu có
    z3_note = ""
    if z3_result:
        status = "✓ ĐÃ XÁC MINH" if z3_result.get("verified") else "✗ KHÔNG ĐỦ ĐIỀU KIỆN"
        z3_note = f"\n\nKết quả xác minh logic ({status}): {z3_result.get('explanation', '')}"

    user_prompt = f"""Câu hỏi của sinh viên: {question}

Các điều khoản liên quan từ quy chế:
{context}
{z3_note}

Hãy trả lời câu hỏi dựa trên các điều khoản trên."""

    # Gọi LLM theo provider
    answer = _call_llm(user_prompt)

    return {
        **state,
        "answer": answer,
    }


def _call_llm(user_prompt: str) -> str:
    """Gọi LLM theo provider được config"""
    provider = settings.llm_provider

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
            temperature=0.1,  # Low temp để consistent, ít hallucinate
        )
        return response.choices[0].message.content

    elif provider == "google":
        import google.generativeai as genai
        genai.configure(api_key=settings.google_api_key)
        model = genai.GenerativeModel(
            model_name=settings.google_model,
            system_instruction=SYSTEM_PROMPT,
        )
        response = model.generate_content(user_prompt)
        return response.text

    elif provider == "anthropic":
        import anthropic
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        response = client.messages.create(
            model=settings.anthropic_model,
            max_tokens=800,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return response.content[0].text

    else:
        return f"[LLM provider '{provider}' không được hỗ trợ. Check .env]"
```

---

## 9. Backend — `app/graph/graph.py`

```python
from langgraph.graph import StateGraph, END
from app.graph.state import GraphState
from app.graph.nodes.retrieve import retrieve_node
from app.graph.nodes.reason import reason_node
from app.graph.nodes.generate import generate_node
import logging

logger = logging.getLogger(__name__)


def should_run_z3(state: GraphState) -> str:
    """Conditional edge: chạy Z3 nếu là logical question và có user_facts"""
    if state.get("question_type") == "logical" and state.get("user_facts"):
        return "reason"
    return "generate"


def build_graph():
    """Build và compile LangGraph"""
    workflow = StateGraph(GraphState)

    # Thêm nodes
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("reason", reason_node)
    workflow.add_node("generate", generate_node)

    # Entry point
    workflow.set_entry_point("retrieve")

    # Edges
    workflow.add_conditional_edges(
        "retrieve",
        should_run_z3,
        {
            "reason": "reason",
            "generate": "generate",
        }
    )
    workflow.add_edge("reason", "generate")
    workflow.add_edge("generate", END)

    return workflow.compile()


# Singleton graph instance
graph = build_graph()
```

---

## 10. Backend — `app/rag/ingest.py`

```python
import fitz  # PyMuPDF
import chromadb
from chromadb.utils import embedding_functions
from app.core.config import settings
from pathlib import Path
import re
import logging

logger = logging.getLogger(__name__)


def get_chroma_collection():
    """Trả về ChromaDB collection, tạo mới nếu chưa có"""
    client = chromadb.PersistentClient(path=settings.chroma_persist_dir)

    if settings.embedding_provider == "openai":
        ef = embedding_functions.OpenAIEmbeddingFunction(
            api_key=settings.openai_api_key,
            model_name=settings.embedding_model,
        )
    else:
        ef = embedding_functions.GoogleGenerativeAiEmbeddingFunction(
            api_key=settings.google_api_key,
            model_name="models/text-embedding-004",
        )

    collection = client.get_or_create_collection(
        name=settings.chroma_collection,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},
    )
    return collection


def parse_pdf_to_chunks(pdf_path: str) -> list[dict]:
    """
    Parse PDF → list chunks với metadata điều khoản.
    Chunking theo điều khoản (detect "Điều X" pattern).
    """
    doc = fitz.open(pdf_path)
    full_text = ""
    for page in doc:
        full_text += page.get_text()
    doc.close()

    # Split theo pattern "Điều X" hoặc "Khoản X"
    # Regex tìm vị trí của các điều khoản
    pattern = r'(Điều\s+\d+[\.\s])'
    parts = re.split(pattern, full_text)

    chunks = []
    current_dieu = "Mở đầu"

    for i, part in enumerate(parts):
        # Nếu là header điều khoản
        if re.match(pattern, part):
            current_dieu = part.strip().rstrip('.')
            continue

        # Nếu là content
        text = part.strip()
        if len(text) < 50:  # Bỏ qua đoạn quá ngắn
            continue

        # Chia thêm theo khoản nếu chunk quá dài
        if len(text) > 1000:
            khoan_parts = re.split(r'(\d+\.\s)', text)
            for j, khoan_text in enumerate(khoan_parts):
                if len(khoan_text.strip()) > 50:
                    chunks.append({
                        "text": khoan_text.strip(),
                        "dieu_khoan": f"{current_dieu}, Khoản {j//2 + 1}",
                        "nguon": Path(pdf_path).stem,
                    })
        else:
            chunks.append({
                "text": text,
                "dieu_khoan": current_dieu,
                "nguon": Path(pdf_path).stem,
            })

    logger.info(f"Parsed {len(chunks)} chunks từ {pdf_path}")
    return chunks


def ingest_pdf(pdf_path: str) -> int:
    """
    Ingest 1 file PDF vào ChromaDB.
    Trả về số chunks đã ingest.
    """
    chunks = parse_pdf_to_chunks(pdf_path)
    collection = get_chroma_collection()

    # Batch upsert để tránh timeout
    batch_size = 50
    total = 0

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        collection.upsert(
            ids=[f"chunk_{i+j}" for j in range(len(batch))],
            documents=[c["text"] for c in batch],
            metadatas=[{
                "dieu_khoan": c["dieu_khoan"],
                "nguon": c["nguon"],
            } for c in batch],
        )
        total += len(batch)
        logger.info(f"Ingested batch {i//batch_size + 1}: {total}/{len(chunks)} chunks")

    return total
```

---

## 11. Backend — `app/rag/retriever.py`

```python
from app.rag.ingest import get_chroma_collection
import logging

logger = logging.getLogger(__name__)


def search_chunks(query: str, n_results: int = 3) -> list[dict]:
    """
    Tìm kiếm chunks liên quan nhất với query trong ChromaDB.
    Trả về list dict với keys: id, document, metadata, distance
    """
    try:
        collection = get_chroma_collection()
        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )

        chunks = []
        for i in range(len(results["ids"][0])):
            chunks.append({
                "id": results["ids"][0][i],
                "document": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i],
            })

        logger.info(f"Found {len(chunks)} chunks for query: {query[:50]}...")
        return chunks

    except Exception as e:
        logger.error(f"ChromaDB search error: {e}")
        return []
```

---

## 12. Backend — `app/z3_engine/rules.py`

```python
from z3 import *
import logging

logger = logging.getLogger(__name__)

# ============================================================
# Z3 Rules — Phase 1: 3 rule cứng để demo
# Phase 2 sẽ tự động extract rule từ LLM
# ============================================================

def check_graduation_condition(user_facts: dict) -> dict:
    """
    Rule: Sinh viên đủ điều kiện tốt nghiệp khi:
    - Tích lũy đủ số tín chỉ theo ngành (VD: ≥ 120)
    - Điểm TB tích lũy ≥ 2.0
    - Không còn môn nợ
    """
    tin_chi = Int('tin_chi')
    diem_tb = Real('diem_tb')
    no_mon = Bool('no_mon')

    solver = Solver()

    # Facts từ sinh viên
    solver.add(tin_chi == user_facts.get("tin_chi_tich_luy", 0))
    solver.add(diem_tb == user_facts.get("diem_tb", 0.0))
    solver.add(no_mon == user_facts.get("no_mon", True))

    # Rule tốt nghiệp (Điều 30, Khoản 1 — giả định)
    du_dieu_kien = And(
        tin_chi >= 120,
        diem_tb >= 2.0,
        no_mon == False
    )
    solver.add(du_dieu_kien)

    if solver.check() == sat:
        return {
            "verified": True,
            "rule_applied": "Điều 30, Khoản 1 — Điều kiện tốt nghiệp",
            "explanation": f"Sinh viên ĐỦ điều kiện tốt nghiệp: {user_facts.get('tin_chi_tich_luy')} TC ≥ 120, ĐTB {user_facts.get('diem_tb')} ≥ 2.0, không nợ môn.",
        }
    else:
        # Tìm lý do cụ thể
        reasons = []
        if user_facts.get("tin_chi_tich_luy", 0) < 120:
            reasons.append(f"Thiếu {120 - user_facts.get('tin_chi_tich_luy', 0)} tín chỉ")
        if user_facts.get("diem_tb", 0) < 2.0:
            reasons.append(f"ĐTB {user_facts.get('diem_tb')} < 2.0")
        if user_facts.get("no_mon", False):
            reasons.append("Còn nợ môn học")

        return {
            "verified": False,
            "rule_applied": "Điều 30, Khoản 1 — Điều kiện tốt nghiệp",
            "explanation": f"Sinh viên CHƯA đủ điều kiện: {'; '.join(reasons)}.",
        }


def check_canh_cao_hoc_vu(user_facts: dict) -> dict:
    """
    Rule: Bị cảnh cáo học vụ khi ĐTB học kỳ < 1.0 hoặc ĐTB tích lũy < 1.2
    """
    diem_tb_hk = Real('diem_tb_hk')
    diem_tb_tl = Real('diem_tb_tl')
    solver = Solver()

    solver.add(diem_tb_hk == user_facts.get("diem_tb_hoc_ky", 2.0))
    solver.add(diem_tb_tl == user_facts.get("diem_tb_tich_luy", 2.0))

    bi_canh_cao = Or(diem_tb_hk < 1.0, diem_tb_tl < 1.2)
    solver.add(bi_canh_cao)

    if solver.check() == sat:
        return {
            "verified": True,
            "rule_applied": "Điều 22 — Cảnh cáo học vụ",
            "explanation": "Sinh viên thuộc diện cảnh cáo học vụ theo quy chế.",
        }
    return {
        "verified": False,
        "rule_applied": "Điều 22 — Cảnh cáo học vụ",
        "explanation": "Sinh viên không thuộc diện cảnh cáo học vụ.",
    }


def check_hoc_bong_khuyen_khich(user_facts: dict) -> dict:
    """
    Rule: Đủ điều kiện học bổng khuyến khích khi ĐTB ≥ 3.2 và không nợ môn
    """
    diem_tb = Real('diem_tb')
    no_mon = Bool('no_mon')
    solver = Solver()

    solver.add(diem_tb == user_facts.get("diem_tb", 0.0))
    solver.add(no_mon == user_facts.get("no_mon", True))

    du_dieu_kien = And(diem_tb >= 3.2, no_mon == False)
    solver.add(du_dieu_kien)

    if solver.check() == sat:
        return {
            "verified": True,
            "rule_applied": "Điều 25 — Học bổng khuyến khích học tập",
            "explanation": f"Sinh viên ĐỦ điều kiện học bổng: ĐTB {user_facts.get('diem_tb')} ≥ 3.2, không nợ môn.",
        }
    return {
        "verified": False,
        "rule_applied": "Điều 25 — Học bổng khuyến khích học tập",
        "explanation": "Sinh viên chưa đủ điều kiện học bổng.",
    }


# Router: chọn rule phù hợp dựa trên câu hỏi
RULE_KEYWORDS = {
    "graduation": ["tốt nghiệp", "ra trường", "hoàn thành chương trình"],
    "canh_cao": ["cảnh cáo", "học vụ", "bị đuổi", "thôi học"],
    "hoc_bong": ["học bổng", "khuyến khích", "hỗ trợ tài chính"],
}


def run_z3_check(question: str, user_facts: dict) -> dict | None:
    """
    Chọn và chạy Z3 rule phù hợp dựa trên câu hỏi.
    Trả về None nếu không có rule phù hợp.
    """
    question_lower = question.lower()

    if any(kw in question_lower for kw in RULE_KEYWORDS["graduation"]):
        return check_graduation_condition(user_facts)

    if any(kw in question_lower for kw in RULE_KEYWORDS["canh_cao"]):
        return check_canh_cao_hoc_vu(user_facts)

    if any(kw in question_lower for kw in RULE_KEYWORDS["hoc_bong"]):
        return check_hoc_bong_khuyen_khich(user_facts)

    logger.info("No matching Z3 rule found for question")
    return None
```

---

## 13. Backend — `app/api/routes.py`

```python
from fastapi import APIRouter, HTTPException
from app.core.schema import AskRequest, AskResponse, Citation, Z3Result, QuestionType
from app.graph.graph import graph
from app.graph.state import initial_state
import time
import logging

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

        # Chạy LangGraph
        result = graph.invoke(state)

        # Build response
        citations = [Citation(**c) for c in result.get("citations", [])]

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

    except Exception as e:
        logger.error(f"Error processing question: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

---

## 14. Backend — `app/main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.core.config import settings
import logging

logging.basicConfig(level=settings.log_level)

app = FastAPI(
    title="QA Quy chế HCMUS",
    description="Hệ thống hỏi đáp quy chế đại học với LangGraph + RAG + Z3",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.app_port, reload=True)
```

---

## 15. Backend — `scripts/ingest_pdf.py`

```python
"""
Chạy script này để ingest PDF vào ChromaDB.
Usage: python scripts/ingest_pdf.py --pdf data/quy_che.pdf
"""
import sys
import argparse
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.rag.ingest import ingest_pdf
from dotenv import load_dotenv

load_dotenv()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", required=True, help="Path đến file PDF quy chế")
    args = parser.parse_args()

    pdf_path = args.pdf
    if not Path(pdf_path).exists():
        print(f"❌ File không tồn tại: {pdf_path}")
        sys.exit(1)

    print(f"📄 Ingesting: {pdf_path}")
    total = ingest_pdf(pdf_path)
    print(f"✅ Đã ingest {total} chunks vào ChromaDB")


if __name__ == "__main__":
    main()
```

---

## 16. Frontend — `src/api/client.js`

```js
const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

export async function askQuestion(question, userFacts = null) {
  const res = await fetch(`${BASE_URL}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, user_facts: userFacts }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }

  return res.json(); // AskResponse schema
}

export async function healthCheck() {
  const res = await fetch(`${BASE_URL}/health`);
  return res.json();
}
```

---

## 17. Frontend — `src/hooks/useChat.js`

```js
import { useState, useCallback } from "react";
import { askQuestion } from "../api/client";

export function useChat() {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const sendMessage = useCallback(async (question, userFacts = null) => {
    setError(null);
    setLoading(true);

    // Optimistic: thêm message user ngay
    const userMsg = { id: Date.now(), role: "user", content: question };
    setMessages((prev) => [...prev, userMsg]);

    try {
      const response = await askQuestion(question, userFacts);
      const assistantMsg = {
        id: Date.now() + 1,
        role: "assistant",
        content: response.answer,
        citations: response.citations || [],
        confidence: response.confidence,
        z3Result: response.z3_result,
        questionType: response.question_type,
        processingTimeMs: response.processing_time_ms,
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const clearChat = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  return { messages, loading, error, sendMessage, clearChat };
}
```

---

## 18. Frontend — `src/components/CitationTag.jsx`

```jsx
export function CitationTag({ citation }) {
  return (
    <span
      title={citation.noi_dung}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 4,
        background: "#EEEDFE",
        color: "#3C3489",
        fontSize: 11,
        fontWeight: 500,
        padding: "2px 8px",
        borderRadius: 100,
        cursor: "help",
        border: "0.5px solid #AFA9EC",
      }}
    >
      📎 {citation.dieu_khoan}
    </span>
  );
}
```

---

## 19. Frontend — `src/components/ConfidenceBadge.jsx`

```jsx
export function ConfidenceBadge({ confidence, z3Result }) {
  const pct = Math.round(confidence * 100);
  const color = pct >= 80 ? "#1D9E75" : pct >= 60 ? "#BA7517" : "#993C1D";
  const bg   = pct >= 80 ? "#E1F5EE" : pct >= 60 ? "#FAEEDA" : "#FAECE7";

  return (
    <div style={{ display: "flex", gap: 8, alignItems: "center", marginTop: 8 }}>
      <span style={{ background: bg, color, fontSize: 11, fontWeight: 500, padding: "2px 10px", borderRadius: 100 }}>
        {pct}% tin cậy
      </span>
      {z3Result && (
        <span style={{
          background: z3Result.verified ? "#E1F5EE" : "#FAECE7",
          color: z3Result.verified ? "#085041" : "#712B13",
          fontSize: 11, fontWeight: 500, padding: "2px 10px", borderRadius: 100,
        }}>
          {z3Result.verified ? "✓ Z3 xác minh" : "✗ Z3: chưa đủ điều kiện"}
        </span>
      )}
    </div>
  );
}
```

---

## 20. Frontend — `src/components/MessageBubble.jsx`

```jsx
import { CitationTag } from "./CitationTag";
import { ConfidenceBadge } from "./ConfidenceBadge";

export function MessageBubble({ message }) {
  const isUser = message.role === "user";

  if (isUser) {
    return (
      <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: 12 }}>
        <div style={{
          background: "#534AB7", color: "#fff",
          borderRadius: "16px 16px 4px 16px",
          padding: "10px 14px", maxWidth: "75%", fontSize: 14,
        }}>
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", justifyContent: "flex-start", marginBottom: 12 }}>
      <div style={{
        background: "#F8F8F8", border: "0.5px solid #E0E0E0",
        borderRadius: "16px 16px 16px 4px",
        padding: "12px 14px", maxWidth: "80%", fontSize: 14, lineHeight: 1.6,
      }}>
        <div style={{ whiteSpace: "pre-wrap" }}>{message.content}</div>

        {message.citations?.length > 0 && (
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 10 }}>
            {message.citations.map((c, i) => (
              <CitationTag key={i} citation={c} />
            ))}
          </div>
        )}

        {message.confidence !== undefined && (
          <ConfidenceBadge confidence={message.confidence} z3Result={message.z3Result} />
        )}

        {message.processingTimeMs && (
          <div style={{ fontSize: 10, color: "#aaa", marginTop: 8 }}>
            {message.processingTimeMs}ms
          </div>
        )}
      </div>
    </div>
  );
}
```

---

## 21. Frontend — `src/components/ChatWindow.jsx`

```jsx
import { useState, useRef, useEffect } from "react";
import { useChat } from "../hooks/useChat";
import { MessageBubble } from "./MessageBubble";

// 5 câu demo sẵn cho hackathon
const DEMO_QUESTIONS = [
  "Điều kiện để được xét tốt nghiệp là gì?",
  "Sinh viên bị cảnh cáo học vụ khi nào?",
  "Điểm trung bình tích lũy tối thiểu để không bị đình chỉ học?",
  "Quy trình đăng ký bảo lưu kết quả học tập như thế nào?",
  "Học bổng khuyến khích cần điều kiện gì?",
];

export function ChatWindow() {
  const { messages, loading, error, sendMessage, clearChat } = useChat();
  const [input, setInput] = useState("");
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSend = () => {
    if (!input.trim() || loading) return;
    sendMessage(input.trim());
    setInput("");
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh", maxWidth: 760, margin: "0 auto", fontFamily: "system-ui" }}>
      {/* Header */}
      <div style={{ padding: "16px 20px", borderBottom: "0.5px solid #E0E0E0", display: "flex", alignItems: "center", gap: 12 }}>
        <div style={{ width: 36, height: 36, borderRadius: "50%", background: "#534AB7", display: "flex", alignItems: "center", justifyContent: "center", color: "#fff", fontWeight: 600, fontSize: 14 }}>Q</div>
        <div>
          <div style={{ fontWeight: 600, fontSize: 15 }}>QA Quy chế HCMUS</div>
          <div style={{ fontSize: 12, color: "#888" }}>RAG + Z3 Solver · Câu trả lời có trích dẫn điều khoản</div>
        </div>
        <button onClick={clearChat} style={{ marginLeft: "auto", fontSize: 12, color: "#888", border: "0.5px solid #ddd", borderRadius: 8, padding: "4px 10px", cursor: "pointer", background: "none" }}>
          Xóa chat
        </button>
      </div>

      {/* Messages */}
      <div style={{ flex: 1, overflowY: "auto", padding: "16px 20px" }}>
        {messages.length === 0 && (
          <div style={{ textAlign: "center", color: "#888", marginTop: 40 }}>
            <div style={{ fontSize: 32, marginBottom: 12 }}>📋</div>
            <div style={{ fontWeight: 500, marginBottom: 16 }}>Hỏi bất kỳ điều gì về quy chế HCMUS</div>
            <div style={{ display: "flex", flexDirection: "column", gap: 8, maxWidth: 480, margin: "0 auto" }}>
              {DEMO_QUESTIONS.map((q, i) => (
                <button key={i} onClick={() => sendMessage(q)} style={{
                  textAlign: "left", padding: "10px 14px", borderRadius: 12,
                  border: "0.5px solid #ddd", cursor: "pointer", background: "#fafafa",
                  fontSize: 13, color: "#333", transition: "background .15s",
                }}>
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}

        {loading && (
          <div style={{ display: "flex", justifyContent: "flex-start", marginBottom: 12 }}>
            <div style={{ background: "#F0F0F0", borderRadius: 16, padding: "10px 16px", fontSize: 13, color: "#888" }}>
              ⏳ Đang tìm kiếm điều khoản...
            </div>
          </div>
        )}

        {error && (
          <div style={{ background: "#FAECE7", color: "#712B13", padding: "10px 14px", borderRadius: 12, fontSize: 13, marginBottom: 12 }}>
            ❌ {error}
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div style={{ padding: "12px 20px", borderTop: "0.5px solid #E0E0E0", display: "flex", gap: 10 }}>
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Nhập câu hỏi về quy chế học vụ..."
          rows={2}
          style={{
            flex: 1, resize: "none", border: "0.5px solid #ddd", borderRadius: 12,
            padding: "10px 14px", fontSize: 14, fontFamily: "inherit",
            outline: "none", lineHeight: 1.5,
          }}
        />
        <button
          onClick={handleSend}
          disabled={loading || !input.trim()}
          style={{
            padding: "0 20px", background: "#534AB7", color: "#fff",
            border: "none", borderRadius: 12, cursor: "pointer",
            fontSize: 14, fontWeight: 500, opacity: (loading || !input.trim()) ? 0.5 : 1,
          }}
        >
          Gửi
        </button>
      </div>
    </div>
  );
}
```

---

## 22. Frontend — `src/App.jsx`

```jsx
import { ChatWindow } from "./components/ChatWindow";

export default function App() {
  return <ChatWindow />;
}
```

---

## 23. `docker-compose.yml`

```yaml
version: "3.9"

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./backend/data:/app/data
      - ./backend/chroma_db:/app/chroma_db
    env_file:
      - ./backend/.env
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    image: node:20-alpine
    working_dir: /app
    volumes:
      - ./frontend:/app
    ports:
      - "5173:5173"
    command: sh -c "npm install && npm run dev -- --host"
    environment:
      - VITE_API_URL=http://localhost:8000/api/v1
```

---

## Lệnh chạy nhanh

```bash
# 1. Clone và setup
git clone <repo>
cd project-root

# 2. Backend setup
cd backend
cp .env.example .env
# → Điền API key vào .env
pip install -r requirements.txt

# 3. Ingest PDF quy chế (đặt file vào backend/data/)
python scripts/ingest_pdf.py --pdf data/quy_che_hcmus_2024.pdf

# 4. Chạy backend
uvicorn app.main:app --reload --port 8000

# 5. Frontend (terminal khác)
cd ../frontend
npm install
npm run dev

# 6. Test nhanh API
curl -X POST http://localhost:8000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Điều kiện tốt nghiệp là gì?"}'
```

---

## Checklist Phase 1 Done ✅

- [ ] Thư mục đúng cấu trúc, repo push lên GitHub
- [ ] `GET /health` trả về 200
- [ ] `POST /ask` với câu hỏi đơn giản không crash
- [ ] ChromaDB có ít nhất 20 chunks từ PDF quy chế
- [ ] Frontend load được, gõ câu hỏi gửi được request
- [ ] Không có hardcode API key trong code

---

*Sang Phase 2: Tối ưu LangGraph nodes, bổ sung thêm Z3 rules, cải thiện chunking strategy.*
