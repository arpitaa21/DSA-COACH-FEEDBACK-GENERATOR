"""
rag/ingestion.py
-----------------
The pipeline entrypoint: loaders -> chunking -> embeddings -> indexing.

Run it directly to (re)build the local vector index from the knowledge base:

    cd backend
    python -m rag.ingestion

Or call `run_ingestion()` programmatically (used by the /api/rag/ingest
endpoint in main.py).
"""

import time

from dotenv import load_dotenv
load_dotenv()

from .loaders import load_documents, load_all_sources
from .chunking import chunk_documents
from .embeddings import embed_texts
from .indexing import VectorIndex


def run_ingestion(source_dir: str | None = None, index_path: str | None = None) -> dict:
    """Runs the full ingestion pipeline and persists the resulting index.

    If `source_dir` is given, only that single directory is loaded (handy for
    testing one source in isolation). Otherwise, every source listed in
    config/tools.yaml's `rag_retrieval.data_sources` is loaded and combined -
    the knowledge base markdown, plus any PDFs dropped into
    rag/data/pdf/tech_interview_handbook/ or rag/data/pdf/neetcode_leetcode/.

    Returns a small stats dict so callers (CLI, API endpoint) can report what
    happened without re-deriving it themselves.
    """
    started_at = time.time()

    documents = load_documents(source_dir) if source_dir else load_all_sources()
    if not documents:
        raise RuntimeError("No documents found to ingest - check the knowledge base directory.")

    chunks = chunk_documents(documents)
    if not chunks:
        raise RuntimeError("Documents loaded, but chunking produced zero chunks.")

    vectors = embed_texts([c.text for c in chunks])

    index = VectorIndex()
    index.add(chunks, vectors)
    saved_path = index.save(index_path)

    return {
        "documents_ingested": len(documents),
        "chunks_created": len(chunks),
        "vectors_embedded": len(vectors),
        "index_path": str(saved_path),
        "seconds_elapsed": round(time.time() - started_at, 2),
        "sources": [d.source for d in documents],
    }


if __name__ == "__main__":
    stats = run_ingestion()
    print("RAG ingestion complete:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
