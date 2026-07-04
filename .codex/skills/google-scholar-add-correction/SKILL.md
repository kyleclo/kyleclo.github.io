---
name: google-scholar-add-correction
description: Run bounded Google Scholar Add Articles corrections in this repo. Use when Codex has a reviewed Add Articles candidate doc_id and needs to dry-run or execute adding one missing or under-clustered paper through the logged-in Scholar UI with exact title checks, explicit confirmation, and pre/post evidence capture.
---

# Google Scholar Add Correction

## Scope

Use this skill only for one reviewed Add Articles candidate at a time. Use `google-scholar-hygiene` first to collect and review evidence.

Primary script:

- `scripts/mutate_scholar_add_articles.py`

Supporting commands:

- `scripts/scholar_hygiene.py evidence add-articles`
- `scripts/run_scholar_add_articles_scan.py`

## Safety

- Mutate only after a specific `doc_id` has been reviewed from Add Articles evidence.
- Dry-run first. Execute only after the dry-run identifies exactly one visible row and prints the expected confirmation phrase.
- Use exact title checks whenever a title is available.
- Use an isolated Chrome session for add corrections, conventionally port `9223` and profile `/tmp/chrome-scholar-002`.
- Do not run live Scholar mutations concurrently with merge automation or another Scholar worktree.
- Do not use network requests or hidden APIs. The helper must act through the visible Scholar UI over CDP.
- Keep pre/post raw artifacts in `_local/scholar_ui/` unless intentionally curating a small evidence artifact for the repo.

## Workflow

Review the current add-articles evidence:

```bash
uv run scripts/scholar_hygiene.py evidence add-articles --status not-in-profile --limit 20
uv run scripts/scholar_hygiene.py review
```

Ask the user to launch an isolated logged-in Chrome session:

```bash
open -na "Google Chrome" --args \
  --remote-debugging-port=9223 \
  --user-data-dir=/tmp/chrome-scholar-002
```

Dry-run the reviewed candidate. Include `--query` when the helper should open/search the Add Articles modal from the profile page:

```bash
env UV_CACHE_DIR=/tmp/uv-cache uv run scripts/mutate_scholar_add_articles.py \
  --cdp-url http://127.0.0.1:9223 \
  --doc-id DOC_ID \
  --title "Exact reviewed title" \
  --query "Reviewed query"
```

If the dry-run proves the row and the operator approves, execute the same candidate with the exact confirmation phrase:

```bash
env UV_CACHE_DIR=/tmp/uv-cache uv run scripts/mutate_scholar_add_articles.py \
  --cdp-url http://127.0.0.1:9223 \
  --doc-id DOC_ID \
  --title "Exact reviewed title" \
  --query "Reviewed query" \
  --execute \
  --confirm "ADD DOC_ID"
```

Refresh evidence after any live add:

```bash
env UV_CACHE_DIR=/tmp/uv-cache uv run scripts/run_scholar_add_articles_scan.py \
  plans/artifacts/scholar_ui/curated_queries.txt \
  --cdp-url http://127.0.0.1:9223
uv run scripts/scholar_hygiene.py detect
uv run scripts/scholar_hygiene.py review
```

## Stop Conditions

Stop without executing when the candidate is missing, duplicated, disabled, title-mismatched, already marked `in profile`, or when the Add button stays disabled. Stop on CAPTCHA, unexpected navigation, modal state drift, or any mismatch between the reviewed evidence and visible UI.
