from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class QuestionType(str, Enum):
    FACTUAL = "factual"
    PROCEDURAL = "procedural"
    LOGICAL = "logical"


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
        description="Thông tin sinh viên nếu câu hỏi cần suy luận cá nhân. VD: {'tin_chi_tich_luy': 115, 'diem_tb': 2.3}",
    )


class AskResponse(BaseModel):
    answer: str
    question_type: QuestionType
    citations: list[Citation]
    confidence: float = Field(..., ge=0.0, le=1.0)
    z3_result: Optional[Z3Result] = None
    processing_time_ms: int


class GraphStateModel(BaseModel):
    """State được truyền qua các node trong LangGraph."""

    question: str
    question_type: Optional[QuestionType] = None
    user_facts: Optional[dict] = None
    retrieved_chunks: list[dict] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)
    z3_result: Optional[Z3Result] = None
    answer: Optional[str] = None
    confidence: float = 0.0
    error: Optional[str] = None
