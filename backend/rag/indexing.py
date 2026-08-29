"""
rag/indexing.py
----------------
Stores chunk vectors and does cosine-similarity search over them.

Deliberately NOT FAISS/Chroma/Pinecone: for a knowledge base this small (a
few dozen chunks), a plain numpy matrix is fast enough, has zero extra
services to run, and avoids piling more native-dependency install risk onto
a Windows setup that already had to fight numpy once during this project
(see the earlier Python-version issue). Swap in FAISS/Chroma later behind
this same VectorIndex interface if the knowledge base grows large.
"""

import json
from dataclasses import asdict
from pathlib import Path

import numpy as np

from .chunking import Chunk

DEFAULT_INDEX_PATH = Path(__file__).parent / "data" / "index" / "index.json"


class VectorIndex:
    def __init__(self):
        self._chunks: list[Chunk] = []
        self._vectors: np.ndarray | None = None  # shape: (n_chunks, dim), L2-normalized

    def add(self, chunks: list[Chunk], vectors: list[list[float]]) -> None:
        if len(chunks) != len(vectors):
            raise ValueError("chunks and vectors must be the same length")
        if not chunks:
            return

        arr = np.array(vectors, dtype=np.float32)
        norms = np.linalg.norm(arr, axis=1, keepdims=True)
        norms[norms == 0] = 1.0  # avoid divide-by-zero on a degenerate embedding
        arr = arr / norms

        self._chunks.extend(chunks)
        self._vectors = arr if self._vectors is None else np.vstack([self._vectors, arr])

    def search(self, query_vector: list[float], top_k: int = 5) -> list[dict]:
        """Returns the top_k most similar chunks as
        [{"chunk": Chunk, "score": cosine_similarity}, ...], highest score first."""
        if self._vectors is None or len(self._chunks) == 0:
            return []

        q = np.array(query_vector, dtype=np.float32)
        q_norm = np.linalg.norm(q)
        if q_norm == 0:
            return []
        q = q / q_norm

        scores = self._vectors @ q  # cosine similarity, since both sides are unit-normalized
        top_k = min(top_k, len(self._chunks))
        top_indices = np.argsort(-scores)[:top_k]

        return [{"chunk": self._chunks[i], "score": float(scores[i])} for i in top_indices]

    def __len__(self) -> int:
        return len(self._chunks)

    # -- persistence -----------------------------------------------------
    def save(self, path: str | Path | None = None) -> Path:
        path = Path(path) if path else DEFAULT_INDEX_PATH
        path.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "chunks": [asdict(c) for c in self._chunks],
            "vectors": self._vectors.tolist() if self._vectors is not None else [],
        }
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    @classmethod
    def load(cls, path: str | Path | None = None) -> "VectorIndex":
        path = Path(path) if path else DEFAULT_INDEX_PATH
        if not path.exists():
            raise FileNotFoundError(
                f"No index found at {path}. Run ingestion first: "
                f"`python -m rag.ingestion` from the backend/ directory."
            )

        payload = json.loads(path.read_text(encoding="utf-8"))
        index = cls()
        chunks = [Chunk(**c) for c in payload["chunks"]]
        vectors = payload["vectors"]
        index.add(chunks, vectors)
        return index
