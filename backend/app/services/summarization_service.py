# -*- coding: utf-8 -*-
"""Meeting summarisation and follow-up email generation."""

from backend.app.llm import llm_call
from backend.app.utils.logger import get_logger

logger = get_logger(__name__)


def build_summary(transcript: str) -> str:
    if not transcript or not transcript.strip():
        return "No transcript provided."
    prompt = f"""You are an expert meeting analyst.
Convert this transcript into a structured summary.

Return in this format:
## Summary
(2-4 sentences)

## Key Discussion Points
- point 1
- point 2

## Decisions Made
- decision 1

## Open Issues
- issue 1

Transcript:
{transcript}
"""
    logger.info("Generating meeting summary...")
    return llm_call(prompt=prompt, context="")


def generate_follow_up_email(summary: str, action_items: str) -> str:
    prompt = f"""Write a professional follow-up email based on this meeting summary and action items.
Include: subject line, thank attendees, recap decisions, list action items with owners. Under 200 words.

Summary:
{summary}

Action Items:
{action_items}
"""
    logger.info("Generating follow-up email...")
    return llm_call(prompt=prompt, context="")
