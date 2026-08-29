# Tech Interview Handbook PDFs

This folder is intentionally empty in the repo.

[Tech Interview Handbook](https://www.techinterviewhandbook.org/) is a
community resource with its own license/attribution terms - its content isn't
bundled here. To use it as a RAG source:

1. Export or save the pages/sections you have the right to use as PDF(s).
2. Drop the PDF file(s) directly into this folder.
3. Re-run ingestion from `backend/`:
   ```
   python -m rag.ingestion
   ```

`rag/loaders.py` will pick up any `.pdf` file placed here automatically (see
the `pdf` entry for this folder in `backend/config/tools.yaml`).
