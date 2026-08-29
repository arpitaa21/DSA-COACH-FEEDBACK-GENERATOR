"""
rag/chunking.py
----------------
Splits loaded Documents into overlapping chunks small enough to embed well
and retrieve precisely, while keeping enough context per chunk to be useful
on its own.

Strategy: split on paragraph/heading boundaries first (so we don't cut a
sentence in half), then greedily pack paragraphs into ~chunk_size-character
chunks with a small overlap between consecutive chunks so context isn't lost
at the boundary.
"""

import re
from dataclasses import dataclass

from .loaders import Document
from config_loader import load_tools_config

try:
    _rag_cfg = load_tools_config().get("rag_retrieval", {})
    DEFAULT_CHUNK_SIZE = int(_rag_cfg.get("chunk_size", 800))
    DEFAULT_CHUNK_OVERLAP = int(_rag_cfg.get("chunk_overlap", 120))
except Exception:
    DEFAULT_CHUNK_SIZE = 800     # characters, not tokens - simple and dependency-free
    DEFAULT_CHUNK_OVERLAP = 120


@dataclass
class Chunk:
    chunk_id: str        # f"{doc_id}::{index}"
    doc_id: str
    source: str
    title: str
    index: int            # position of this chunk within its source document
    text: str


def _split_into_paragraphs(text: str) -> list[str]:
    # Split on blank lines, keep headings attached to the paragraph that follows.
    raw_blocks = re.split(r"\n\s*\n", text.strip())
    return [b.strip() for b in raw_blocks if b.strip()]


def chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[str]:
    """Greedily packs paragraphs into chunks of roughly `chunk_size` characters,
    carrying `overlap` characters of trailing context into the next chunk."""
    paragraphs = _split_into_paragraphs(text)
    if not paragraphs:
        return []

    chunks: list[str] = []
    current = ""

    for para in paragraphs:
        candidate = f"{current}\n\n{para}".strip() if current else para

        if len(candidate) <= chunk_size:
            current = candidate
            continue

        # current chunk is full - flush it, start a new one carrying overlap forward
        if current:
            chunks.append(current)
            tail = current[-overlap:] if overlap else ""
            current = f"{tail}\n\n{para}".strip() if tail else para
        else:
            # a single paragraph longer than chunk_size - hard-split it
            for i in range(0, len(para), chunk_size - overlap):
                chunks.append(para[i : i + chunk_size])
            current = ""

    if current:
        chunks.append(current)

    return chunks


def chunk_documents(
    documents: list[Document],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[Chunk]:
    """Chunks every document in the list, returning a flat list of Chunks
    ready for embedding + indexing."""
    all_chunks: list[Chunk] = []
    for doc in documents:
        pieces = chunk_text(doc.text, chunk_size=chunk_size, overlap=overlap)
        for i, piece in enumerate(pieces):
            all_chunks.append(
                Chunk(
                    chunk_id=f"{doc.doc_id}::{i}",
                    doc_id=doc.doc_id,
                    source=doc.source,
                    title=doc.title,
                    index=i,
                    text=piece,
                )
            )
    return all_chunks
