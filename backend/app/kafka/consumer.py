# -*- coding: utf-8 -*-
"""Kafka consumers - one thread per topic."""

import json
import threading

from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable

from backend.app.config import settings
from backend.app.utils.logger import get_logger

logger = get_logger(__name__)


def _make_consumer(topic: str):
    try:
        consumer = KafkaConsumer(
            topic,
            bootstrap_servers=settings.KAFKA_BOOTSTRAP,
            value_deserializer=lambda x: json.loads(x.decode("utf-8")),
            auto_offset_reset="latest",
            enable_auto_commit=True,
            group_id=f"meeting_ai_{topic}",
        )
        logger.info(f"Consumer ready for topic '{topic}'.")
        return consumer
    except NoBrokersAvailable:
        logger.warning(f"Kafka not available - consumer for '{topic}' skipped.")
        return None
    except Exception as e:
        logger.warning(f"Consumer error for '{topic}': {e}")
        return None


def _consume_transcripts():
    consumer = _make_consumer(settings.TOPIC_TRANSCRIPTS)
    if consumer is None:
        return
    for msg in consumer:
        try:
            event = msg.value
            meeting_id = event.get("meeting_id", "unknown")
            transcript = event.get("transcript", "")
            logger.info(f"Transcript received for meeting '{meeting_id}'")

            from backend.app.rag.chuncking import chunk_text
            from backend.app.services.embeddding_service import get_embeddings
            from backend.app.rag.fiass_store import faiss_store
            from backend.app.kafka.producer import send_summary, send_action_items

            chunks = chunk_text(transcript, chunk_size=200, overlap=20)
            if chunks:
                embeddings = get_embeddings(chunks)
                faiss_store.add_vectors_batch(meeting_id, chunks, embeddings)

            from backend.app.services.summarization_service import build_summary
            summary = build_summary(transcript)
            send_summary(meeting_id=meeting_id, summary=summary)

            from backend.app.services.action_item_service import extract_action_items
            items = extract_action_items(transcript)
            if items:
                send_action_items(meeting_id=meeting_id, items=items)

        except Exception as e:
            logger.error(f"Error processing transcript: {e}")


def _consume_summaries():
    consumer = _make_consumer(settings.TOPIC_SUMMARIES)
    if consumer is None:
        return
    for msg in consumer:
        try:
            event = msg.value
            logger.info(f"Summary for '{event.get('meeting_id')}': {str(event.get('summary',''))[:80]}")
        except Exception as e:
            logger.error(f"Summary consumer error: {e}")


def _consume_action_items():
    consumer = _make_consumer(settings.TOPIC_ACTION_ITEMS)
    if consumer is None:
        return
    for msg in consumer:
        try:
            event = msg.value
            items = event.get("action_items", [])
            logger.info(f"Action items for '{event.get('meeting_id')}': {len(items)} items")
        except Exception as e:
            logger.error(f"Action items consumer error: {e}")


def _consume_alerts():
    consumer = _make_consumer(settings.TOPIC_ALERTS)
    if consumer is None:
        return
    for msg in consumer:
        try:
            event = msg.value
            logger.warning(f"ALERT [{event.get('alert_type')}] for '{event.get('meeting_id')}': {event.get('detail')}")
        except Exception as e:
            logger.error(f"Alert consumer error: {e}")


def _consume_speaker_events():
    consumer = _make_consumer(settings.TOPIC_SPEAKER_EVENTS)
    if consumer is None:
        return
    for msg in consumer:
        try:
            event = msg.value
            logger.info(f"Speaker '{event.get('speaker')}' in '{event.get('meeting_id')}'")
        except Exception as e:
            logger.error(f"Speaker event consumer error: {e}")


def start_consumer():
    """Start all Kafka consumers in daemon threads."""
    fns = [_consume_transcripts, _consume_summaries, _consume_action_items,
           _consume_alerts, _consume_speaker_events]
    for fn in fns:
        t = threading.Thread(target=fn, daemon=True)
        t.start()
    logger.info(f"Started {len(fns)} Kafka consumer threads.")
