"""
RAG routes for semantic search and contextual question answering.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.app.rag.generator import generate_answer
from backend.app.rag.retriever import search_similar
from backend.app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["RAG"])


class AskRequest(BaseModel):
    query: str
    top_k: int = 5


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5


@router.post("/ask")
def ask_question(body: AskRequest):
    """
    Ask a natural language question over all ingested meeting transcripts.

    Examples:
      - "What decisions were made about Project X?"
      - "What action items were assigned last week?"
      - "Summarise discussions related to deployment issues."
    """
    if not body.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    result = generate_answer(query=body.query, top_k=body.top_k)
    return result


@router.post("/search")
def similarity_search(body: SearchRequest):
    """Return raw transcript chunks most similar to the query."""
    if not body.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    chunks = search_similar(query=body.query, top_k=body.top_k)
    return {"query": body.query, "results": chunks}
