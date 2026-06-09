"""
GET /analytics/overview
GET /analytics/{id}/engagement
GET /analytics/{id}/timeline
GET /analytics/{id}/speakers
"""

from fastapi import APIRouter, HTTPException
from backend.app.db.models import (
    init_db, get_meeting, get_transcript_chunks,
    get_total_meetings, get_total_chunks,
)
from backend.app.rag.fiass_store import faiss_store
from backend.app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["Analytics"])
init_db()


@router.get("/overview")
def overview():
    return {
        "total_meetings": get_total_meetings(),
        "total_transcript_chunks": get_total_chunks(),
        "total_vectors_indexed": faiss_store.total_vectors(),
    }


@router.get("/{meeting_id}/engagement")
def engagement(meeting_id: str):
    m = get_meeting(meeting_id)
    if not m:
        raise HTTPException(status_code=404, detail="Meeting not found.")

    chunks = get_transcript_chunks(meeting_id)
    if not chunks:
        raise HTTPException(status_code=400, detail="No transcript chunks found.")

    texts = [c["text"] for c in chunks]

    from backend.app.services.sentiment_service import analyse_batch, aggregate_sentiment
    sentiments = analyse_batch(texts)
    agg = aggregate_sentiment(sentiments)

    try:
        from backend.app.services.embeddding_service import get_embeddings
        from backend.app.ml.anomaly_detection import detect_anomalies
        embeddings = get_embeddings(texts)
        anomaly_result = detect_anomalies(embeddings)
        anomaly_count = anomaly_result["anomaly_count"]
        anomaly_indices = anomaly_result["anomaly_indices"]
    except Exception:
        anomaly_count = 0
        anomaly_indices = []

    anomaly_penalty = anomaly_count / max(len(texts), 1) * 30
    sentiment_bonus = (agg["avg_score"] + 1) / 2 * 40
    engagement_score = round(max(0, min(100, 60 + sentiment_bonus - anomaly_penalty)), 1)

    return {
        "meeting_id": meeting_id,
        "engagement_score": engagement_score,
        "anomaly_count": anomaly_count,
        "anomaly_chunk_indices": anomaly_indices,
        "sentiment_summary": agg,
    }


@router.get("/{meeting_id}/timeline")
def timeline(meeting_id: str):
    m = get_meeting(meeting_id)
    if not m:
        raise HTTPException(status_code=404, detail="Meeting not found.")

    chunks = get_transcript_chunks(meeting_id)
    if not chunks:
        raise HTTPException(status_code=400, detail="No transcript chunks found.")

    from backend.app.services.sentiment_service import analyse_batch
    texts = [c["text"] for c in chunks]
    sentiments = analyse_batch(texts)

    return {
        "meeting_id": meeting_id,
        "timeline": [
            {
                "chunk_index": i,
                "text_preview": texts[i][:80],
                "sentiment_score": s["score"],
                "sentiment_label": s["label"],
            }
            for i, s in enumerate(sentiments)
        ],
    }


@router.get("/{meeting_id}/speakers")
def speakers(meeting_id: str):
    m = get_meeting(meeting_id)
    if not m:
        raise HTTPException(status_code=404, detail="Meeting not found.")

    chunks = get_transcript_chunks(meeting_id)
    total_words = sum(len(c["text"].split()) for c in chunks)
    return {
        "meeting_id": meeting_id,
        "note": "Speaker diarisation not available. Showing aggregate.",
        "total_words": total_words,
        "speakers": [],
    }
