---
name: google-scholar-merge-correction
description: Run bounded Google Scholar merge corrections in this repo. Use when Codex needs to review, approve, dry-run, or execute one Google Scholar profile merge family with exact row ids, exact title checks, queue state, explicit confirmation, and pre/post evidence capture.
---

# Google Scholar Merge Correction

## Scope

Use this skill for reviewed Google Scholar profile-row merges. It is intentionally stricter than Add Articles correction because prior live batch execution caused page-state drift.

Primary scripts:

- `scripts/discover_scholar_merge_queue.py`
- `scripts/review_scholar_merge_queue.py`
- `scripts/run_next_scholar_merge_queue_item.py`
- `scripts/run_batch_scholar_merge_queue.py`
- `scripts/mutate_scholar_merge_family.py`

## Safety

- Live execution is one reviewed family at a time.
- Batch review and batch dry-run are allowed. Live batch execution is disabled and must stay disabled.
- Use exact Scholar row ids plus exact title checks before any mutation.
- Dry-run before live execution.
- Use an isolated Chrome session for merge corrections, conventionally port `9224` and profile `/tmp/chrome-scholar-003`.
- Do not share the Chrome session with Add Articles correction or another Scholar worktree.
- Treat `Scim` as a known semantic false positive family. Do not merge it without fresh explicit review.
- Treat `Dolma` / `CORD-19` batch state drift as the reason live batching remains forbidden.

## Queue Workflow

Ask the user to launch an isolated logged-in Chrome session:

```bash
open -na "Google Chrome" --args \
  --remote-debugging-port=9224 \
  --user-data-dir=/tmp/chrome-scholar-003
```

Start with the existing queue:

```bash
python3 scripts/review_scholar_merge_queue.py \
  --queue-file plans/artifacts/scholar_ui/merge_queue.json \
  list --triage --limit 20
```

Inspect one item before changing its status:

```bash
python3 scripts/review_scholar_merge_queue.py \
  --queue-file plans/artifacts/scholar_ui/merge_queue.json \
  show --id "QUEUE_ITEM_ID"
```

Approve only one reviewed family at a time:

```bash
python3 scripts/review_scholar_merge_queue.py \
  --queue-file plans/artifacts/scholar_ui/merge_queue.json \
  update --id "QUEUE_ITEM_ID" --status approved --note "Reviewed exact duplicate family"
```

Dry-run the next approved item:

```bash
env UV_CACHE_DIR=/tmp/uv-cache uv run scripts/run_next_scholar_merge_queue_item.py \
  --cdp-url http://127.0.0.1:9224 \
  --queue-file plans/artifacts/scholar_ui/merge_queue.json
```

Execute exactly one approved item only after the dry-run succeeds:

```bash
env UV_CACHE_DIR=/tmp/uv-cache uv run scripts/run_next_scholar_merge_queue_item.py \
  --cdp-url http://127.0.0.1:9224 \
  --queue-file plans/artifacts/scholar_ui/merge_queue.json \
  --execute
```

Use batch mode for dry-run preview only:

```bash
env UV_CACHE_DIR=/tmp/uv-cache uv run scripts/run_batch_scholar_merge_queue.py \
  --cdp-url http://127.0.0.1:9224 \
  --queue-file plans/artifacts/scholar_ui/merge_queue.json
```

## Discovery

Rediscover only when the existing queue is stale or insufficient. Discovery is read-only and may use bounded `Show more` expansion:

```bash
env UV_CACHE_DIR=/tmp/uv-cache uv run scripts/discover_scholar_merge_queue.py \
  --cdp-url http://127.0.0.1:9224 \
  --queue-file plans/artifacts/scholar_ui/merge_queue.json \
  --expand-show-more 1
```

## Direct Bounded Merge

For a hand-reviewed family outside the queue, dry-run the exact row ids and titles:

```bash
env UV_CACHE_DIR=/tmp/uv-cache uv run scripts/mutate_scholar_merge_family.py \
  --cdp-url http://127.0.0.1:9224 \
  --target "ROW_ID_1::Exact title 1" \
  --target "ROW_ID_2::Exact title 2"
```

Execute only with the exact confirmation phrase printed by dry-run:

```bash
env UV_CACHE_DIR=/tmp/uv-cache uv run scripts/mutate_scholar_merge_family.py \
  --cdp-url http://127.0.0.1:9224 \
  --target "ROW_ID_1::Exact title 1" \
  --target "ROW_ID_2::Exact title 2" \
  --execute \
  --confirm "MERGE ROW_ID_1 ROW_ID_2"
```

## Stop Conditions

Stop without executing when any reviewed row is missing, duplicated, disabled, or title-mismatched; when the primary merge button is absent or disabled; when Scholar shows an unexpected merge surface; when post-merge verification is ambiguous; or when visible page state has drifted after a previous live mutation.
