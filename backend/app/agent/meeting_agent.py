# -*- coding: utf-8 -*-
"""AI Agent - escalation, unresolved topics, missed action items, reminders."""

from backend.app.llm import llm_call
from backend.app.services.action_item_service import extract_action_items
from backend.app.kafka.producer import send_alert
from backend.app.utils.logger import get_logger

logger = get_logger(__name__)


class MeetingAgent:

    def __init__(self, meeting_id: str, transcript: str):
        self.meeting_id = meeting_id
        self.transcript = transcript

    def needs_escalation(self) -> dict:
        prompt = f"""You are a meeting intelligence agent.
Read this transcript and decide if it needs escalation to senior management.
Escalate if: critical blockers unresolved, deadlines at risk, conflicts present, security issues.

Reply ONLY:
ESCALATE: YES or NO
REASON: one sentence

Transcript:
{self.transcript[:2000]}
"""
        response = llm_call(prompt=prompt, context="")
        escalate = "YES" in response.upper()
        reason = response.split("REASON:")[-1].strip() if "REASON:" in response else response
        if escalate:
            send_alert(self.meeting_id, "escalation_required", reason)
        return {"escalate": escalate, "reason": reason}

    def find_unresolved(self) -> list:
        prompt = f"""Identify topics DISCUSSED but NOT RESOLVED in this transcript.
Return a bullet list. If all resolved, return "None".

Transcript:
{self.transcript[:2000]}
"""
        response = llm_call(prompt=prompt, context="")
        lines = [
            line.strip().lstrip("-* ")
            for line in response.splitlines()
            if line.strip() and line.strip().lower() != "none"
        ]
        return lines

    def detect_missed_action_items(self) -> list:
        items = extract_action_items(self.transcript)
        return [i for i in items if i.get("owner", "Not specified").lower() in ("not specified", "", "unknown")]

    def generate_reminders(self, action_items: list) -> str:
        if not action_items:
            return "No open action items to remind about."
        items_text = "\n".join(
            f"- {i.get('task')} (Owner: {i.get('owner')}, Due: {i.get('deadline')})"
            for i in action_items
        )
        return llm_call(
            prompt=f"Write a friendly reminder for these action items (under 100 words):\n{items_text}",
            context=""
        )

    def prioritise_follow_ups(self, action_items: list) -> list:
        urgent = {"urgent", "critical", "asap", "today", "tomorrow", "immediately"}
        return sorted(action_items, key=lambda i: 0 if any(
            kw in (i.get("task", "") + i.get("deadline", "")).lower() for kw in urgent
        ) else 1)

    def run(self) -> dict:
        logger.info(f"Running agent for meeting '{self.meeting_id}'")
        escalation = self.needs_escalation()
        unresolved = self.find_unresolved()
        missed = self.detect_missed_action_items()
        all_items = extract_action_items(self.transcript)
        prioritised = self.prioritise_follow_ups(all_items)
        reminder = self.generate_reminders(missed or all_items[:3])
        return {
            "meeting_id": self.meeting_id,
            "escalation": escalation,
            "unresolved_discussions": unresolved,
            "missed_action_items": missed,
            "prioritised_action_items": prioritised,
            "reminder_message": reminder,
        }
