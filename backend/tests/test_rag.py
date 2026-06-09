"""
RAG pipeline tests: chunking, embedding, FAISS retrieval.
Run from backend/ folder: pytest tests/test_rag.py -v
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import numpy as np
from backend.app.rag.chuncking import chunk_text, chunk_by_sentences
from backend.app.services.embeddding_service import get_embedding, get_embeddings
from backend.app.rag.fiass_store import FAISSStore
from tests.conftest import SAMPLE_TRANSCRIPT


# -- Chunking ------------------------------------------------------------------

def test_chunk_text_basic():
    chunks = chunk_text("word " * 500, chunk_size=100, overlap=10)
    assert len(chunks) > 0

def test_chunk_text_empty():
    assert chunk_text("") == []

def test_chunk_by_sentences():
    text = "Hello world. This is a test. Another sentence. One more."
    chunks = chunk_by_sentences(text, sentences_per_chunk=2)
    assert len(chunks) == 2

def test_chunk_transcript():
    chunks = chunk_text(SAMPLE_TRANSCRIPT, chunk_size=50, overlap=10)
    assert len(chunks) > 0


# -- Embeddings ----------------------------------------------------------------

def test_embedding_shape():
    emb = get_embedding("test sentence")
    assert isinstance(emb, list)
    assert len(emb) == 384

def test_embedding_not_zero():
    emb = get_embedding("Kafka consumer lag issue")
    assert any(v != 0.0 for v in emb)

def test_batch_embeddings():
    texts = ["hello world", "kafka streaming", "action items"]
    embeddings = get_embeddings(texts)
    assert len(embeddings) == 3
    assert all(len(e) == 384 for e in embeddings)

def test_embedding_similarity():
    e1 = np.array(get_embedding("Kafka consumer lag"))
    e2 = np.array(get_embedding("Kafka streaming delay"))
    e3 = np.array(get_embedding("The weather is sunny today"))
    def cosine(a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    assert cosine(e1, e2) > cosine(e1, e3)


# -- FAISS ---------------------------------------------------------------------

def test_faiss_add_and_search(tmp_path):
    store = FAISSStore(
        index_path=str(tmp_path / "test.index"),
        meta_path=str(tmp_path / "test.pkl"),
        dimension=384,
    )
    text = "Kafka consumer lag needs to be fixed"
    emb = get_embedding(text)
    store.add_vector("meeting-test", 0, text, emb)
    results = store.search(emb, k=1)
    assert len(results) == 1
    assert results[0]["text"] == text

def test_faiss_empty_search(tmp_path):
    store = FAISSStore(
        index_path=str(tmp_path / "empty.index"),
        meta_path=str(tmp_path / "empty.pkl"),
        dimension=384,
    )
    results = store.search(get_embedding("test"), k=5)
    assert results == []
