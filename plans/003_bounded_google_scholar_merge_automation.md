# Bounded Google Scholar Merge Automation

## Why This File Exists

This file starts the 003 phase for **bounded merge automation** in the `scholar-merge-automation` worktree.

Primary 003 entrypoint for recovered sessions:

- `plans/003_merge_automation_index.md`

The 002 add phase is complete enough for its bounded goal:

- one reviewed Add Articles row at a time
- explicit operator confirmation
- DOM-only modal actions
- pre/post evidence capture
- refusal when the expected Add Articles surface is not visible

003 is a separate phase. It should not continue broad Add Articles automation or reopen the exhausted under-clustered add queue. Its scope is narrower:

- merge already-reviewed Scholar profile families
- one reviewed family at a time
- reuse the same safety posture as the add phase

## Goals

Primary goal:

- implement a bounded helper for one reviewed Scholar merge family at a time

First implementation goal:

- verify that a reviewed set of profile rows is visible
- select only those rows via DOM actions
- capture pre/post evidence
- refuse to act unless a visible merge affordance is present
- require explicit operator confirmation before any live click

Non-goals for the first slice:

- no queue-driven bulk merge automation
- no heuristic auto-selection of merge targets from the full profile
- no mutation on ambiguous row families
- no broad refactor of the add helper unless a small shared primitive becomes clearly necessary

## Operating Model

The merge helper should mirror the completed add helper:

- attach to an already-open logged-in Chrome session over CDP
- operate against the currently visible Scholar profile page
- use DOM-only actions, not synthetic network calls
- default to dry-run output first
- require an exact confirmation phrase for execution
- write pre/post evidence artifacts for review

Chrome session isolation rule:

- each Scholar git worktree should use its own Chrome instance
- each Chrome instance should use its own:
  - remote debugging port
  - `--user-data-dir`
- 003 should not attach to the same Chrome session used by 002

Suggested convention:

- 002:
  - port `9223`
  - `/tmp/chrome-scholar-002`
- 003:
  - port `9224`
  - `/tmp/chrome-scholar-003`

Expected reviewed input:

- a small reviewed target family, usually 2 rows
- exact Scholar row ids
- optional exact title checks for each row
- optional reviewed note about which row is the anchor / canonical entry

## Guardrails

Required guardrails:

- one reviewed merge family at a time
- explicit operator intent via `MERGE <row ids...>`
- refuse to share a Chrome session with another Scholar worktree
- refuse if the profile page action bar is not visible
- refuse if any reviewed row is missing, duplicated, disabled, or title-mismatched
- refuse if the visible merge surface is not present after selecting the reviewed rows
- refuse if the merge surface text is ambiguous or disabled
- capture pre-mutation evidence before any click
- capture post-mutation evidence immediately after any click

Safety style carried over from 002:

- bounded step limits
- DOM-state verification after each action
- dry-run by default
- narrow CLI inputs instead of inferred targets
- evidence-first reviewability

## Risks

Main product risks:

- Scholar may expose merge through a different action surface than Add Articles
- stale overlays or profile-table redraws may interfere with row selection
- reviewed rows may disappear if the profile sort/filter changes
- Scholar may redirect or re-render after merge in a way that invalidates optimistic assumptions

Main automation risks:

- selecting the wrong row family because titles are similar
- clicking a visible but wrong action if merge affordance detection is too loose
- treating a partial profile action bar state as mutation-ready when Scholar is not actually ready

Initial mitigation:

- start with selection and merge-surface verification primitives
- keep execution optional and confirmation-gated
- click only a visible enabled control whose text clearly matches `Merge`
- stop immediately if the expected merge surface cannot be proven from the DOM

## First Reviewed Target

Primary first target:

- `2 OLMo 2 Furious`

Initial reviewed family to prepare for bounded merge:

- anchor candidates already noted in `plans/artifacts/scholar_ui/olmo_2_furious_review_notes.md`
- prefer a 2-row reviewed merge family first, not the whole paper family at once

Fallback target:

- `Dolma`

The reviewed row ids should be supplied explicitly at runtime after manual confirmation of the exact visible profile rows.

## Implementation Sequence

1. Create a dedicated 003 plan file.
2. Add a new bounded merge helper script alongside the add helper.
3. Reuse the add-phase patterns for:
   - CDP attach
   - page selection
   - profile readiness checks
   - artifact capture
   - explicit confirmation
4. Implement first bounded primitives:
   - parse and validate reviewed target specs
   - enumerate visible profile rows
   - choose exactly the reviewed rows
   - select them by DOM checkbox
   - prove whether a visible enabled merge action exists
5. Add unit tests for the non-live selection and guardrail logic.
6. Only after the above is stable, attempt one live reviewed merge action.

## Exit Criteria For The First Slice

The first 003 slice is complete when:

- the new plan exists
- a merge helper script exists and is dry-run safe by default
- the helper can prove or reject the merge surface from the current DOM
- explicit confirmation is required for execution
- unit tests cover the target parsing and reviewed-row selection guardrails

Live mutation is optional for this slice. If attempted later, it must remain bounded to one reviewed merge family.

## Related 003 Files

- `plans/003_merge_automation_index.md`
  - single best recovery / entrypoint file
- `plans/003_bounded_google_scholar_merge_automation_scaleout.md`
  - queue-driven scale-out design
- `plans/artifacts/scholar_ui/bounded_merge_automation_summary_20260413.md`
  - concise validated-results summary
- `plans/artifacts/scholar_ui/003_merge_queue_progress_resume_20260413.md`
  - primary resume / handoff note
- `plans/artifacts/scholar_ui/merge_queue.json`
  - current operational queue state
