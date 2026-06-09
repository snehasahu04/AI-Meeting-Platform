# -*- coding: utf-8 -*-
"""Embedding service using fastembed (all-MiniLM-L6-v2). Dimension: 384."""

from backend.app.utils.logger import get_logger

logger = get_logger(__name__)

_model = None


def _get_model():
    global _model
    if _model is None:
        logger.info("Loading fastembed model...")
        from fastembed import TextEmbedding

        _model = TextEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
        logger.info("Embedding model ready.")
    return _model


def get_embedding(text: str) -> list:
    model = _get_model()
    return next(model.embed([text])).tolist()


def get_embeddings(texts: list) -> list:
    if not texts:
        return []
    model = _get_model()
    return [embedding.tolist() for embedding in model.embed(texts)]
