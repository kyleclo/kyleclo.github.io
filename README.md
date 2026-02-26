# kyleclo.com

Personal academic website for Kyle Lo, built with [Jekyll](https://jekyllrb.com/) and based on the [al-folio](https://github.com/alshedivat/al-folio) theme.

## Development

```bash
make docker-build   # build the Docker image
make docker-up      # start local dev server at localhost:8080
```

## Bibliography

See `_bibliography/BIB.md` for formatting rules. Key scripts:

```bash
uv run scripts/1_scrape_google_scholar.py   # pull from Google Scholar
uv run scripts/get_pdfs.py                  # download PDFs
uv run scripts/get_paper_thumbnails.py      # generate thumbnails
python scripts/generate_cv.py               # regenerate CV
```
