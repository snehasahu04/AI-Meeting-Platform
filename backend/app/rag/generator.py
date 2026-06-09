# -*- coding: utf-8 -*-
"""RAG generator - retrieve context then generate answer with LLM."""

from backend.app.rag.retriever import search_similar
from backend.app.llm import llm_call
from backend.app.utils.logger import get_logger

logger = get_logger(__name__)


def generate_answer(query: str, top_k: int = 5) -> dict:
    logger.info(f"RAG query: '{query[:60]}'")
    chunks = search_similar(query, top_k=top_k)

    if not chunks:
        return {
            "answer": "No relevant meeting data found. Please ingest some meetings first.",
            "sources": [],
        }

    context = "\n\n".join(
        f"[Meeting: {c.get('meeting_id')} | Chunk {c.get('chunk_id')}]\n{c.get('text')}"
        for c in chunks
    )

    prompt = f"""You are a meeting intelligence assistant.
Use ONLY the context below to answer the question.
If the answer is not in the context, say "I don't have enough information."

Question: {query}

Answer clearly and concisely:"""

    answer = llm_call(prompt=prompt, context=context)
    return {"answer": answer, "sources": chunks}
