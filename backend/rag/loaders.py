"""
rag/loaders.py
---------------
Loads raw documents into a common shape before chunking/embedding.

Two source types are supported, both producing the same `Document` shape:
  - markdown/text files (the hand-written DSA knowledge base)
  - PDFs (e.g. your own Tech Interview Handbook / NeetCode exports - see
    backend/rag/data/pdf/*/README.md; these folders are empty by default
    since that content is copyrighted and isn't bundled in this repo)

`load_all_sources()` reads the source manifest from backend/config/tools.yaml
(`rag_retrieval.data_sources`) and loads every listed source automatically -
that's what `rag/ingestion.py` calls by default. Web/GitHub loaders would
follow the same `Document` shape and could be added the same way later.
"""

from dataclasses import dataclass
from pathlib import Path

from config_loader import load_tools_config

BACKEND_DIR = Path(__file__).parent.parent
DEFAULT_KNOWLEDGE_BASE_DIR = Path(__file__).parent / "data" / "knowledge_base"
SUPPORTED_TEXT_EXTENSIONS = {".md", ".txt"}


@dataclass
class Document:
    doc_id: str          # stable id, derived from filename
    source: str          # human-readable source (file path/name)
    title: str           # first heading or filename, used in citations/UI
    text: str            # raw text content


def _derive_title(text: str, fallback: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("#"):
            return line.lstrip("#").strip()
        if line:
            return line[:80]
    return fallback


def load_documents(source_dir: str | Path | None = None) -> list[Document]:
    """Loads every .md/.txt file in `source_dir` (default: the bundled DSA
    knowledge base) into a list of Documents, sorted by filename for
    reproducible ingestion runs."""
    directory = Path(source_dir) if source_dir else DEFAULT_KNOWLEDGE_BASE_DIR
    if not directory.exists():
        raise FileNotFoundError(f"Knowledge base directory not found: {directory}")

    documents: list[Document] = []
    for path in sorted(directory.iterdir()):
        if path.suffix.lower() not in SUPPORTED_TEXT_EXTENSIONS:
            continue
        text = path.read_text(encoding="utf-8").strip()
        if not text:
            continue
        doc_id = path.stem
        documents.append(
            Document(
                doc_id=doc_id,
                source=path.name,
                title=_derive_title(text, fallback=doc_id.replace("-", " ").title()),
                text=text,
            )
        )
    return documents


def load_pdf_documents(source_dir: str | Path) -> list[Document]:
    """Loads every .pdf in `source_dir`, extracting text page by page. Returns
    an empty list (not an error) if the directory doesn't exist or has no
    PDFs yet - the bundled PDF folders are empty by default (see their
    README.md), so an empty result here is the expected common case, not a
    failure."""
    directory = Path(source_dir)
    if not directory.exists():
        return []

    pdf_paths = sorted(directory.glob("*.pdf"))
    if not pdf_paths:
        return []

    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise ImportError(
            "pypdf is required to load PDF sources - install it with "
            "`pip install pypdf` (already in backend/requirements.txt)."
        ) from exc

    documents: list[Document] = []
    for path in pdf_paths:
        reader = PdfReader(str(path))
        pages_text = [page.extract_text() or "" for page in reader.pages]
        text = "\n\n".join(p.strip() for p in pages_text if p.strip()).strip()
        if not text:
            continue
        documents.append(
            Document(
                doc_id=f"pdf-{path.stem}",
                source=path.name,
                title=_derive_title(text, fallback=path.stem.replace("-", " ").replace("_", " ").title()),
                text=text,
            )
        )
    return documents


def load_all_sources() -> list[Document]:
    """Reads the data-source manifest from config/tools.yaml
    (`rag_retrieval.data_sources`) and loads every listed source, dispatching
    to load_documents() for type "markdown" and load_pdf_documents() for
    type "pdf". This is what ingestion.py calls by default."""
    cfg = load_tools_config().get("rag_retrieval", {})
    sources = cfg.get("data_sources", [])
    if not sources:
        # no manifest configured - fall back to just the bundled knowledge base
        return load_documents()

    documents: list[Document] = []
    for source in sources:
        path = BACKEND_DIR / source["path"]
        source_type = source.get("type", "markdown")
        if source_type == "pdf":
            documents.extend(load_pdf_documents(path))
        else:
            try:
                documents.extend(load_documents(path))
            except FileNotFoundError:
                continue  # a listed markdown source dir doesn't exist yet - skip, don't crash ingestion
    return documents


def load_from_text(text: str, doc_id: str, title: str | None = None, source: str = "inline") -> Document:
    """Convenience helper for loading a single in-memory string as a Document -
    useful for tests, or for ingesting content that didn't come from a file."""
    return Document(doc_id=doc_id, source=source, title=title or doc_id, text=text.strip())
