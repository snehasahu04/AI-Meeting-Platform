# -*- coding: utf-8 -*-
"""Kafka producer - sends events to all platform topics."""

import json
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable

from backend.app.config import settings
from backend.app.utils.logger import get_logger

logger = get_logger(__name__)

_producer = None


def get_producer():
    global _producer
    if _producer is None:
        try:
            _producer = KafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                retries=3,
            )
            logger.info("Kafka producer connected.")
        except NoBrokersAvailable:
            logger.warning("Kafka not available - events will be skipped.")
            _producer = None
    return _producer


def _send(topic: str, payload: dict):
    producer = get_producer()
    if producer is None:
        return
    try:
        producer.send(topic, payload)
        producer.flush()
    except Exception as e:
        logger.warning(f"Kafka send failed: {e}")


def send_audio(audio_hex: str):
    _send(settings.TOPIC_RAW_AUDIO, {"audio": audio_hex})


def send_transcript(meeting_id: str, transcript: str):
    _send(settings.TOPIC_TRANSCRIPTS, {"meeting_id": meeting_id, "transcript": transcript})


def send_summary(meeting_id: str, summary: str):
    _send(settings.TOPIC_SUMMARIES, {"meeting_id": meeting_id, "summary": summary})


def send_action_items(meeting_id: str, items: list):
    _send(settings.TOPIC_ACTION_ITEMS, {"meeting_id": meeting_id, "action_items": items})


def send_alert(meeting_id: str, alert_type: str, detail: str):
    _send(settings.TOPIC_ALERTS, {"meeting_id": meeting_id, "alert_type": alert_type, "detail": detail})


def send_speaker_event(meeting_id: str, speaker: str, speaking_time: float):
    _send(settings.TOPIC_SPEAKER_EVENTS, {"meeting_id": meeting_id, "speaker": speaker, "speaking_time": speaking_time})
