# 003 Merge Automation Index

## Purpose

This is the single best entrypoint for a fresh agent or a recovered session working on `003`.

If context is lost, start here first, then read the linked files in order.

This index is for the `003` merge-correction workflow now merged into this repository.

It originated in the `scholar-merge-automation` worktree, but should now be treated as the canonical `main` entrypoint for bounded Scholar merge correction.

## Read In This Order

1. `plans/003_bounded_google_scholar_merge_automation.md`

- role:
  - original 003 phase-entry plan
  - goals, guardrails, bounded-safety model

2. `plans/003_bounded_google_scholar_merge_automation_scaleout.md`

- role:
  - queue/review/execute/verify operating model
  - reviewer-centered scale-out design

3. `plans/artifacts/scholar_ui/bounded_merge_automation_summary_20260413.md`

- role:
  - concise summary of what 003 actually validated
  - successful merges, guardrails, incidents, current execution policy

4. `plans/artifacts/scholar_ui/003_merge_queue_progress_resume_20260413.md`

- role:
  - primary resume / handoff document
  - Chrome/CDP setup, queue commands, incidents, completed merges, current resume guidance

5. `plans/artifacts/scholar_ui/merge_queue.json`

- role:
  - machine-readable current queue state
  - operational source of truth for discovered / approved / merged / skipped / stale items

## Current Execution Policy

The current safe policy for 003 is:

- batch review is allowed
- batch dry-run is allowed
- live batch execution is disabled
- live mutation must be one reviewed family at a time
- dry-run before live execution
- stop when there is no clearly safe visible next family

## Key Operational Notes

- use isolated Chrome for 003:
  - CDP: `http://127.0.0.1:9224`
  - profile dir: `/tmp/chrome-scholar-003`
- do not share the Chrome session with 002
- do not run live Scholar mutation concurrently across worktrees/sessions

## Important Incident History

- `Scim` was a false-positive merge candidate and was manually repaired
- a live batch execution attempt caused an incorrect `Dolma` / `CORD-19` merge after page-state drift
- because of that, live batch execution is disabled in code

## If Resuming Fresh

1. start with this file
2. read the four linked docs above
3. inspect `merge_queue.json`
4. attach to isolated Chrome for 003
5. run fresh discovery only if needed
6. continue with one-item live execution only
