# 003 Merge Queue Progress / Resume Note

## Scope

This note records the current state of the `003` merge-automation effort so a later session can resume without rediscovering the operational details.

It originated in the `scholar-merge-automation` worktree and is now merged into `main`. This note is for the `003` merge workflow only.

## Operational Setup

Use an isolated Chrome instance for `003`.

Recommended launch:

```bash
open -na "Google Chrome" --args \
  --remote-debugging-port=9224 \
  --user-data-dir=/tmp/chrome-scholar-003
```

Rules:

- do not attach `003` automation to the `002` Chrome instance
- do not share CDP ports across worktrees
- do not run live Scholar mutations concurrently across worktrees / sessions

Current `003` CDP endpoint:

- `http://127.0.0.1:9224`

## What 003 Implemented

Main files added / updated:

- `plans/003_bounded_google_scholar_merge_automation.md`
- `plans/003_bounded_google_scholar_merge_automation_scaleout.md`
- `plans/artifacts/scholar_ui/bounded_merge_automation_summary_20260413.md`
- `scripts/mutate_scholar_merge_family.py`
- `scripts/scholar_merge_queue.py`
- `scripts/discover_scholar_merge_queue.py`
- `scripts/review_scholar_merge_queue.py`
- `scripts/run_next_scholar_merge_queue_item.py`
- `tests/test_mutate_scholar_merge_family.py`
- `tests/test_scholar_merge_queue.py`
- `tests/test_run_next_scholar_merge_queue_item.py`

## Validated Merge Flow

The real live Scholar merge flow validated in `003` is:

1. select reviewed profile rows by exact row id
2. click primary profile merge button:
   - `gsc_btn_mer`
3. Scholar opens a confirmation modal
4. click modal merge button:
   - `gsc_md_mopt_merge`
5. wait for observable profile-table change
6. perform read-only relisting for verification

Important behavior:

- stale merge confirmation modals can persist and must be dismissed before a new run
- `Show more` is acceptable as bounded read-only discovery
- exact row ids plus exact title checks are required guardrails

## Queue Workflow Now Available

The one-item queue workflow is implemented end to end:

1. discover candidate families
2. review queue items
3. approve one family
4. dry-run one approved item
5. execute one approved item live
6. perform read-only verification
7. persist result into the queue artifact

Queue artifact:

- `plans/artifacts/scholar_ui/merge_queue.json`

Useful commands:

Discover:

```bash
env UV_CACHE_DIR=/tmp/uv-cache uv run scripts/discover_scholar_merge_queue.py \
  --cdp-url http://127.0.0.1:9224 \
  --queue-file plans/artifacts/scholar_ui/merge_queue.json \
  --expand-show-more 1
```

Compact triage review:

```bash
python3 scripts/review_scholar_merge_queue.py \
  --queue-file plans/artifacts/scholar_ui/merge_queue.json \
  list --triage --limit 20
```

Show one item:

```bash
python3 scripts/review_scholar_merge_queue.py \
  --queue-file plans/artifacts/scholar_ui/merge_queue.json \
  show --id '<queue-item-id>'
```

Approve one item:

```bash
python3 scripts/review_scholar_merge_queue.py \
  --queue-file plans/artifacts/scholar_ui/merge_queue.json \
  update --id '<queue-item-id>' --status approved --note '<review note>'
```

Dry-run next approved item:

```bash
env UV_CACHE_DIR=/tmp/uv-cache uv run scripts/run_next_scholar_merge_queue_item.py \
  --cdp-url http://127.0.0.1:9224 \
  --queue-file plans/artifacts/scholar_ui/merge_queue.json
```

Execute next approved item live:

```bash
env UV_CACHE_DIR=/tmp/uv-cache uv run scripts/run_next_scholar_merge_queue_item.py \
  --cdp-url http://127.0.0.1:9224 \
  --queue-file plans/artifacts/scholar_ui/merge_queue.json \
  --execute
```

Batch dry-run approved items:

```bash
env UV_CACHE_DIR=/tmp/uv-cache uv run scripts/run_batch_scholar_merge_queue.py \
  --cdp-url http://127.0.0.1:9224 \
  --queue-file plans/artifacts/scholar_ui/merge_queue.json
```

## Queue / UX State

Discovery heuristics were tightened:

- obvious ordinal-series mismatches such as `second` vs `third` are no longer rediscovered as merge candidates

Queue triage view now shows:

- `status`
- `type=pair|multi`
- rough `confidence`
- top two titles

Remaining UX caveat:

- automatic post-merge verification filters are still somewhat narrow for some families
- when the automatic verification text is empty or misleading, use a broader read-only title filter manually

Important live-execution policy:

- batch live execution is disabled
- batch is allowed only for read-only dry-run preview
- live merges must go through `run_next_scholar_merge_queue_item.py --execute` or the bounded helper for a single reviewed family at a time

## Incorrect Merge Incident

`Scim` was merged incorrectly and should be treated as a false positive, not a validated merge.

Do not merge these as duplicates:

- `Scim: Intelligent skimming support for scientific papers`
- `Scim: Intelligent faceted highlights for interactive, multi-pass skimming of scientific papers`

Observed mistake:

- the family-name overlap after `Scim:` was too weak to justify merge safety
- the queue/discovery heuristic accepted the pair anyway
- a live merge was executed before that semantic mismatch was caught

Recovery / handling:

- the queue item was later moved to `skipped` after manual Scholar repair
- do not attempt automated unmerge until a safe unmerge flow is explicitly investigated
- treat `Scim` as the motivating regression test for stricter title-suffix heuristics

## Batch Execution Incident

A second failure mode was observed during live batch execution.

Observed mistake:

- `Cord-19` merged correctly as the first batch item
- page state then shifted before the next item
- the next queued `Dolma` item no longer had its reviewed row visible
- after subsequent manual repair, it became clear a `Dolma` / `CORD-19` incorrect merge had occurred during the batch-execution attempt

Recovery / handling:

- manual Scholar repair was performed
- live batch execution is now disabled in code
- only batch dry-run remains enabled
- all live merges are back to one-item-at-a-time execution

## Live Merges Completed In 003

### Early bounded helper validations

1. `2 OLMo 2 Furious`

- surviving row:
  - `2 OLMo 2 Furious`
- observed citation change:
  - `343* -> 396*`

2. `Dolma`

- surviving row:
  - `Dolma: An open corpus of three trillion tokens for language model pretraining research`
- observed citation change:
  - `377 -> 388`

### Queue-driven validated merges

3. `OLMo: Accelerating the science of language models`

- surviving row:
  - `OLMo: Accelerating the science of language models`
- observed citation change:
  - `491 -> 508`

4. `SciBERT`

- surviving row:
  - `SciBERT: A pretrained language model for scientific text`
- observed citation change:
  - `5676 -> 5709`

5. `The semantic reader project`

- surviving row:
  - `The semantic reader project: Augmenting scholarly documents through ai-powered interactive reading interfaces`
- observed family outcome:
  - pre-merge visible family `34 + 20`
  - post-merge visible surviving row `54*`

6. `Molmo and pixmo`

- surviving row:
  - `Molmo and pixmo: Open weights and open data for state-of-the-art vision-language models`
- observed citation change:
  - `606* -> 618*`

7. `The semantic scholar open data platform`

- surviving row:
  - `The semantic scholar open data platform`
- observed citation change:
  - `192 -> 204`

8. `Cord-19: The covid-19 open research dataset`

- surviving row:
  - `Cord-19: The covid-19 open research dataset`
- observed citation change:
  - `1207* -> 1605*`

9. `Dolma` recovery, part 1

- reviewed rows:
  - `Dolma: An open corpus of three trillion tokens for language model pretraining research`
  - `Dolma: An open corpus of 3 trillion tokens for language model pretraining research`
- observed citation change:
  - `377 -> 388`

10. `Dolma` recovery, part 2

- reviewed rows:
  - `Dolma: An open corpus of three trillion tokens for language model pretraining research`
  - `Dolma: an open corpus of three trillion tokens for language model pretraining research (2024)`
- observed citation change:
  - `388 -> 396`

11. `2 OLMo 2 Furious` cleanup, part 1

- reviewed rows:
  - `2 OLMo 2 Furious`
  - `olmo 2 furious`
- observed citation change:
  - `396* -> 413*`

12. `2 OLMo 2 Furious` cleanup, part 2

- reviewed rows:
  - `2 OLMo 2 Furious`
  - `olmo 2 furious, 2025`
- observed citation change:
  - `413* -> 442*`

13. `2 OLMo 2 Furious` cleanup, part 3

- reviewed rows:
  - `2 OLMo 2 Furious`
  - `others. 2024. 2 olmo 2 furious`
- observed citation change:
  - `442* -> 459*`

14. `OpenScholar` visible 2024 pair

- reviewed rows:
  - `Openscholar: Synthesizing scientific literature with retrieval-augmented lms`
  - `OpenScholar: synthesizing scientific literature with retrieval-augmented language models`
- observed family outcome:
  - visible 2024 pair merged successfully
  - no clearly visible residual family remained after one bounded read-only refresh

Incorrect merge to repair manually:

- `Scim`
  - merged in error
  - do not count as a validated success
  - manual Scholar repair is needed before considering that family resolved

- `Dolma` / `CORD-19`
  - incorrect merge during live batch execution attempt
  - manually repaired
  - do not use as evidence that live batching is safe

## Evidence Pattern

Each live merge produced:

- `merge_pre_*.html`
- `merge_pre_*.png`
- `merge_pre_*_capture.json`
- `merge_post_*.html`
- `merge_post_*.png`
- `merge_post_*_capture.json`

These live artifacts are under:

- `plans/artifacts/scholar_ui/`

## Current Queue Situation

At the end of this session, the queue has multiple items already advanced beyond `discovered`:

- merged:
  - `OLMo`
  - `SciBERT`
  - `The semantic reader project`
  - `Molmo and pixmo`
  - `The semantic scholar open data platform`
- skipped:
  - workshop `second` / `third` mismatch

Still-remaining notable candidates include:

- `Scim`
- `OpenScholar`
  - lower confidence and requires more caution
  - visible 2024 pair was merged, but the 2026 variant was not visibly actionable afterward
- residual rediscovery artifacts such as `Molmo and pixmo`
  - do not treat as actionable unless a bounded read-only refresh makes the family visibly rediscoverable again

## Resume Guidance

If a future session resumes:

1. launch isolated `003` Chrome on port `9224`
2. manually open the Scholar profile page in that Chrome
3. inspect queue triage:

```bash
python3 scripts/review_scholar_merge_queue.py \
  --queue-file plans/artifacts/scholar_ui/merge_queue.json \
  list --triage --limit 20
```

4. inspect specific queue items before approving anything new
5. only approve one family at a time
6. dry-run before live execution
7. do not use batch `--execute`; it is intentionally disabled

Do not immediately rediscover unless needed.

Reason:

- rediscovery is now safer than before, but it can still shift family composition and produce new ids
- the current queue already contains useful state and completed history

## Recommended Next Step

Best next work is review, not more plumbing.

Recommended next candidate families to review:

- any newly rediscovered clean 2-row pair after fresh discovery
- `OpenScholar` 2026 residual only if it becomes visibly actionable in a future session

Lower-confidence family to defer unless explicitly reviewed:

- `OpenScholar`
