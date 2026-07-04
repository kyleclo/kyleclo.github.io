# 003 Merge Automation Scale-Out Plan

## Why This File Exists

This file extends the 003 merge-automation phase after the first bounded live validations.

Primary 003 entrypoint for recovered sessions:

- `plans/003_merge_automation_index.md`

003 already proved that bounded live merge automation is possible for at least two reviewed families:

- `2 OLMo 2 Furious`
- `Dolma`

What is still missing is the workflow layer between:

- one-off hand-driven reviewed merges
- and any credible path toward larger-scale merge automation

This file defines that workflow layer.

It is still part of 003 because the core problem has not changed:

- bounded Google Scholar merge automation

What changes now is the operating model:

- from single ad hoc reviewed runs
- to a structured reviewed queue with explicit operator approval and recorded outcomes

## Phase Goal

Build a queue-driven, reviewer-centered merge workflow that can:

- discover likely merge families in read-only mode
- present them for human review
- execute only explicitly approved families
- verify and record outcomes
- stop safely on ambiguity or unexpected UI states

This is the prerequisite for any later discussion of semi-batch or broader-scale merge execution.

## Related 003 Files

- `plans/003_merge_automation_index.md`
  - single best recovery / entrypoint file
- `plans/003_bounded_google_scholar_merge_automation.md`
  - original bounded phase-entry plan
- `plans/artifacts/scholar_ui/bounded_merge_automation_summary_20260413.md`
  - concise validated-results summary
- `plans/artifacts/scholar_ui/003_merge_queue_progress_resume_20260413.md`
  - primary resume / handoff note
- `plans/artifacts/scholar_ui/merge_queue.json`
  - current operational queue state

## Operator Role

The human operator remains the reviewer and approver.

The operator is responsible for semantic judgment:

- whether two or more rows are truly the same paper
- whether a reviewed family is safe to merge
- whether an unexpected canonical-choice or ambiguous merge surface requires manual handling

The automation is responsible for mechanical work:

- discovering candidate families
- formatting them into a review queue
- revalidating exact row ids and titles before action
- performing the known merge flow
- capturing evidence
- recording success or failure

Operator approval should be per family, not global.

The workflow should never interpret "continue" as blanket approval for all visible duplicate families.

## Validated Scholar Merge Flow

The currently validated live merge flow is:

1. open a logged-in Scholar profile page over CDP
2. select reviewed rows by exact row id
3. click the primary profile merge button:
   - `gsc_btn_mer`
4. if Scholar opens the standard confirmation modal:
   - click `gsc_md_mopt_merge`
5. wait for an observable profile-table change
6. relist the visible family in read-only mode to confirm the post-merge state

Additional validated behavior:

- stale merge confirmation modals can persist and must be dismissed before a new run
- read-only `Show more` expansion is acceptable for bounded discovery
- exact row-id and exact-title checks are necessary guardrails

Not yet validated:

- a canonical-choice merge surface where Scholar asks the operator to choose a surviving record
- safe unattended execution across many approved families in one session

## Scale-Out Architecture

The scale-out workflow should have four layers:

1. discovery
2. review queue
3. bounded execution
4. verification and state recording

### 1. Discovery

Discovery stays read-only.

Responsibilities:

- inspect the current visible Scholar profile rows
- optionally perform bounded `Show more` expansion
- group likely duplicate or under-clustered families
- emit candidate merge families with evidence

Discovery must not click merge controls.

Discovery should be allowed to:

- list visible rows
- filter by title fragments
- collect row ids, titles, citations, and years
- record local evidence artifacts when useful

### 2. Review Queue

Discovery output should be normalized into a queue artifact.

Suggested statuses:

- `discovered`
- `reviewed`
- `approved`
- `skipped`
- `merged`
- `failed`
- `needs_manual_choice`
- `stale`

Each queue item should be a single reviewed family, ideally 2 rows at first.

Suggested fields:

- queue item id
- status
- family label
- target rows:
  - `row_id`
  - `title`
  - `citations`
  - `year`
- discovery evidence path
- operator review notes
- approval timestamp
- execution attempt count
- pre-artifact paths
- post-artifact paths
- post-merge verification summary

The queue artifact can be JSON first. Markdown review views can be generated from it later.

### 3. Bounded Execution

Execution should consume one approved queue item at a time.

Execution steps:

1. load the next approved queue item
2. attach to the logged-in Scholar session
3. dismiss any stale merge confirmation modal
4. revalidate exact reviewed rows by row id and title
5. capture pre evidence
6. click `gsc_btn_mer`
7. if the standard confirmation modal appears:
   - click `gsc_md_mopt_merge`
8. refuse if an unexpected merge surface appears
9. capture post evidence
10. write execution outcome back to the queue item

The execution runner should still default to one item only.

Even after queue support exists, execution should not silently roll into the next approved family in the same run unless the policy is intentionally widened later.

### 4. Verification and State Recording

Verification should be explicit and structured, not just eyeballing screenshots.

Suggested checks:

- relist the visible family after merge
- compare pre / post family row count
- compare citation deltas on the surviving row
- record whether the reviewed duplicate row is still separately visible

Suggested verification outcomes:

- `verified_merged`
- `uncertain`
- `verification_failed`

Verification results should be written back into the queue item, not left only in stdout.

## Proposed Queue Item Shape

Illustrative JSON shape:

```json
{
  "id": "merge:dolma:001",
  "status": "approved",
  "family_label": "Dolma",
  "targets": [
    {
      "row_id": "jY919eMAAAAJ:maZDTaKrznsC",
      "title": "Dolma: An open corpus of three trillion tokens for language model pretraining research",
      "citations": "377",
      "year": "2024"
    },
    {
      "row_id": "jY919eMAAAAJ:sSrBHYA8nusC",
      "title": "Dolma: An open corpus of 3 trillion tokens for language model pretraining research",
      "citations": "12",
      "year": "2023"
    }
  ],
  "discovery_evidence": [
    "plans/artifacts/scholar_ui/merge_pre_20260413_082530.html"
  ],
  "review_notes": "Clear duplicate title variant",
  "approved_by_operator": true,
  "execution_attempts": 0,
  "result": null
}
```

## Safety Policy

The scale-out plan must preserve the safety style already validated in 003.

Required stop conditions:

- reviewed row missing
- reviewed title mismatch
- duplicate row-id match
- primary merge button not visible and enabled
- unexpected modal type
- multiple conflicting visible merge surfaces not explained by the known two-step flow
- Scholar transient error state
- post-merge verification ambiguity

Required policy:

- stop on first failure
- do not continue to the next queue item automatically after a failed or ambiguous item
- do not guess at canonical selection if Scholar presents a richer choice surface

## Canonical-Choice Handling

The currently validated flow did not require a canonical-choice decision.

However, the workflow must explicitly account for the possibility that Scholar may show a richer merge surface for some families.

If that happens:

- do not click through heuristically
- capture evidence
- mark the queue item `needs_manual_choice`
- return control to the operator

A future enhancement may explicitly model that UI, but that should not be assumed during current scale-out work.

## Implementation Plan

### Step 1. Formalize Queue Artifacts

Add a merge queue artifact format under `plans/artifacts/scholar_ui/` or a nearby structured location.

Deliverables:

- JSON schema-by-convention
- helper functions to read and write queue items
- initial sample queue artifact

### Step 2. Build Read-Only Discovery Output

Extend the merge helper or add a companion script that:

- collects visible rows
- optionally expands with bounded `Show more`
- proposes likely duplicate families
- writes discovered candidates into queue items with status `discovered`

Deliverables:

- read-only discovery CLI
- candidate-family output artifact
- tests for family grouping and queue writing

### Step 3. Build Review Surfaces

Add a simple operator review path:

- render queue items as Markdown or concise terminal output
- allow updating queue status from `discovered` to `approved`, `skipped`, or `needs_manual_choice`

This can begin as file editing plus helper commands rather than a full interactive UI.

Deliverables:

- queue review formatter
- queue status updater
- tests for status transitions

### Step 4. Connect Queue To Execution

Add a runner that executes exactly one approved queue item using the existing bounded merge helper logic.

Deliverables:

- `run-next-approved-merge` style command
- pre/post artifact recording into queue item state
- stop-on-failure behavior

### Step 5. Add Structured Verification

After execution, perform read-only verification and write the result back to the queue item.

Deliverables:

- verification result object
- queue item result updates
- tests for success / uncertain / failed verification transitions

## Exit Criteria For 003 Scale-Out Slice

This slice is complete when:

- a queue artifact format exists
- discovery can write candidate families into that queue
- the operator can approve or skip individual queue items
- one approved item can be executed via the queue runner
- verification writes structured outcomes back to the queue
- the workflow stops safely on ambiguity

## Explicit Non-Goals

Not part of this slice:

- fully unattended merge automation
- auto-approving merge families
- executing many approved families in one run by default
- guessing canonical records in a richer merge-choice UI
- broad workflow refactors unrelated to the merge queue path

## Recommended Next Build Order

The next implementation work should proceed in this order:

1. queue artifact helpers
2. read-only discovery into queue items
3. review formatting and status updates
4. one-item queue execution
5. structured verification result writing

Only after those pieces are working should we consider policy for tiny approved batches.
