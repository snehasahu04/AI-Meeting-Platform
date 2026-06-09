"""
Real-time transcription via WebSocket using Groq Whisper.

Protocol:
  1. Client connects to:
     ws://localhost:8000/stream/transcript?meeting_id=<id>&title=<title>

  2. Client sends raw PCM audio as binary frames
     Format: int16, mono, 16000 Hz

  3. Server buffers frames and transcribes every ~1.5 sec

  4. Server sends:
     {
       "transcript": "...",
       "chunk_index": N,
       "meeting_id": "...",
       "is_final": false
     }

  5. Client sends text "END"
     -> server flushes remaining audio
     -> sends final event
     -> publishes transcript to Kafka
"""

import asyncio
import json
import os
import tempfile
import wave
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect

from backend.app.utils.logger import get_logger

logger = get_logger(__name__)

# -------------------------------------------------------------------
# Audio settings
# -------------------------------------------------------------------

SAMPLE_RATE = 16000

# Smaller = faster live transcript updates
CHUNK_FLUSH_COUNT = 12

_groq_client = None


# -------------------------------------------------------------------
# Groq Whisper Loader
# -------------------------------------------------------------------

def _get_groq_client():
    global _groq_client

    if _groq_client is None:
        from groq import Groq
        from backend.app.config import settings

        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is not set in .env")

        _groq_client = Groq(api_key=settings.GROQ_API_KEY)
        logger.info("Groq transcription client ready.")

    return _groq_client


# -------------------------------------------------------------------
# PCM -> WAV conversion
# -------------------------------------------------------------------

def _pcm_to_wav(raw_bytes: bytes) -> str:
    """
    Convert raw PCM int16 bytes to a temporary WAV file for Groq.
    """
    wav_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    wav_file.close()

    with wave.open(wav_file.name, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(raw_bytes)

    return wav_file.name


# -------------------------------------------------------------------
# Groq Whisper transcription
# -------------------------------------------------------------------

async def _transcribe(raw_audio: bytes) -> str:
    """
    Run Groq Whisper transcription in background thread.
    """

    loop = asyncio.get_event_loop()

    def _run():
        wav_path = None
        try:
            # Ignore tiny audio
            if len(raw_audio) < SAMPLE_RATE * 0.1 * 2:
                return ""

            from backend.app.config import settings

            client = _get_groq_client()
            wav_path = _pcm_to_wav(raw_audio)

            with open(wav_path, "rb") as audio_file:
                result = client.audio.transcriptions.create(
                    file=audio_file,
                    model=settings.WHISPER_MODEL,
                    language="en",
                    response_format="json",
                )

            text = (getattr(result, "text", "") or "").strip()

            return text

        except Exception as exc:
            logger.error(f"Groq Whisper transcription failed: {exc}")
            return ""
        finally:
            if wav_path:
                try:
                    os.remove(wav_path)
                except Exception:
                    pass

    return await loop.run_in_executor(None, _run)


# -------------------------------------------------------------------
# Save transcript chunk
# -------------------------------------------------------------------

def _persist_chunk(meeting_id: str, chunk_index: int, text: str):
    """
    Save transcript chunk into SQLite DB.
    """

    try:
        from backend.app.db.models import get_conn

        conn = get_conn()

        try:
            conn.execute(
                """
                INSERT INTO meeting_transcripts
                (
                    meeting_id,
                    chunk_index,
                    text,
                    created_at
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    meeting_id,
                    chunk_index,
                    text,
                    datetime.utcnow().isoformat(),
                ),
            )

            conn.commit()

        finally:
            conn.close()

    except Exception as exc:
        logger.warning(f"DB save failed for chunk {chunk_index}: {exc}")


# -------------------------------------------------------------------
# Kafka publisher
# -------------------------------------------------------------------

def _publish_to_kafka(meeting_id: str, full_transcript: str):
    """
    Publish transcript to Kafka pipeline.
    """

    try:
        from backend.app.kafka.producer import send_transcript

        send_transcript(
            meeting_id=meeting_id,
            transcript=full_transcript,
        )

        logger.info(
            f"Transcript published to Kafka for meeting '{meeting_id}'."
        )

    except Exception as exc:
        logger.warning(f"Kafka publish failed: {exc}")


# -------------------------------------------------------------------
# Main realtime transcription WebSocket
# -------------------------------------------------------------------

async def realtime_transcription(
    websocket: WebSocket,
    meeting_id: str,
    title: str,
):
    """
    Main WebSocket transcription handler.
    """

    await websocket.accept()

    logger.info(
        f"Live transcription started | "
        f"meeting_id='{meeting_id}' | title='{title}'"
    )

    # ---------------------------------------------------------------
    # Ensure meeting exists
    # ---------------------------------------------------------------

    try:
        from backend.app.db.models import insert_meeting

        insert_meeting(meeting_id, title)

    except Exception as exc:
        logger.warning(f"Could not create meeting row: {exc}")

    # ---------------------------------------------------------------
    # Runtime buffers
    # ---------------------------------------------------------------

    frames = []

    chunk_index = 0

    transcript_parts = []

    # ---------------------------------------------------------------
    # Flush buffered audio
    # ---------------------------------------------------------------

    async def flush(is_final: bool = False):
        nonlocal chunk_index

        if not frames:
            return

        try:
            raw_audio = b"".join(frames)

            frames.clear()

            text = await _transcribe(raw_audio)

            if not text:
                return

            transcript_parts.append(text)

            # Save in DB
            loop = asyncio.get_event_loop()

            await loop.run_in_executor(
                None,
                _persist_chunk,
                meeting_id,
                chunk_index,
                text,
            )

            payload = {
                "meeting_id": meeting_id,
                "chunk_index": chunk_index,
                "transcript": text,
                "is_final": is_final,
            }

            await websocket.send_text(json.dumps(payload))

            logger.info(
                f"[{'FINAL' if is_final else 'LIVE'}] "
                f"{meeting_id} | chunk={chunk_index} | text={text[:80]}"
            )

            chunk_index += 1

        except Exception as exc:
            logger.error(f"Flush failed: {exc}")

    # ---------------------------------------------------------------
    # Main receive loop
    # ---------------------------------------------------------------

    try:
        while True:

            msg = await websocket.receive()

            # -------------------------------------------------------
            # Binary audio frame
            # -------------------------------------------------------

            if msg.get("bytes") is not None:

                audio_bytes = msg["bytes"]

                frames.append(audio_bytes)

                # Flush every N frames
                if len(frames) >= CHUNK_FLUSH_COUNT:
                    await flush(is_final=False)

            # -------------------------------------------------------
            # Text commands
            # -------------------------------------------------------

            elif msg.get("text") is not None:

                command = msg["text"].strip().upper()

                logger.info(f"Received command: {command}")

                # ---------------------------------------------------
                # END command
                # ---------------------------------------------------

                if command == "END":

                    logger.info(
                        f"Ending transcription session for {meeting_id}"
                    )

                    # Flush remaining audio
                    await flush(is_final=True)

                    # Publish complete transcript
                    if transcript_parts:

                        full_transcript = " ".join(transcript_parts)

                        loop = asyncio.get_event_loop()

                        await loop.run_in_executor(
                            None,
                            _publish_to_kafka,
                            meeting_id,
                            full_transcript,
                        )

                    # Send final event
                    await websocket.send_text(
                        json.dumps(
                            {
                                "meeting_id": meeting_id,
                                "transcript": "",
                                "is_final": True,
                                "status": "done",
                                "total_chunks": chunk_index,
                            }
                        )
                    )

                    logger.info(
                        f"Session finished | "
                        f"meeting_id='{meeting_id}' | "
                        f"chunks={chunk_index}"
                    )

                    break

    # ----------------------------------------------------------------
    # Client disconnected
    # ----------------------------------------------------------------

    except WebSocketDisconnect:

        logger.info(
            f"Client disconnected | meeting_id='{meeting_id}'"
        )

        try:
            if frames:
                await flush(is_final=True)

            if transcript_parts:

                full_transcript = " ".join(transcript_parts)

                loop = asyncio.get_event_loop()

                await loop.run_in_executor(
                    None,
                    _publish_to_kafka,
                    meeting_id,
                    full_transcript,
                )

        except Exception as exc:
            logger.warning(f"Disconnect cleanup failed: {exc}")

    # ----------------------------------------------------------------
    # Unknown server error
    # ----------------------------------------------------------------

    except Exception as exc:

        logger.error(
            f"Realtime transcription error "
            f"for meeting '{meeting_id}': {exc}"
        )

        try:
            await websocket.send_text(
                json.dumps(
                    {
                        "error": str(exc)
                    }
                )
            )

        except Exception:
            pass

        try:
            await websocket.close()
        except Exception:
            pass
