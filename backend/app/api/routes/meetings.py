"""
Meeting routes.

GET  /meetings/                  - list all meetings
GET  /meetings/{id}              - meeting detail
GET  /meetings/{id}/summary      - AI summary
GET  /meetings/{id}/action-items - action items
GET  /meetings/{id}/sentiment    - sentiment analysis
GET  /meetings/{id}/topics       - topic clusters
POST /meetings/{id}/follow-up    - follow-up email

NEW:
POST /meetings/create            - create new meeting
"""

from fastapi import APIRouter, Body, HTTPException, Query
from pydantic import BaseModel
import uuid

from backend.app.db.models import (
    init_db, get_meeting, get_all_meetings, get_full_transcript,
    get_chunk_count, get_summary, save_summary,
    get_action_items, save_action_items, get_transcript_chunks,
)

from backend.app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["Meetings"])
init_db()


# =========================
# 🔥 NEW: CREATE MEETING
# =========================

class CreateMeeting(BaseModel):
    title: str


@router.post("/create")
def create_meeting(
    payload: CreateMeeting | None = Body(default=None),
    title: str | None = Query(default=None),
):
    meeting_title = payload.title if payload else title
    if not meeting_title:
        raise HTTPException(
            status_code=422,
            detail="Meeting title is required. Send JSON {'title': '...'} or use ?title=...",
        )

    meeting_id = str(uuid.uuid4())

    # optional DB save (safe fallback)
    try:
        from backend.app.db.models import insert_meeting
        insert_meeting(meeting_id, meeting_title)
    except Exception as e:
        logger.warning(f"insert_meeting skipped: {e}")

    return {
        "meeting_id": meeting_id,
        "title": meeting_title,
        "status": "created"
    }


# =========================
# INTERNAL HELPER
# =========================

def _require_meeting(meeting_id: str) -> dict:
    m = get_meeting(meeting_id)
    if not m:
        raise HTTPException(
            status_code=404,
            detail=f"Meeting '{meeting_id}' not found."
        )
    return m


# =========================
# GET ALL MEETINGS
# =========================

@router.get("/")
def list_meetings():
    return get_all_meetings()


# =========================
# GET MEETING DETAIL
# =========================

@router.get("/{meeting_id}")
def meeting_detail(meeting_id: str):
    m = _require_meeting(meeting_id)
    m["chunk_count"] = get_chunk_count(meeting_id)
    return m


# =========================
# SUMMARY
# =========================

@router.get("/{meeting_id}/summary")
def get_meeting_summary(meeting_id: str):
    _require_meeting(meeting_id)

    cached = get_summary(meeting_id)
    if cached:
        return {"meeting_id": meeting_id, "summary": cached, "cached": True}

    transcript = get_full_transcript(meeting_id)
    if not transcript:
        raise HTTPException(status_code=400, detail="No transcript found.")

    from backend.app.services.summarization_service import build_summary
    summary = build_summary(transcript)
    save_summary(meeting_id, summary)

    return {"meeting_id": meeting_id, "summary": summary, "cached": False}


# =========================
# ACTION ITEMS
# =========================

@router.get("/{meeting_id}/action-items")
def get_meeting_action_items(meeting_id: str):
    _require_meeting(meeting_id)

    cached = get_action_items(meeting_id)
    if cached:
        return {"meeting_id": meeting_id, "action_items": cached, "cached": True}

    transcript = get_full_transcript(meeting_id)
    if not transcript:
        raise HTTPException(status_code=400, detail="No transcript found.")

    from backend.app.services.action_item_service import extract_action_items
    items = extract_action_items(transcript)
    save_action_items(meeting_id, items)

    return {"meeting_id": meeting_id, "action_items": items, "cached": False}


# =========================
# SENTIMENT
# =========================

@router.get("/{meeting_id}/sentiment")
def get_meeting_sentiment(meeting_id: str):
    _require_meeting(meeting_id)

    chunks = get_transcript_chunks(meeting_id)
    if not chunks:
        raise HTTPException(status_code=400, detail="No transcript chunks found.")

    from backend.app.services.sentiment_service import analyse_batch, aggregate_sentiment

    texts = [c["text"] for c in chunks]
    per_chunk = analyse_batch(texts)
    aggregate = aggregate_sentiment(per_chunk)

    return {
        "meeting_id": meeting_id,
        "aggregate": aggregate,
        "per_chunk": per_chunk
    }


# =========================
# TOPICS
# =========================

@router.get("/{meeting_id}/topics")
def get_meeting_topics(meeting_id: str, num_clusters: int = 3):
    _require_meeting(meeting_id)

    chunks = get_transcript_chunks(meeting_id)
    if not chunks:
        raise HTTPException(status_code=400, detail="No transcript chunks found.")

    from backend.app.services.clustering_service import cluster_transcript_chunks

    texts = [c["text"] for c in chunks]
    result = cluster_transcript_chunks(texts, num_clusters=num_clusters)

    return {
        "meeting_id": meeting_id,
        "num_clusters": num_clusters,
        "labels": result["labels"],
        "top_terms": result["top_terms"]
    }


# =========================
# FOLLOW UP EMAIL
# =========================

@router.post("/{meeting_id}/follow-up")
def generate_follow_up(meeting_id: str):
    _require_meeting(meeting_id)

    summary = get_summary(meeting_id)
    if not summary:
        transcript = get_full_transcript(meeting_id)
        from backend.app.services.summarization_service import build_summary
        summary = build_summary(transcript)

    items = get_action_items(meeting_id)

    action_text = "\n".join(
        f"- {i['task']} (Owner: {i['owner']}, Deadline: {i['deadline']})"
        for i in items
    ) or "No action items yet."

    from backend.app.services.summarization_service import generate_follow_up_email
    email = generate_follow_up_email(summary, action_text)

    return {
        "meeting_id": meeting_id,
        "follow_up_email": email
    }
