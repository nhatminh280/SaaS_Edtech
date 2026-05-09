# QA Quy chế HCMUS

Phase 2 scaffold for a university-regulation QA system using FastAPI, LangGraph, RAG over ChromaDB, Z3 rule checks, and a Vite React chat UI.

## Structure

```txt
backend/
  app/
    api/          FastAPI routes
    core/         settings and Pydantic schemas
    graph/        LangGraph workflow and nodes
    rag/          smart PDF ingestion and Chroma retrieval
    z3_engine/    Z3 academic-rule checks
  data/           place regulation PDFs here
  chroma_db/      ChromaDB persistence
  scripts/        manual ingestion scripts
frontend/
  src/            React chat UI
docker-compose.yml
```

## Backend

```bash
cd backend
cp .env.example .env
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Health check:

```bash
curl http://localhost:8000/api/v1/health
```

Collection stats:

```bash
curl http://localhost:8000/api/v1/collection/stats
```

Ask endpoint:

```bash
curl -X POST http://localhost:8000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Điều kiện tốt nghiệp là gì?"}'
```

Without an LLM API key or ingested PDF, `/ask` returns a safe scaffold response instead of crashing.

## Ingest PDF

Place a PDF in `backend/data/`, then run:

```bash
cd backend
python scripts/ingest_pdf.py --pdf data/quy_che_hcmus_2024.pdf
```

Reset the collection before ingesting:

```bash
python scripts/ingest_pdf.py --pdf data/quy_che_hcmus_2024.pdf --reset
```

Or ingest through the API:

```bash
curl -X POST "http://localhost:8000/api/v1/collection/ingest?pdf_path=data/quy_che_hcmus_2024.pdf&reset=true"
```

Set `OPENAI_API_KEY` or `GOOGLE_API_KEY` in `backend/.env` before ingesting, depending on `EMBEDDING_PROVIDER`.

OCR is used only during PDF ingestion for pages where normal PDF text extraction is too short. Default `OCR_PROVIDER=auto` tries local PaddleOCR first, then uses OpenAI vision OCR as a fallback when Paddle returns weak text and `OPENAI_API_KEY` is configured. Use `OCR_PROVIDER=paddle` to avoid API cost, `OCR_PROVIDER=openai` for higher-quality OCR, or `OCR_PROVIDER=off` to disable OCR.

## Frontend

```bash
cd frontend
npm install
npm run dev
```

The app runs at `http://localhost:5173` and calls `http://localhost:8000/api/v1` by default.

## Docker Compose

```bash
cp backend/.env.example backend/.env
docker compose up --build
```

## Phase 2 Test Requests

Factual:

```bash
curl -X POST http://localhost:8000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Sinh viên bị cảnh cáo học vụ khi nào?"}'
```

Logical with Z3:

```bash
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
```

Scholarship:

```bash
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
```

## Phase 2 Checklist

- Smart chunking detects chapters, articles, sections, and falls back to sliding windows
- Retriever returns normalized cosine scores and filters weak matches
- LangGraph routes retrieve -> optional Z3 -> generate end to end
- Z3 covers graduation, academic warning, suspension, scholarship, course registration, and study deferral
- `/health` and `/collection/stats` report ChromaDB state
- `/collection/ingest` can ingest a PDF without restarting the backend
