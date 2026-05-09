import logging
import re
from pathlib import Path

import chromadb
import fitz
from chromadb.utils import embedding_functions

from app.core.config import settings

logger = logging.getLogger(__name__)


def get_chroma_collection():
    """Return a ChromaDB collection, creating it if needed."""
    if settings.embedding_provider == "openai":
        if not settings.openai_api_key or settings.openai_api_key == "sk-...":
            raise ValueError("OPENAI_API_KEY is required when EMBEDDING_PROVIDER=openai")
    else:
        if not settings.google_api_key or settings.google_api_key == "AIza...":
            raise ValueError("GOOGLE_API_KEY is required when EMBEDDING_PROVIDER=google")

    client = chromadb.PersistentClient(path=settings.chroma_persist_dir)

    if settings.embedding_provider == "openai":
        embedding_function = embedding_functions.OpenAIEmbeddingFunction(
            api_key=settings.openai_api_key,
            model_name=settings.embedding_model,
        )
    else:
        embedding_function = embedding_functions.GoogleGenerativeAiEmbeddingFunction(
            api_key=settings.google_api_key,
            model_name="models/text-embedding-004",
        )

    return client.get_or_create_collection(
        name=settings.chroma_collection,
        embedding_function=embedding_function,
        metadata={"hnsw:space": "cosine"},
    )


def parse_pdf_to_chunks(pdf_path: str) -> list[dict]:
    """
    Parse a PDF into chunks with article metadata.
    Chunking starts from "Điều X" boundaries, then splits long text by clauses.
    """
    doc = fitz.open(pdf_path)
    full_text = ""
    for page in doc:
        full_text += page.get_text()
    doc.close()

    pattern = r"(Điều\s+\d+[\.\s])"
    parts = re.split(pattern, full_text)

    chunks = []
    current_dieu = "Mở đầu"

    for part in parts:
        if re.match(pattern, part):
            current_dieu = part.strip().rstrip(".")
            continue

        text = part.strip()
        if len(text) < 50:
            continue

        if len(text) > 1000:
            khoan_parts = re.split(r"(\d+\.\s)", text)
            clause_no = 1
            for khoan_text in khoan_parts:
                clean_text = khoan_text.strip()
                if len(clean_text) <= 50:
                    continue
                chunks.append(
                    {
                        "text": clean_text,
                        "dieu_khoan": f"{current_dieu}, Khoản {clause_no}",
                        "nguon": Path(pdf_path).stem,
                    }
                )
                clause_no += 1
        else:
            chunks.append(
                {
                    "text": text,
                    "dieu_khoan": current_dieu,
                    "nguon": Path(pdf_path).stem,
                }
            )

    logger.info("Parsed %s chunks from %s", len(chunks), pdf_path)
    return chunks


def ingest_pdf(pdf_path: str) -> int:
    """Ingest one PDF into ChromaDB and return the number of chunks written."""
    chunks = parse_pdf_to_chunks(pdf_path)
    collection = get_chroma_collection()

    batch_size = 50
    total = 0

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        collection.upsert(
            ids=[f"{Path(pdf_path).stem}_chunk_{i + j}" for j in range(len(batch))],
            documents=[chunk["text"] for chunk in batch],
            metadatas=[
                {
                    "dieu_khoan": chunk["dieu_khoan"],
                    "nguon": chunk["nguon"],
                }
                for chunk in batch
            ],
        )
        total += len(batch)
        logger.info("Ingested batch %s: %s/%s chunks", i // batch_size + 1, total, len(chunks))

    return total
