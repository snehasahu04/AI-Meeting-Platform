"""
API endpoint tests.
Run from backend/ folder: pytest tests/test_api.py -v
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.conftest import SAMPLE_TRANSCRIPT


def test_health(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

def test_ingest_text(client):
    resp = client.post("/ingest/text", json={
        "meeting_id": "test-001",
        "transcript": SAMPLE_TRANSCRIPT,
    })
    assert resp.status_code == 200
    assert resp.json()["meeting_id"] == "test-001"

def test_ingest_text_empty(client):
    resp = client.post("/ingest/text", json={"transcript": ""})
    assert resp.status_code == 400

def test_list_meetings(client):
    resp = client.get("/meetings/")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)

def test_get_meeting_not_found(client):
    resp = client.get("/meetings/nonexistent-id-xyz")
    assert resp.status_code == 404

def test_analytics_overview(client):
    resp = client.get("/analytics/overview")
    assert resp.status_code == 200
    assert "total_meetings" in resp.json()

def test_rag_search(client):
    client.post("/ingest/text", json={
        "meeting_id": "test-rag-001",
        "transcript": SAMPLE_TRANSCRIPT,
    })
    resp = client.post("/rag/search", json={"query": "Kafka consumer lag", "top_k": 3})
    assert resp.status_code == 200
    assert "results" in resp.json()

def test_rag_ask_empty(client):
    resp = client.post("/rag/ask", json={"query": ""})
    assert resp.status_code == 400
