# -*- coding: utf-8 -*-
"""Action item extraction using LLM with JSON output."""

import json
from backend.app.llm import llm_call
from backend.app.utils.logger import get_logger

logger = get_logger(__name__)


def extract_action_items(transcript: str) -> list:
    if not transcript or not transcript.strip():
        return []

    prompt = f"""You are an expert meeting analyst.
Extract ALL action items from this transcript.

Return ONLY a valid JSON array. Each element must have:
  "task"     - what needs to be done
  "owner"    - who is responsible (use "Not specified" if unknown)
  "deadline" - when it is due (use "Not specified" if unknown)
  "status"   - always "open"

Example:
[
  {{"task": "Fix Kafka lag", "owner": "Bob", "deadline": "Friday", "status": "open"}}
]

Transcript:
{transcript}

JSON array:"""

    logger.info("Extracting action items...")
    raw = llm_call(prompt=prompt, context="")

    try:
        start = raw.find("[")
        end = raw.rfind("]") + 1
        if start == -1 or end == 0:
            return []
        items = json.loads(raw[start:end])
        return items if isinstance(items, list) else []
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse action items: {e}")
        return []
