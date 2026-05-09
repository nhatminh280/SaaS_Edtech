import logging

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.core.config import settings
from app.rag.ingest import get_chroma_collection

logger = logging.getLogger(__name__)


def search_chunks(query: str, n_results: int = 5, min_score: float = 0.3) -> list[dict]:
    """
    Search relevant chunks.
    Chroma cosine distance: 0 = identical, 2 = opposite.
    Score is normalized to 0..1 as 1 - distance / 2.
    """
    try:
        collection = get_chroma_collection()
        count = collection.count()
        if count == 0:
            logger.info("ChromaDB collection is empty")
            return []

        results = collection.query(
            query_texts=[query],
            n_results=min(n_results, count),
            include=["documents", "metadatas", "distances"],
        )

        chunks = []
        ids = results.get("ids", [[]])[0]
        for i in range(len(ids)):
            distance = results["distances"][0][i]
            score = max(0.0, 1.0 - distance / 2.0)
            if score < min_score:
                continue

            chunks.append(
                {
                    "id": ids[i],
                    "document": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "score": round(score, 3),
                    "distance": distance,
                }
            )

        chunks.sort(key=lambda chunk: chunk["score"], reverse=True)
        chunks = chunks[:3]
        logger.info("Retrieved %s chunks (scores: %s)", len(chunks), [chunk["score"] for chunk in chunks])
        return chunks
    except ValueError as exc:
        logger.info("ChromaDB search skipped: %s", exc)
        return []
    except Exception as exc:
        logger.error("ChromaDB error: %s", exc)
        return []


def get_collection_stats() -> dict:
    """Return ChromaDB collection stats for debugging."""
    try:
        client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        collection = client.get_collection(settings.chroma_collection)
        return {"total_chunks": collection.count(), "collection": collection.name}
    except Exception as exc:
        return {"error": str(exc), "total_chunks": 0, "collection": None}
