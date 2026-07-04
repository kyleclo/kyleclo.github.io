---
name: google-scholar-hygiene
description: Collect and review Google Scholar profile hygiene evidence in this repo. Use when Codex needs to refresh or inspect the Scholar SQLite export, run the scholar_hygiene detector or review commands, capture logged-in read-only Scholar UI evidence over Playwright/CDP, scan Add Articles queries, or reason about missing-paper and under-clustered-profile evidence before any correction.
---

# Google Scholar Hygiene

## Scope

Use this skill for read-only Google Scholar evidence collection and review in this repository. Use the separate add-correction or merge-correction skills for account mutations.

Primary scripts:

- `scripts/1_scrape_google_scholar.py`
- `scripts/scholar_hygiene.py`
- `scripts/investigate_scholar_ui.py`
- `scripts/run_scholar_add_articles_scan.py`

## Safety

- Treat direct `scholarly` scraping as best-effort. If Google returns CAPTCHA or anti-bot friction, stop and use the logged-in browser evidence path instead.
- For browser evidence, attach to a human-opened Chrome session over CDP. Do not automate Google login.
- Keep Scholar use low-rate, headful, and human-supervised. Use one tab by default and stop on CAPTCHA, redirects, selector instability, or unusual UI behavior.
- Do not click Add, Merge, Save, Delete, or confirmation controls in this skill.
- Keep raw screenshots, HTML, and parsed modal captures in `_local/scholar_ui/` unless deliberately curating a small reference artifact for the repo.

## Evidence Workflow

Start by checking the local state:

```bash
git status --short --branch
uv run scripts/scholar_hygiene.py review
uv run scripts/scholar_hygiene.py evidence add-articles --status not-in-profile --limit 20
```

Refresh the scraper-backed database when direct scraping is still viable:

```bash
uv run scripts/1_scrape_google_scholar.py
uv run scripts/scholar_hygiene.py refresh --coauthors
uv run scripts/scholar_hygiene.py detect
uv run scripts/scholar_hygiene.py review
```

If direct scraping is blocked, use the logged-in UI path. Ask the user to launch Chrome with remote debugging and log into Scholar:

```bash
open -na "Google Chrome" --args \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome-scholar-readonly
```

Capture the already-open Scholar tab:

```bash
env UV_CACHE_DIR=/tmp/uv-cache uv run scripts/investigate_scholar_ui.py \
  --cdp-url http://127.0.0.1:9222 \
  --use-existing-page \
  --capture-current-page \
  --parse-add-articles
```

Run bounded curated Add Articles scans from a query file:

```bash
env UV_CACHE_DIR=/tmp/uv-cache uv run scripts/run_scholar_add_articles_scan.py \
  plans/artifacts/scholar_ui/curated_queries.txt \
  --cdp-url http://127.0.0.1:9222
```

After any new evidence capture, rerun detection and inspect issues:

```bash
uv run scripts/scholar_hygiene.py detect
uv run scripts/scholar_hygiene.py review
uv run scripts/scholar_hygiene.py evidence add-articles --status not-in-profile --limit 20
```

## Outputs

Structured outputs live under `_bibliography/`:

- `gscholar_export.db`
- `scholar_issues.json`
- `scholar_issues.csv`
- `scholar_state.json`

Read-only UI artifacts default to `_local/scholar_ui/`. Commit only concise notes, query lists, or deliberately curated evidence under `plans/artifacts/scholar_ui/`.
