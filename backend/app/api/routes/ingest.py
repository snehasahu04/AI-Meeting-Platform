"""
POST /ingest/audio  - Upload audio, transcribe, embed, send to Kafka
POST /ingest/text   - Ingest raw transcript text
"""


import os
import uuid
import shutil

from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel

from backend.app.db.models import init_db, insert_meeting, insert_transcript_chunks
from backend.app.kafka.producer import send_transcript
from backend.app.rag.chuncking import chunk_text
from backend.app.rag.fiass_store import faiss_store
from backend.app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["Ingestion"])
init_db()


class TextIngestRequest(BaseModel):
    meeting_id: str | None = None
    transcript: str


def _embed_and_store(meeting_id: str, chunks: list[str]):
    """Embed chunks and add to FAISS. Done lazily to avoid slow startup."""
    try:
        from backend.app.services.embeddding_service import get_embeddings
        embeddings = get_embeddings(chunks)
        faiss_store.add_vectors_batch(meeting_id, chunks, embeddings)
    except Exception as e:
        logger.warning(f"Embedding failed (non-fatal): {e}")


@router.post("/audio")
def upload_audio(file: UploadFile = File(...)):
    os.makedirs("data/transcripts", exist_ok=True)
    file_path = f"data/transcripts/{file.filename}"

    with open(file_path, "wb") as buf:
        shutil.copyfileobj(file.file, buf)

    try:
        from backend.app.services.transcription_service import transcribe_audio
        transcript = transcribe_audio(file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {e}")

    meeting_id = str(uuid.uuid4())
    chunks = chunk_text(transcript, chunk_size=200, overlap=20)

    insert_meeting(meeting_id, file.filename)
    insert_transcript_chunks(meeting_id, chunks)
    _embed_and_store(meeting_id, chunks)
    send_transcript(meeting_id=meeting_id, transcript=transcript)

    return {
        "meeting_id": meeting_id,
        "filename": file.filename,
        "transcript_preview": transcript[:300],
        "chunks_indexed": len(chunks),
        "status": "processing",
    }


@router.post("/text")
def ingest_text(body: TextIngestRequest):
    transcript = (body.transcript or "").strip()
    if not transcript:
        raise HTTPException(status_code=400, detail="Transcript cannot be empty.")

    meeting_id = body.meeting_id or str(uuid.uuid4())
    chunks = chunk_text(transcript, chunk_size=200, overlap=20)

    insert_meeting(meeting_id, f"text_ingest_{meeting_id[:8]}")
    insert_transcript_chunks(meeting_id, chunks)
    _embed_and_store(meeting_id, chunks)
    send_transcript(meeting_id=meeting_id, transcript=transcript)

    return {
        "meeting_id": meeting_id,
        "chunks_indexed": len(chunks),
        "status": "processing",
    }
