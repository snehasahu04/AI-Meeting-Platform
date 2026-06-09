"""
Database layer using Python's built-in sqlite3.
No SQLAlchemy — works on Python 3.13 without issues.
"""

import sqlite3
import os
from datetime import datetime

# DB file lives in the backend/ folder
_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "meeting_platform.db")


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row   # rows behave like dicts
    return conn


def init_db():
    """Create all tables if they don't exist."""
    conn = get_conn()
    c = conn.cursor()

    c.executescript("""
        CREATE TABLE IF NOT EXISTS meetings (
            id TEXT PRIMARY KEY,
            title TEXT,
            status TEXT DEFAULT 'processing',
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS meeting_transcripts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meeting_id TEXT,
            chunk_index INTEGER DEFAULT 0,
            text TEXT,
            speaker TEXT,
            sentiment_score REAL,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS meeting_summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meeting_id TEXT,
            summary_text TEXT,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS meeting_action_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meeting_id TEXT,
            task TEXT,
            owner TEXT,
            deadline TEXT,
            status TEXT DEFAULT 'open',
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS meeting_speakers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meeting_id TEXT,
            speaker_name TEXT,
            speaking_time_seconds REAL DEFAULT 0,
            word_count INTEGER DEFAULT 0,
            sentiment_avg REAL,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS meeting_embeddings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meeting_id TEXT,
            chunk_id INTEGER,
            chunk_text TEXT,
            faiss_index INTEGER,
            created_at TEXT
        );
    """)

    conn.commit()
    conn.close()


# ── Helper functions ──────────────────────────────────────────────────────────

def insert_meeting(meeting_id: str, title: str, status: str = "processing"):
    conn = get_conn()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO meetings (id, title, status, created_at) VALUES (?, ?, ?, ?)",
            (meeting_id, title, status, datetime.utcnow().isoformat())
        )
        conn.commit()
    finally:
        conn.close()


def insert_transcript_chunks(meeting_id: str, chunks: list[str]):
    conn = get_conn()
    try:
        now = datetime.utcnow().isoformat()
        conn.executemany(
            "INSERT INTO meeting_transcripts (meeting_id, chunk_index, text, created_at) VALUES (?, ?, ?, ?)",
            [(meeting_id, i, chunk, now) for i, chunk in enumerate(chunks)]
        )
        conn.commit()
    finally:
        conn.close()


def get_meeting(meeting_id: str) -> dict | None:
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM meetings WHERE id = ?", (meeting_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_all_meetings() -> list[dict]:
    conn = get_conn()
    try:
        rows = conn.execute("SELECT * FROM meetings ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_transcript_chunks(meeting_id: str) -> list[dict]:
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM meeting_transcripts WHERE meeting_id = ? ORDER BY chunk_index",
            (meeting_id,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_full_transcript(meeting_id: str) -> str:
    chunks = get_transcript_chunks(meeting_id)
    return " ".join(c["text"] for c in chunks)


def get_chunk_count(meeting_id: str) -> int:
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM meeting_transcripts WHERE meeting_id = ?",
            (meeting_id,)
        ).fetchone()
        return row["cnt"] if row else 0
    finally:
        conn.close()


def save_summary(meeting_id: str, summary_text: str):
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO meeting_summaries (meeting_id, summary_text, created_at) VALUES (?, ?, ?)",
            (meeting_id, summary_text, datetime.utcnow().isoformat())
        )
        conn.commit()
    finally:
        conn.close()


def get_summary(meeting_id: str) -> str | None:
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT summary_text FROM meeting_summaries WHERE meeting_id = ? ORDER BY id DESC LIMIT 1",
            (meeting_id,)
        ).fetchone()
        return row["summary_text"] if row else None
    finally:
        conn.close()


def save_action_items(meeting_id: str, items: list[dict]):
    conn = get_conn()
    try:
        now = datetime.utcnow().isoformat()
        conn.executemany(
            "INSERT INTO meeting_action_items (meeting_id, task, owner, deadline, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            [(meeting_id, i.get("task", ""), i.get("owner", ""), i.get("deadline", ""), i.get("status", "open"), now)
             for i in items]
        )
        conn.commit()
    finally:
        conn.close()


def get_action_items(meeting_id: str) -> list[dict]:
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT task, owner, deadline, status FROM meeting_action_items WHERE meeting_id = ?",
            (meeting_id,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_total_chunks() -> int:
    conn = get_conn()
    try:
        row = conn.execute("SELECT COUNT(*) as cnt FROM meeting_transcripts").fetchone()
        return row["cnt"] if row else 0
    finally:
        conn.close()


def get_total_meetings() -> int:
    conn = get_conn()
    try:
        row = conn.execute("SELECT COUNT(*) as cnt FROM meetings").fetchone()
        return row["cnt"] if row else 0
    finally:
        conn.close()
