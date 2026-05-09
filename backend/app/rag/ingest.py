import base64
import hashlib
import logging
import os
import re
from functools import lru_cache
from pathlib import Path

import chromadb
import fitz
import numpy as np
from chromadb.config import Settings as ChromaSettings
from chromadb.utils import embedding_functions

from app.core.config import settings

logger = logging.getLogger(__name__)
logging.getLogger("chromadb.telemetry.product.posthog").setLevel(logging.CRITICAL)

# PaddlePaddle 3.3+ CPU regression workaround for oneDNN/PIR inference.
os.environ.setdefault("FLAGS_enable_pir_api", "0")
os.environ.setdefault("PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT", "0")


class HashEmbeddingFunction:
    """Small deterministic local embedding fallback for development without API keys."""

    def __init__(self, dimensions: int = 384):
        self.dimensions = dimensions

    def __call__(self, input):
        return [self._embed_text(text) for text in input]

    def _embed_text(self, text: str) -> list[float]:
        vector = np.zeros(self.dimensions, dtype=np.float32)
        tokens = re.findall(r"\w+", text.lower(), flags=re.UNICODE)
        for token in tokens:
            digest = hashlib.md5(token.encode("utf-8")).digest()
            idx = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[idx] += sign
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        return vector.tolist()


@lru_cache(maxsize=1)
def _get_paddle_ocr():
    """Lazy-load PaddleOCR so the backend still imports without OCR deps installed."""
    try:
        from paddleocr import PaddleOCR
    except Exception as exc:  # pragma: no cover - import guard
        logger.warning("PaddleOCR is not available: %s", exc)
        return None

    init_attempts = [
        {
            "lang": "la",
            "ocr_version": "PP-OCRv5",
            "device": "cpu",
            "use_doc_orientation_classify": False,
            "use_doc_unwarping": False,
            "use_textline_orientation": False,
        },
        {
            "lang": "en",
            "ocr_version": "PP-OCRv5",
            "device": "cpu",
            "use_doc_orientation_classify": False,
            "use_doc_unwarping": False,
            "use_textline_orientation": False,
        },
        {"lang": "la", "device": "cpu"},
        {"lang": "en", "device": "cpu"},
    ]
    last_error = None
    for kwargs in init_attempts:
        try:
            return PaddleOCR(**kwargs)
        except TypeError as exc:
            last_error = exc
        except Exception as exc:
            last_error = exc
    logger.warning("Failed to initialize PaddleOCR: %s", last_error)
    return None


def _pixmap_to_array(pix):
    """Convert a PyMuPDF pixmap to a numpy RGB array."""
    img = np.frombuffer(pix.samples, dtype=np.uint8)
    img = img.reshape(pix.height, pix.width, pix.n)
    if pix.n > 3:
        img = img[:, :, :3]
    return img


def _ocr_page_text_paddle(page, page_no: int) -> str:
    """OCR a single PDF page image with PaddleOCR."""
    ocr = _get_paddle_ocr()
    if ocr is None:
        return ""

    try:
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
        image = _pixmap_to_array(pix)

        if hasattr(ocr, "predict"):
            result = ocr.predict(image)
        elif hasattr(ocr, "ocr"):
            try:
                result = ocr.ocr(image)
            except TypeError:
                result = ocr.ocr(image, cls=True)
        else:
            logger.warning("Unsupported PaddleOCR interface on page %s", page_no)
            return ""

        lines = []
        pages = result or []
        is_legacy_nested_result = (
            pages
            and isinstance(pages[0], list)
            and len(pages) == 1
            and pages[0]
            and isinstance(pages[0][0], list)
        )
        if is_legacy_nested_result:
            lines = pages[0]
        else:
            lines = pages

        texts = []
        for line in lines:
            text = None
            if hasattr(line, "get"):
                rec_texts = line.get("rec_texts")
                if isinstance(rec_texts, list):
                    texts.extend(str(item) for item in rec_texts if item)
                    continue
                text = line.get("text") or line.get("rec_text")
            elif isinstance(line, list) and len(line) >= 2:
                rec = line[1]
                if isinstance(rec, (list, tuple)) and rec:
                    text = rec[0]
                elif isinstance(rec, dict):
                    text = rec.get("text")
            elif hasattr(line, "text"):
                text = line.text

            if text:
                texts.append(str(text))

        ocr_text = "\n".join(texts).strip()
        if ocr_text:
            logger.info("OCR extracted page %s with %s chars", page_no, len(ocr_text))
        return ocr_text
    except Exception as exc:
        logger.warning("OCR failed on page %s: %s", page_no, exc)
        return ""


def _has_openai_key() -> bool:
    return bool(settings.openai_api_key and settings.openai_api_key != "sk-...")


def _page_to_png_data_url(page) -> str:
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
    png_bytes = pix.tobytes("png")
    encoded = base64.b64encode(png_bytes).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _ocr_page_text_openai(page, page_no: int) -> str:
    """Use OpenAI vision as a higher-quality OCR fallback for difficult pages."""
    if not _has_openai_key():
        logger.info("OpenAI OCR skipped on page %s: OPENAI_API_KEY is not configured", page_no)
        return ""

    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key)
        response = client.chat.completions.create(
            model=settings.ocr_openai_model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Extract all readable text from this PDF page. "
                                "Preserve Vietnamese accents, line breaks, article numbers, clauses, and table text. "
                                "Return plain text only, with no markdown or explanation."
                            ),
                        },
                        {"type": "image_url", "image_url": {"url": _page_to_png_data_url(page)}},
                    ],
                }
            ],
            max_tokens=3000,
            temperature=0,
        )
        text = (response.choices[0].message.content or "").strip()
        if text:
            logger.info("OpenAI OCR extracted page %s with %s chars", page_no, len(text))
        return text
    except Exception as exc:
        error_text = str(exc)
        if "invalid_api_key" in error_text or "401" in error_text:
            raise RuntimeError("OpenAI OCR authentication failed. Check OPENAI_API_KEY in backend/.env.") from exc
        logger.warning("OpenAI OCR failed on page %s: %s", page_no, exc)
        return ""


def _ocr_page_text(page, page_no: int) -> str:
    provider = settings.ocr_provider
    if provider == "off":
        return ""
    if provider == "paddle":
        return _ocr_page_text_paddle(page, page_no)
    if provider == "openai":
        return _ocr_page_text_openai(page, page_no)

    paddle_text = _ocr_page_text_paddle(page, page_no)
    if len(paddle_text.strip()) >= settings.ocr_min_chars:
        return paddle_text

    if not _has_openai_key():
        return paddle_text

    openai_text = _ocr_page_text_openai(page, page_no)
    return openai_text or paddle_text


def _has_embedding_key() -> bool:
    if settings.embedding_provider == "openai":
        return bool(settings.openai_api_key and settings.openai_api_key != "sk-...")
    if settings.embedding_provider == "google":
        return bool(settings.google_api_key and settings.google_api_key != "AIza...")
    if settings.embedding_provider == "hash":
        return True
    return True


def get_chroma_collection():
    """Return a ChromaDB collection, creating it if needed."""
    if not _has_embedding_key():
        key_name = "OPENAI_API_KEY" if settings.embedding_provider == "openai" else "GOOGLE_API_KEY"
        raise ValueError(f"{key_name} is required when EMBEDDING_PROVIDER={settings.embedding_provider}")

    client = chromadb.PersistentClient(
        path=settings.chroma_persist_dir,
        settings=ChromaSettings(anonymized_telemetry=False),
    )

    if settings.embedding_provider == "openai":
        embedding_function = embedding_functions.OpenAIEmbeddingFunction(
            api_key=settings.openai_api_key,
            model_name=settings.embedding_model,
        )
    elif settings.embedding_provider == "google":
        embedding_function = embedding_functions.GoogleGenerativeAiEmbeddingFunction(
            api_key=settings.google_api_key,
            model_name="models/text-embedding-004",
        )
    elif settings.embedding_provider == "hash":
        embedding_function = HashEmbeddingFunction()
    else:
        embedding_function = embedding_functions.DefaultEmbeddingFunction()

    return client.get_or_create_collection(
        name=settings.chroma_collection,
        embedding_function=embedding_function,
        metadata={"hnsw:space": "cosine"},
    )


def extract_text_with_pages(pdf_path: str) -> list[dict]:
    """Extract text per page; use configured OCR fallback for image-only pages."""
    doc = fitz.open(pdf_path)
    pages = []
    for i, page in enumerate(doc):
        text = page.get_text("text").strip()
        if len(text) < settings.ocr_min_chars:
            logger.info("Page %s has %s text chars; running OCR", i + 1, len(text))
            ocr_text = _ocr_page_text(page, i + 1)
            if ocr_text:
                text = ocr_text
            logger.info("Page %s extracted %s chars after OCR", i + 1, len(text))
        else:
            logger.info("Page %s extracted %s chars from PDF text", i + 1, len(text))
        pages.append({"page": i + 1, "text": text})
    doc.close()
    return pages


def detect_article_boundaries(text: str) -> list[dict]:
    """
    Detect regulation boundaries across common formats:
    "Điều 1.", "Điều 1:", "ĐIỀU 1", "Chương I", "Mục 1".
    """
    patterns = [
        (r"(?:^|\n)((?:CHƯƠNG|Chương)\s+[IVXLCDM\d]+[.:]?\s*.*?)(?=\n)", "chapter"),
        (r"(?:^|\n)((?:Điều|ĐIỀU)\s+\d+[.:]?\s*.*?)(?=\n)", "article"),
        (r"(?:^|\n)((?:Mục|MỤC)\s+\d+[.:]?\s*.*?)(?=\n)", "section"),
    ]

    boundaries = []
    for pattern, boundary_type in patterns:
        for match in re.finditer(pattern, text, re.MULTILINE):
            header = match.group(1).strip()
            if header:
                boundaries.append(
                    {
                        "pos": match.start(),
                        "header": header,
                        "type": boundary_type,
                    }
                )

    boundaries.sort(key=lambda item: item["pos"])
    return boundaries


def sliding_window_chunks(text: str, chunk_size: int = 500, overlap: int = 100) -> list[str]:
    """Create overlapping word windows for unstructured PDF text."""
    words = text.split()
    chunks = []
    step = max(chunk_size - overlap, 1)
    for i in range(0, len(words), step):
        chunk_words = words[i : i + chunk_size]
        if chunk_words:
            chunks.append(" ".join(chunk_words))
    return chunks


def _page_for_offset(page_offsets: list[tuple[int, int, int]], offset: int) -> int | None:
    for start, end, page_no in page_offsets:
        if start <= offset <= end:
            return page_no
    return page_offsets[-1][2] if page_offsets else None


def _chunk_record(text: str, dieu_khoan: str, chuong: str, nguon: str, page: int | None) -> dict:
    chunk_hash = hashlib.md5(text.encode("utf-8")).hexdigest()[:8]
    return {
        "text": text,
        "dieu_khoan": dieu_khoan,
        "chuong": chuong,
        "trang": page,
        "nguon": nguon,
        "chunk_hash": chunk_hash,
    }


def parse_pdf_smart(pdf_path: str) -> list[dict]:
    """
    Smart chunking:
    - Prefer structured article/chapter boundaries.
    - Split long articles by clauses.
    - Fall back to sliding windows when structure is not detected.
    """
    pages = extract_text_with_pages(pdf_path)
    page_offsets = []
    full_text_parts = []
    offset = 0
    for page in pages:
        text = page["text"]
        start = offset
        full_text_parts.append(text)
        offset += len(text) + 1
        page_offsets.append((start, offset, page["page"]))

    full_text = "\n".join(full_text_parts)
    nguon = Path(pdf_path).stem
    boundaries = detect_article_boundaries(full_text)

    chunks = []
    if len(boundaries) >= 3:
        current_chapter = "Chưa xác định"
        current_article = "Mở đầu"

        for i, boundary in enumerate(boundaries):
            start = boundary["pos"]
            end = boundaries[i + 1]["pos"] if i + 1 < len(boundaries) else len(full_text)
            segment_text = full_text[start:end].strip()
            page_no = _page_for_offset(page_offsets, start)

            if boundary["type"] == "chapter":
                current_chapter = boundary["header"]
                continue
            if boundary["type"] == "article":
                current_article = boundary["header"]

            if len(segment_text) < 50:
                continue

            if len(segment_text) > 800:
                sub_parts = re.split(r"\n\s*(\d+\.\s)", segment_text)
                khoan_idx = 0
                for j in range(0, len(sub_parts), 2):
                    part = sub_parts[j].strip()
                    if j + 1 < len(sub_parts):
                        part = sub_parts[j + 1] + part
                    if len(part) <= 40:
                        continue
                    khoan_idx += 1
                    label = f"{current_article}, Khoản {khoan_idx}"
                    chunk_text = f"{label}: {part}"
                    chunks.append(_chunk_record(chunk_text, label, current_chapter, nguon, page_no))
            else:
                chunks.append(_chunk_record(segment_text, current_article, current_chapter, nguon, page_no))
    else:
        logger.warning("Could not detect article structure, using sliding window chunking")
        for i, text in enumerate(sliding_window_chunks(full_text, chunk_size=400, overlap=80)):
            page_no = _page_for_offset(page_offsets, full_text.find(text[:50])) if text else None
            chunks.append(_chunk_record(text, f"Đoạn {i + 1}", "Không xác định", nguon, page_no))

    logger.info("Smart parse: %s chunks from %s", len(chunks), pdf_path)
    return chunks


def parse_pdf_to_chunks(pdf_path: str) -> list[dict]:
    """Backward-compatible alias used by Phase 1 callers/tests."""
    return parse_pdf_smart(pdf_path)


def ingest_pdf(pdf_path: str, reset: bool = False) -> int:
    """Ingest a PDF into ChromaDB. Set reset=True to recreate the collection first."""
    chunks = parse_pdf_smart(pdf_path)

    if reset:
        client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        try:
            client.delete_collection(settings.chroma_collection)
        except Exception as exc:
            logger.info("Collection reset skipped: %s", exc)
        logger.info("Collection reset complete")

    collection = get_chroma_collection()

    batch_size = 50
    total = 0
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        collection.upsert(
            ids=[f"{chunk['chunk_hash']}_{i + j}" for j, chunk in enumerate(batch)],
            documents=[chunk["text"] for chunk in batch],
            metadatas=[
                {
                    "dieu_khoan": chunk["dieu_khoan"],
                    "chuong": chunk["chuong"],
                    "trang": chunk["trang"] or 0,
                    "nguon": chunk["nguon"],
                }
                for chunk in batch
            ],
        )
        total += len(batch)

    logger.info("Ingest complete: %s chunks", total)
    return total
