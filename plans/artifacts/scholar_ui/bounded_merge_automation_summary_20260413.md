# Bounded Merge Automation Summary

## Outcome

The bounded Scholar merge automation slice is validated for one-item-at-a-time live execution.

What was validated:

- reviewed profile-row targeting by exact Scholar row id
- DOM-only row selection on the profile page
- refusal unless a visible enabled primary merge control is present
- explicit confirmation before mutation
- pre / post evidence capture around each merge attempt
- handling of Scholar's real two-step merge flow:
  - profile merge button first
  - confirmation modal merge button second
- read-only verification after merge by relisting the visible family
- batch dry-run preview across approved items

What is not validated:

- live batch execution across multiple items without an intermediate page-state reset

## Successful Reviewed Merges

### 1. `2 OLMo 2 Furious`

Reviewed rows:

- `jY919eMAAAAJ:roLk4NBRz8UC`
  - `2 OLMo 2 Furious`
- `jY919eMAAAAJ:tOudhMTPpwUC`
  - `Faeze Brahman, Christopher Clark, Pradeep Dasigi, Nouha Dziri, and 21 others. 2025. 2 olmo 2 furious`

Evidence:

- pre:
  - `plans/artifacts/scholar_ui/merge_pre_20260412_090548.html`
  - `plans/artifacts/scholar_ui/merge_pre_20260412_090548.png`
- post:
  - `plans/artifacts/scholar_ui/merge_post_20260412_090550.html`
  - `plans/artifacts/scholar_ui/merge_post_20260412_090550.png`

Read-only verification result:

- visible family reduced to a single `2 OLMo 2 Furious` row
- citations increased from `343*` to `396*`

### 2. `Dolma`

Reviewed rows:

- `jY919eMAAAAJ:maZDTaKrznsC`
  - `Dolma: An open corpus of three trillion tokens for language model pretraining research`
- `jY919eMAAAAJ:sSrBHYA8nusC`
  - `Dolma: An open corpus of 3 trillion tokens for language model pretraining research`

Evidence:

- pre:
  - `plans/artifacts/scholar_ui/merge_pre_20260413_082950.html`
  - `plans/artifacts/scholar_ui/merge_pre_20260413_082950.png`
- post:
  - `plans/artifacts/scholar_ui/merge_post_20260413_082953.html`
  - `plans/artifacts/scholar_ui/merge_post_20260413_082953.png`

Read-only verification result:

- visible family reduced to a single `Dolma` row
- citations increased from `377` to `388`

### 3. `Cord-19: The covid-19 open research dataset`

Reviewed rows:

- `jY919eMAAAAJ:D03iK_w7-QYC`
  - `Cord-19: The covid-19 open research dataset`
- `jY919eMAAAAJ:rO6llkc54NcC`
  - `The Covid-19 open research dataset`

Evidence:

- pre:
  - `plans/artifacts/scholar_ui/merge_pre_20260413_145549.html`
  - `plans/artifacts/scholar_ui/merge_pre_20260413_145549.png`
- post:
  - `plans/artifacts/scholar_ui/merge_post_20260413_145551.html`
  - `plans/artifacts/scholar_ui/merge_post_20260413_145551.png`

Read-only verification result:

- visible family reduced to a single `Cord-19` row
- citations increased from `1207*` to `1605*`

### 4. `Dolma` recovery via reviewed sub-pairs

Reviewed sub-pair A:

- `jY919eMAAAAJ:kRWSkSYxWN8C`
  - `Dolma: An open corpus of three trillion tokens for language model pretraining research`
- `jY919eMAAAAJ:V3AGJWp-ZtQC`
  - `Dolma: An open corpus of 3 trillion tokens for language model pretraining research`

Reviewed sub-pair B:

- `jY919eMAAAAJ:kRWSkSYxWN8C`
  - `Dolma: An open corpus of three trillion tokens for language model pretraining research`
- `jY919eMAAAAJ:mvPsJ3kp5DgC`
  - `Dolma: an open corpus of three trillion tokens for language model pretraining research (2024)`

Evidence:

- part A pre/post:
  - `plans/artifacts/scholar_ui/merge_pre_20260413_155740.html`
  - `plans/artifacts/scholar_ui/merge_post_20260413_155742.html`
- part B pre/post:
  - `plans/artifacts/scholar_ui/merge_pre_20260413_161548.html`
  - `plans/artifacts/scholar_ui/merge_post_20260413_161550.html`

Read-only verification result:

- final visible `Dolma` row:
  - `Dolma: An open corpus of three trillion tokens for language model pretraining research`
- citations increased to `396`

### 5. `2 OLMo 2 Furious` cleanup via reviewed sub-pairs

Reviewed sub-pair A:

- `jY919eMAAAAJ:roLk4NBRz8UC`
  - `2 OLMo 2 Furious`
- `jY919eMAAAAJ:fQNAKQ3IYiAC`
  - `olmo 2 furious`

Reviewed sub-pair B:

- `jY919eMAAAAJ:roLk4NBRz8UC`
  - `2 OLMo 2 Furious`
- `jY919eMAAAAJ:4fKUyHm3Qg0C`
  - `olmo 2 furious, 2025`

Reviewed sub-pair C:

- `jY919eMAAAAJ:roLk4NBRz8UC`
  - `2 OLMo 2 Furious`
- `jY919eMAAAAJ:B3FOqHPlNUQC`
  - `others. 2024. 2 olmo 2 furious`

Evidence:

- part A pre/post:
  - `plans/artifacts/scholar_ui/merge_pre_20260414_081922.html`
  - `plans/artifacts/scholar_ui/merge_post_20260414_081924.html`
- part B pre/post:
  - `plans/artifacts/scholar_ui/merge_pre_20260414_082642.html`
  - `plans/artifacts/scholar_ui/merge_post_20260414_082644.html`
- part C pre/post:
  - `plans/artifacts/scholar_ui/merge_pre_20260414_082710.html`
  - `plans/artifacts/scholar_ui/merge_post_20260414_082712.html`

Read-only verification result:

- final visible `2 OLMo 2 Furious` row:
  - `2 OLMo 2 Furious`
- citations increased to `459*`

### 6. `OpenScholar` visible 2024 pair

Reviewed rows:

- `jY919eMAAAAJ:SP6oXDckpogC`
  - `Openscholar: Synthesizing scientific literature with retrieval-augmented lms`
- `jY919eMAAAAJ:LPZeul_q3PIC`
  - `OpenScholar: synthesizing scientific literature with retrieval-augmented language models`

Evidence:

- pre:
  - `plans/artifacts/scholar_ui/merge_pre_20260414_105527.html`
  - `plans/artifacts/scholar_ui/merge_pre_20260414_105527.png`
- post:
  - `plans/artifacts/scholar_ui/merge_post_20260414_105529.html`
  - `plans/artifacts/scholar_ui/merge_post_20260414_105529.png`

Read-only verification result:

- the visible 2024 pair merged successfully
- after one bounded refresh, no clearly visible residual `OpenScholar` family remained actionable

## Important Scholar Behavior Observed

The real merge flow is two-step:

1. select reviewed profile rows
2. click the primary profile merge button `gsc_btn_mer`
3. Scholar opens a merge confirmation modal
4. click the confirmation modal merge button `gsc_md_mopt_merge`

This was not safely automatable until the helper was updated to:

- detect the primary merge surface separately from modal merge controls
- detect and click the confirmation modal merge control only as the second step
- dismiss a stale open merge confirmation modal before starting a new run
- page state can drift materially after a live merge and must be treated as unsafe for the next live item without fresh revalidation
- keep Chrome sessions isolated per worktree:
  - separate CDP port per Scholar worktree
  - separate `--user-data-dir` per Scholar worktree
  - do not attach 003 automation to the same Chrome instance used by 002

## Guardrails That Matter In Practice

- one reviewed merge family at a time
- exact row ids plus exact title checks
- dry-run by default
- explicit confirmation phrase:
  - `MERGE <sorted row ids...>`
- refuse if the primary merge button is not visibly enabled
- refuse if reviewed rows are missing, duplicated, or title-mismatched
- capture pre evidence before any click
- capture post evidence after the merge completes
- perform a read-only family relist after merge to confirm the visible result
- do not use live batch execution

## Incorrect Merge Lessons

Two important mistakes were observed and then contained:

- `Scim` was a false-positive semantic merge candidate and required manual repair
- a live batch execution attempt led to an incorrect `Dolma` / `CORD-19` merge after page-state drift

Operational conclusion:

- batch review is fine
- batch dry-run is fine
- live execution must remain one reviewed family at a time

## Discovery Notes

- read-only `Show more` expansion is safe for bounded discovery
- it should be treated as page-state discovery only, not as mutation
- after expansion, reviewed row ids must still be revalidated before any merge action

## Current State

The merge helper is now strong enough for additional bounded reviewed families, but the phase should remain conservative:

- one reviewed family at a time
- dry-run first
- live merge only after exact row verification
- evidence capture on every run
- batch execute disabled; single-item live execution only
- stop when no clearly safe visible next family remains
