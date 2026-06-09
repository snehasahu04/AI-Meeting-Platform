"""
ML pipeline tests.
Run from backend/ folder: pytest tests/test_ml.py -v
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from backend.app.ml.clustering import cluster_topics
from backend.app.ml.anomaly_detection import detect_anomalies
from backend.app.ml.tfidf import top_keywords, get_tfidf_matrix
from backend.app.services.sentiment_service import analyse_sentiment, aggregate_sentiment
from backend.app.services.clustering_service import cluster_transcript_chunks
from tests.conftest import SAMPLE_TRANSCRIPT


def test_cluster_topics_basic():
    embeddings = np.random.rand(10, 384).tolist()
    labels, model = cluster_topics(embeddings, num_clusters=3)
    assert len(labels) == 10

def test_cluster_topics_empty():
    labels, model = cluster_topics([], num_clusters=3)
    assert len(labels) == 0

def test_detect_anomalies_basic():
    embeddings = np.random.rand(20, 384).tolist()
    result = detect_anomalies(embeddings)
    assert len(result["predictions"]) == 20

def test_detect_anomalies_empty():
    result = detect_anomalies([])
    assert result["anomaly_count"] == 0

def test_tfidf_matrix():
    texts = ["kafka consumer lag", "deployment pipeline issue", "action items review"]
    X, features = get_tfidf_matrix(texts)
    assert X.shape[0] == 3

def test_top_keywords():
    keywords = top_keywords([SAMPLE_TRANSCRIPT], top_n=5)
    assert len(keywords) == 5

def test_sentiment_positive():
    result = analyse_sentiment("This meeting was very productive and successful!")
    assert result["label"] == "positive"

def test_sentiment_negative():
    result = analyse_sentiment("Everything is broken and the deployment failed badly.")
    assert result["label"] in ("negative", "neutral")

def test_aggregate_empty():
    agg = aggregate_sentiment([])
    assert agg["avg_score"] == 0.0

def test_cluster_transcript_chunks():
    from backend.app.rag.chuncking import chunk_text
    chunks = chunk_text(SAMPLE_TRANSCRIPT, chunk_size=30)
    result = cluster_transcript_chunks(chunks, num_clusters=2)
    assert len(result["labels"]) == len(chunks)
