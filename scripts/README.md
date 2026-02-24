# Scripts

## Bibliography Workflow

### 1. Scrape Google Scholar

```bash
uv run scripts/1_scrape_google_scholar.py
```

Fetches papers from Google Scholar and saves to `_bibliography/gscholar_export.db`.

### 2. Check Paper Quality

```bash
uv run scripts/2_check_paper_quality.py
```

Generates `_bibliography/quality_report.html` with duplicate detection, missing fields, etc.

### 3. Download PDFs and Thumbnails

```bash
uv run scripts/get_pdfs.py
uv run scripts/get_paper_thumbnails.py
```

Downloads PDFs to `assets/pdf/` and generates preview thumbnails in `assets/img/publication_preview/`.

### 4. Screenshot HF Dataset Cards

```bash
uv run scripts/screenshot_hf_dataset.py
```

Uses Playwright to screenshot a Hugging Face dataset card for entries without a traditional PDF. Requires `uv run playwright install chromium` first.

## CV Generation

```bash
python scripts/generate_cv.py              # generate and push to Overleaf
python scripts/generate_cv.py --short      # short (industry) CV
python scripts/generate_cv.py --dry-run    # preview without writing
python scripts/generate_cv.py --local-only # write locally, no push
```

Generates `publications.tex` from `papers.bib` and pushes to the Overleaf CV project.

## Utilities

- `scripts/sort_bib.py` — Sort `papers.bib` in reverse chronological order
- `scripts/sort_news_articles.py` — Renumber news article files
- `scripts/inspect_papers_db.sh` — Print summary of the Google Scholar SQLite DB
- `scripts/check_file_sizes.py` — Check for oversized files in the repo
