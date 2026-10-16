"""
rag/embeddings.py
------------------
Turns text into vectors using Gemini's embedding model, so the RAG pipeline
uses the same GEMINI_API_KEY as the Code Exec Agent - no separate embedding
provider or extra API key to manage.
"""

import os
import time

import google.generativeai as genai
from config_loader import load_tools_config

try:
    _DEFAULT_EMBEDDING_MODEL = load_tools_config().get("rag_retrieval", {}).get(
        "embedding_model", "models/gemini-embedding-001"
    )
except Exception:
    _DEFAULT_EMBEDDING_MODEL = "models/gemini-embedding-001"

EMBEDDING_MODEL = os.getenv("RAG_EMBEDDING_MODEL", _DEFAULT_EMBEDDING_MODEL)

# gemini-embedding-001 returns 3072-dim vectors by default (it supports scaling
# down via Matryoshka Representation Learning, but we keep the default here
# for simplicity). This constant is informational only - indexing.py doesn't
# hardcode a dimension, it just uses whatever length comes back.
EMBEDDING_DIM = 3072

_MAX_RETRIES = 3
_RETRY_DELAY_SECONDS = 2


def _configure_gemini():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Copy backend/.env.example to backend/.env "
            "and add your Gemini API key before running RAG ingestion."
        )
    genai.configure(api_key=api_key)


def _embed_one(text: str, task_type: str) -> list[float]:
    last_error = None
    for attempt in range(_MAX_RETRIES):
        try:
            result = genai.embed_content(model=EMBEDDING_MODEL, content=text, task_type=task_type)
            return result["embedding"]
        except Exception as exc:  # rate limits / transient network errors
            last_error = exc
            if attempt < _MAX_RETRIES - 1:
                time.sleep(_RETRY_DELAY_SECONDS * (attempt + 1))
    raise RuntimeError(f"Embedding call failed after {_MAX_RETRIES} attempts: {last_error}")


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embeds a batch of chunk texts for indexing (task_type='retrieval_document'
    tells the model these are documents to be searched over, not the search
    query itself - Gemini's embeddings are asymmetric between the two)."""
    _configure_gemini()
    return [_embed_one(t, task_type="retrieval_document") for t in texts]


def embed_query(text: str) -> list[float]:
    """Embeds a single search query (task_type='retrieval_query')."""
    _configure_gemini()
    return _embed_one(text, task_type="retrieval_query")
