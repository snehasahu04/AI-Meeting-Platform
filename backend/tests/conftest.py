"""
Shared pytest fixtures.
Run tests from the backend/ folder:
    cd backend
    pytest tests/ -v
"""

import sys
import os

# Make sure 'backend' is importable from either project root or backend/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


SAMPLE_TRANSCRIPT = """
Alice: Good morning everyone. Let's start with the Kafka consumer lag issue.
Bob: Yes, I noticed the lag increased by 200ms yesterday. We need to fix it by Friday.
Alice: Agreed. Bob, can you own that?
Bob: Sure. I'll also review the CI/CD pipeline.
Charlie: The Databricks cluster needs to be reviewed by DevOps.
Alice: Let's make sure the staging deployment is validated before the release.
Bob: I'll coordinate with the DevOps team on that.
Alice: Any blockers?
Charlie: The authentication service is still broken. It's critical.
Alice: That needs escalation. Let's wrap up.
"""
