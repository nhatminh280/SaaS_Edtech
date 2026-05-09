import logging

from app.rag.ingest import get_chroma_collection

logger = logging.getLogger(__name__)


def search_chunks(query: str, n_results: int = 3) -> list[dict]:
    """
    Search the most relevant chunks in ChromaDB.
    Returns dicts with id, document, metadata, and distance.
    """
    try:
        collection = get_chroma_collection()
        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )

        chunks = []
        ids = results.get("ids", [[]])[0]
        for i in range(len(ids)):
            chunks.append(
                {
                    "id": ids[i],
                    "document": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i],
                }
            )

        logger.info("Found %s chunks for query: %s...", len(chunks), query[:50])
        return chunks
    except ValueError as exc:
        logger.info("ChromaDB search skipped: %s", exc)
        return []
    except Exception as exc:
        logger.error("ChromaDB search error: %s", exc)
        return []
