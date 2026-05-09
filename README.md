# QA Quy chế HCMUS

Phase 1 scaffold for a university-regulation QA system using FastAPI, LangGraph, RAG over ChromaDB, Z3 rule checks, and a Vite React chat UI.

## Structure

```txt
backend/
  app/
    api/          FastAPI routes
    core/         settings and Pydantic schemas
    graph/        LangGraph workflow and nodes
    rag/          PDF ingestion and Chroma retrieval
    z3_engine/    initial Z3 rules
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

Set `OPENAI_API_KEY` or `GOOGLE_API_KEY` in `backend/.env` before ingesting, depending on `EMBEDDING_PROVIDER`.

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

## Phase 1 Checklist

- FastAPI skeleton with `GET /health` and `POST /ask`
- Pydantic schemas for request, response, citation, Z3 result, and graph state
- LangGraph workflow with retrieve, reason, and generate nodes
- ChromaDB PDF ingestion and retriever modules
- Three initial Z3 rule stubs
- Vite React chat UI calling the backend API
- `.env.example` with configurable keys and model settings
