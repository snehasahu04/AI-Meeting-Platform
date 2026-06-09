# -*- coding: utf-8 -*-
"""Text chunking utilities for the RAG pipeline."""

import re


def chunk_text(text: str, chunk_size: int = 200, overlap: int = 20) -> list:
    words = text.split()
    if not words:
        return []
    step = max(1, chunk_size - overlap)
    chunks = []
    for i in range(0, len(words), step):
        chunk = " ".join(words[i: i + chunk_size])
        if chunk:
            chunks.append(chunk)
    return chunks


def chunk_by_sentences(text: str, sentences_per_chunk: int = 5) -> list:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    chunks = []
    for i in range(0, len(sentences), sentences_per_chunk):
        chunk = " ".join(sentences[i: i + sentences_per_chunk])
        if chunk:
            chunks.append(chunk)
    return chunks
