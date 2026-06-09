"""
Run this file from the meeting_AI_platform root folder:
    python backend/run.py
OR from inside the backend folder:
    python run.py

It adds the project root to sys.path so 'backend.*' imports resolve correctly.
"""
import sys
import os

# Add the parent of 'backend' to sys.path so 'import backend.app...' works
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[os.path.join(ROOT, "backend")],
    )
