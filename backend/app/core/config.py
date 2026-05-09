from typing import Literal

from pydantic_settings import BaseSettings


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
    embedding_provider: Literal["openai", "google", "hash"] = "openai"
    embedding_model: str = "text-embedding-3-small"

    # OCR for image-only PDF pages during ingestion
    ocr_provider: Literal["auto", "paddle", "openai", "off"] = "auto"
    ocr_min_chars: int = 30
    ocr_openai_model: str = "gpt-4o-mini"

    # ChromaDB
    chroma_persist_dir: str = "./chroma_db"
    chroma_collection: str = "quy_che_hcmus"
    pdf_source_urls: str = (
        "QC_DT=https://hcmus.edu.vn/wp-content/uploads/2025/04/QD-1175_Quy-che-dao-tao-trinh-do-DH-2021.pdf"
    )

    # App
    app_port: int = 8000
    cors_origins: str = "http://localhost:5173"
    log_level: str = "INFO"

    # Opik tracing and online evaluation
    opik_enabled: bool = False
    opik_project_name: str = "saas-edtech-rag"
    opik_api_key: str = ""
    opik_base_url: str = ""
    opik_workspace: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
