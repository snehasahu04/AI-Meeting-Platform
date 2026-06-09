# -*- coding: utf-8 -*-
"""Transcription service using Groq Whisper."""

from backend.app.utils.logger import get_logger

logger = get_logger(__name__)

_client = None


def _get_client():
    global _client
    if _client is None:
        from groq import Groq
        from backend.app.config import settings

        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is not set in .env")

        _client = Groq(api_key=settings.GROQ_API_KEY)
        logger.info("Groq transcription client ready.")
    return _client


def transcribe_audio(file_path: str) -> str:
    client = _get_client()

    from backend.app.config import settings

    logger.info(f"Transcribing: {file_path}")

    with open(file_path, "rb") as audio_file:
        result = client.audio.transcriptions.create(
            file=audio_file,
            model=settings.WHISPER_MODEL,
            response_format="json",
        )

    text = (getattr(result, "text", "") or "").strip()
    logger.info(f"Done ({len(text)} chars).")
    return text
