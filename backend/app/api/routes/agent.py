"""
Agent routes.

POST /agent/{meeting_id}/run - run the full agentic workflow for a meeting.
"""

from fastapi import APIRouter, HTTPException

from backend.app.agent.meeting_agent import MeetingAgent
from backend.app.db.models import (
    init_db,
    get_meeting,
    get_transcript_chunks,
)
from backend.app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["Agent"])

init_db()


@router.post("/{meeting_id}/run")
def run_agent(meeting_id: str):
    """
    Run the AI agent pipeline for a specific meeting.
    Returns escalation decision, unresolved topics, missed action items,
    prioritised follow-ups, and a reminder message.
    """

    # Check if meeting exists
    meeting = get_meeting(meeting_id)

    if not meeting:
        raise HTTPException(
            status_code=404,
            detail=f"Meeting '{meeting_id}' not found."
        )

    # Fetch transcript chunks
    chunks = get_transcript_chunks(meeting_id)

    if not chunks:
        raise HTTPException(
            status_code=400,
            detail="No transcript found for this meeting."
        )

    # Combine transcript text
    transcript = " ".join(c["text"] for c in chunks)

    # Run AI agent
    agent = MeetingAgent(
        meeting_id=meeting_id,
        transcript=transcript
    )

    result = agent.run()

    return result