## Bibliography

Before editing `_bibliography/papers.bib`, always read `_bibliography/BIB.md` for formatting rules and conventions.

Key commands:

- `uv run scripts/1_scrape_google_scholar.py` — pull latest from Google Scholar into SQLite DB
- `uv run scripts/get_pdfs.py` — download PDFs for papers
- `uv run scripts/get_paper_thumbnails.py` — generate preview thumbnails
- `python scripts/generate_cv.py` — regenerate CV and push to Overleaf
- `make docker-build` — build Jekyll site via Docker
- `make docker-up` — start Jekyll dev server via Docker
