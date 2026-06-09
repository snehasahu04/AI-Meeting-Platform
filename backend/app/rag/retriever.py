# -*- coding: utf-8 -*-
"""RAG retriever - converts query to embedding and searches FAISS."""

from backend.app.rag.fiass_store import faiss_store
from backend.app.services.embeddding_service import get_embedding
from backend.app.utils.logger import get_logger

logger = get_logger(__name__)


def search_similar(query: str, top_k: int = 5) -> list:
    logger.info(f"Searching for: '{query[:60]}'")
    query_embedding = get_embedding(query)
    results = faiss_store.search(query_embedding, k=top_k)
    logger.info(f"Found {len(results)} results.")
    return results
