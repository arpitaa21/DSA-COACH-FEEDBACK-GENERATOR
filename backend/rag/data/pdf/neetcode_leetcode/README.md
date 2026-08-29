# NeetCode / LeetCode PDFs

This folder is intentionally empty in the repo.

Problem statements and editorial content from [NeetCode](https://neetcode.io/)
and [LeetCode](https://leetcode.com/) belong to their respective owners and
aren't bundled here. To use your own notes/exports as a RAG source:

1. Save your own PDF notes (e.g. personal pattern summaries, your own write-ups
   of problems you've solved) into this folder.
2. Re-run ingestion from `backend/`:
   ```
   python -m rag.ingestion
   ```

`rag/loaders.py` will pick up any `.pdf` file placed here automatically (see
the `pdf` entry for this folder in `backend/config/tools.yaml`).
