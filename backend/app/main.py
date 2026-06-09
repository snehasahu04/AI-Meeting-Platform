# """
# Meeting AI Platform — FastAPI entry point.
# Run from the backend/ folder:
#     uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# """

# import threading
# import uuid
# import backend.app.streaming.audio_stream
# from contextlib import asynccontextmanager

# from fastapi import FastAPI, HTTPException, Query, WebSocket
# from fastapi.middleware.cors import CORSMiddleware

# from backend.app.utils.logger import get_logger


# logger = get_logger(__name__)


# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # -- Startup ---------------------------------------------------------------
#     logger.info("Initialising database...")
#     from backend.app.db.models import init_db
#     init_db()
#     logger.info("Database ready.")

#     # Start Kafka consumers (gracefully skipped if Kafka is not running)
#     logger.info("Starting Kafka consumers...")
#     try:
#         from backend.app.kafka.consumer import start_consumer
#         thread = threading.Thread(target=start_consumer, daemon=True)
#         thread.start()
#         logger.info("Kafka consumers started.")
#     except Exception as e:
#         logger.warning(f"Kafka consumers not started (Kafka may be offline): {e}")

#     yield

#     logger.info("Shutting down.")


# app = FastAPI(
#     title="Meeting AI Platform",
#     description="Real-time meeting intelligence — transcription, RAG, analytics, AI agents.",
#     version="1.0.0",
#     lifespan=lifespan,
# )

# # -- CORS ----------------------------------------------------------------------
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],   # tighten in production
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # -- Routers -------------------------------------------------------------------
# from backend.app.api.routes import ingest, rag, meetings, analytics, agent  # noqa: E402

# app.include_router(ingest.router,    prefix="/ingest")
# app.include_router(rag.router,       prefix="/rag")
# app.include_router(meetings.router,  prefix="/meetings")
# app.include_router(analytics.router, prefix="/analytics")
# app.include_router(agent.router,     prefix="/agent")


# # -- Health --------------------------------------------------------------------
# @app.get("/", tags=["Health"])
# def health():
#     return {"status": "ok", "service": "Meeting AI Platform"}


# # -- Streaming: REST poll endpoint ---------------------------------------------
# @app.get("/stream/transcript/{meeting_id}", tags=["Streaming"])
# def get_live_transcript(meeting_id: str):
#     """
#     Fetch all transcript chunks accumulated so far for a live or completed meeting.
#     Useful for polling from a UI while the WebSocket session is still open.
#     """
#     from backend.app.db.models import get_transcript_chunks, get_meeting

#     meeting = get_meeting(meeting_id)
#     if not meeting:
#         raise HTTPException(status_code=404, detail=f"Meeting '{meeting_id}' not found.")

#     chunks = get_transcript_chunks(meeting_id)
#     full_text = " ".join(c["text"] for c in chunks if c.get("text"))
#     return {
#         "meeting_id": meeting_id,
#         "title": meeting.get("title"),
#         "status": meeting.get("status"),
#         "chunk_count": len(chunks),
#         "full_transcript": full_text,
#         "chunks": [
#             {
#                 "chunk_index": c["chunk_index"],
#                 "text": c["text"],
#                 "created_at": c["created_at"],
#             }
#             for c in chunks
#         ],
#     }


# # -- Streaming: WebSocket ------------------------------------------------------
# @app.websocket("/stream/transcript")
# async def ws_transcript(
#     websocket: WebSocket,
#     meeting_id: str = Query(
#         default=None,
#         description="Unique meeting ID; a new UUID is generated if omitted.",
#     ),
#     title: str = Query(
#         default="Live Meeting",
#         description="Human-readable meeting title stored in the DB.",
#     ),
# ):
#     """
#     Real-time audio transcription via WebSocket.

#     **Query params**
#     - `meeting_id` (optional) — reuse an existing meeting or start a new one
#     - `title`      (optional) — display name stored in the DB

#     **Client → Server**
#     - Binary frames: raw PCM int16, mono, 16 kHz
#     - Text `"END"`: signals end of session

#     **Server → Client (JSON)**
#     - Live chunk:  `{"meeting_id": "...", "chunk_index": N, "transcript": "...", "is_final": false}`
#     - Session end: `{"meeting_id": "...", "transcript": "", "is_final": true, "status": "done", "total_chunks": N}`
#     """
#     resolved_id = meeting_id or str(uuid.uuid4())
#     from backend.app.streaming.audio_stream import realtime_transcription
#     await realtime_transcription(websocket, meeting_id=resolved_id, title=title)

# print(app.routes)   



"""
Meeting AI Platform — FastAPI entry point
Run:
    uvicorn backend.app.main:app --reload --port 8000
"""

import threading
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from backend.app.utils.logger import get_logger

logger = get_logger(__name__)


# =========================
# APP LIFESPAN
# =========================
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initialising database...")

    from backend.app.db.models import init_db
    init_db()

    logger.info("Database ready.")

    # Kafka (optional)
    try:
        from backend.app.kafka.consumer import start_consumer
        thread = threading.Thread(target=start_consumer, daemon=True)
        thread.start()
        logger.info("Kafka consumers started.")
    except Exception as e:
        logger.warning(f"Kafka not running: {e}")

    yield

    logger.info("Shutting down...")


app = FastAPI(
    title="Meeting AI Platform",
    version="1.0.0",
    lifespan=lifespan,
)

# =========================
# CORS
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# ROUTES IMPORT
# =========================
from backend.app.api.routes import (
    ingest,
    rag,
    meetings,
    analytics,
    agent,
)

app.include_router(ingest.router, prefix="/ingest")
app.include_router(rag.router, prefix="/rag")
app.include_router(meetings.router, prefix="/meetings")
app.include_router(analytics.router, prefix="/analytics")
app.include_router(agent.router, prefix="/agent")


# =========================
# HEALTH CHECK
# =========================
@app.get("/")
def health():
    return {"status": "ok"}


# =========================
# CREATE MEETING (NEW ADD)
# =========================
@app.post("/meetings/create")
def create_meeting(title: str):
    """
    New meeting create endpoint
    """
    from backend.app.db.models import insert_meeting

    meeting_id = str(uuid.uuid4())
    insert_meeting(meeting_id, title)

    return {
        "meeting_id": meeting_id,
        "title": title,
        "status": "created"
    }


# =========================
# REST TRANSCRIPT FETCH
# =========================
@app.get("/stream/transcript/{meeting_id}")
def get_live_transcript(meeting_id: str):
    from backend.app.db.models import get_transcript_chunks, get_meeting

    meeting = get_meeting(meeting_id)
    if not meeting:
        raise HTTPException(404, "Meeting not found")

    chunks = get_transcript_chunks(meeting_id)

    return {
        "meeting_id": meeting_id,
        "title": meeting.get("title"),
        "chunks": chunks
    }


# =========================
# WEBSOCKET TRANSCRIPT
# =========================
@app.websocket("/stream/transcript")
async def ws_transcript(
    websocket: WebSocket,
    meeting_id: str = Query(None),
    title: str = Query("Live Meeting"),
):
    from backend.app.streaming.audio_stream import realtime_transcription

    resolved_id = meeting_id or str(uuid.uuid4())

    await realtime_transcription(
        websocket,
        meeting_id=resolved_id,
        title=title
    )