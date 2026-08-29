"""
rag/
----
DSA Coach - Mind Matrix (GENAICH-010)

A small, self-contained retrieval-augmented pipeline that ingests a local DSA
"knowledge base" (pattern write-ups: two pointers, sliding window, DP, ...),
chunks it, embeds it with Gemini, indexes it in a lightweight local vector
store, and evaluates retrieval quality.

Scope note: this package intentionally contains only the ingestion/indexing
side of RAG - loaders, chunking, embeddings, indexing, ingestion, evaluation.
It does NOT include a retriever/hybrid_retriever/reranker/generator/prompts
layer that would wire retrieval into the Code Exec Agent's live feedback
generation - that's a deliberately separate, not-yet-built piece.

Typical flow:

    from rag.ingestion import run_ingestion
    from rag.evaluation import evaluate_retrieval

    stats = run_ingestion()          # loaders -> chunking -> embeddings -> indexing
    report = evaluate_retrieval()    # sanity-checks retrieval quality against a small gold set
"""

from .loaders import load_documents, load_all_sources
from .chunking import chunk_documents
from .embeddings import embed_texts, embed_query
from .indexing import VectorIndex
from .ingestion import run_ingestion
from .evaluation import evaluate_retrieval

__all__ = [
    "load_documents",
    "load_all_sources",
    "chunk_documents",
    "embed_texts",
    "embed_query",
    "VectorIndex",
    "run_ingestion",
    "evaluate_retrieval",
]
