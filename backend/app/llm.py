"""
LLM wrapper using Groq (llama3-8b-8192).
All callers use:  llm_call(prompt, context="")
"""

import os
from groq import Groq
from dotenv import load_dotenv

from backend.app.utils.logger import get_logger

logger = get_logger(__name__)

# Try loading .env from backend/ folder (one level up from app/)
_APP_DIR = os.path.dirname(os.path.abspath(__file__))
_BACKEND_DIR = os.path.dirname(_APP_DIR)
load_dotenv(os.path.join(_BACKEND_DIR, ".env"))
load_dotenv()  # also try cwd as fallback

_client: Groq | None = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        api_key = os.getenv("GROQ_API_KEY", "")
        if not api_key:
            raise ValueError("GROQ_API_KEY is not set in .env")
        _client = Groq(api_key=api_key)
        logger.info("Groq client initialised.")
    return _client


def llm_call(prompt: str, context: str = "") -> str:
    """
    Call the LLM with an optional context block prepended to the prompt.

    Args:
        prompt:  The main instruction / question.
        context: Optional retrieved context (RAG chunks, etc.).

    Returns:
        The model's text response.
    """
    client = _get_client()

    full_prompt = prompt
    if context:
        full_prompt = f"Context:\n{context}\n\n{prompt}"

    try:
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": full_prompt}],
            temperature=0.3,
            max_tokens=1024,
        )
        return response.choices[0].message.content
    except Exception as exc:
        logger.error(f"LLM call failed: {exc}")
        raise
