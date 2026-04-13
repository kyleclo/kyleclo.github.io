# Bounded Add Automation Summary

## Outcome

The bounded Add Articles mutation phase is complete enough to close.

What was validated:

- profile-page Add Articles reopening via DOM actions
- bounded query replay
- bounded Add Articles pagination to specific page starts
- one-row add / attach with explicit confirmation
- pre / post evidence capture around each mutation
- live verification by reopening the same query surface and checking whether the row moved to `in profile`

Observed Scholar behavior that is now accounted for:

- after a successful add, Scholar redirects back to the profile page instead of leaving the modal open
- stale visible modal layers can intercept pointer events and must be closed before reopening the Add Articles flow
- deep-page candidates can still be handled safely if pagination is bounded to a known `data-start`
- fresh verification captures must be parsed into `*_add_articles.json` or the detector will continue using stale candidate evidence

Artifact handling going forward:

- keep this summary and other curated notes in `plans/artifacts/scholar_ui/`
- treat raw screenshots / HTML / parsed modal captures as local-only by default
- the Playwright capture and bounded-add helpers should write to `_local/scholar_ui/` unless there is a deliberate reason to promote a small curated artifact into version control

## Completed Adds

These reviewed candidates were added and then rechecked live until they were confirmed `in profile`:

- `o054MLHYLD4J` — `olmo 2 furious, 2025`
- `vpfBpp8-EFEJ` — `others. 2024. 2 olmo 2 furious`
- `wCg_BxIioKoJ` — `Dolma: An open corpus of 3 trillion tokens for language model pretraining research`
- `5Bt43d6l_X0J` — `The Semantic Scholar Open Data Platform. 2023`
- `22A56kzvw6AJ` — `others. 2024. Molmo and pixmo: Open weights and open data for state-of-the-art vision-language models`
- `GV3Zrefy3-AJ` — `Olmo: Accelerating the science of language models, 2024`
- `k1OqTfh6yacJ` — `OpenScholar: synthesizing scientific literature with retrieval-augmented language models`
- `tAX08StN4NIJ` — `olmo 2 furious`
- `dKNX2RTny1wJ` — `Dolma: an open corpus of three trillion tokens for language model pretraining research (2024)`

## Follow-Up Add After The Main Checkpoint

One additional targeted add-backed under-clustering case was validated after the main bounded-add checkpoint:

- profile anchor:
  - `2 OLMo 2 Furious`
- reviewed add candidate:
  - `LIUPXrPTFKwJ`
  - `& Hajishirzi, H.(2024). 2 OLMo 2 Furious`
  - query: `"2 OLMo 2 Furious"`

Observed outcome:

- the bounded add helper successfully clicked `Add`
- immediate post-click state again matched known Scholar behavior: the reviewed row disappeared rather than flipping inline to `in profile`
- a later live profile/add-surface check showed the family attached to the profile:
  - `2 OLMo 2 Furious`
  - `2 OLMo 2 Furious (COLM's Version)`
  - `2 olmo 2 furious`
  - each visible as `in profile`

Interpretation:

- treat this add as operationally successful
- any remaining duplicate cleanup for the `2 OLMo 2 Furious` family belongs to the separate merge-focused `003` track

## Additional Follow-Up Add Attempt

One further targeted under-clustering case was attempted after the `2 OLMo 2 Furious` follow-up:

- profile anchor:
  - `Molmo and pixmo: Open weights and open data for state-of-the-art vision-language models`
- reviewed add candidate:
  - `KLTHA-EEY2sJ`
  - `Molmo and PixMo: Open Weights and Open Data for State-ofthe-Art Vision-Language Models`
  - query: `Pixmo`

Observed outcome:

- the bounded add helper successfully clicked `Add`
- immediate post-click behavior again matched the known Scholar pattern: the reviewed row disappeared instead of flipping inline to `in profile`
- a later direct `Pixmo` reopen returned an empty add surface rather than a visible `in profile` row
- unlike the `2 OLMo 2 Furious` case, this follow-up did not yet produce a strong same-family post-add verification artifact

Interpretation:

- treat this as a likely-successful add attempt, but not yet a fully verified one
- keep the `Molmo/Pixmo` family in the unresolved follow-up bucket until a later session captures a clearer post-add verification signal
- any duplicate cleanup or merge work for this family still belongs to `003`

## Historical Checkpoint Queue State

After backfilling the final verification captures and rerunning:

```bash
python3 scripts/scholar_hygiene.py detect
python3 scripts/scholar_hygiene.py review --type under_clustered_profile_article
```

The result was:

- total issue count: `81`
- open under-clustered add queue: `0`
- `review --type under_clustered_profile_article` returns `No issues found.`

This was the closeout state of the original bounded-add checkpoint on April 11, 2026.

Later `002` follow-up work reopened targeted under-clustering discovery for specific families such as:

- `2 OLMo 2 Furious`
- `Molmo/Pixmo`

So the historical zero-queue checkpoint should not be read as "002 is permanently exhausted."

## Evidence Pattern

For each successful bounded add, useful evidence is typically:

- `mutation_pre_*_capture.json`
- `mutation_post_*_capture.json`
- a later `mutation_pre_*_capture.json` from the verification reopen showing `status_label = "in profile"`

## Next Phase

The original next phase after the April 11 checkpoint was intended to avoid further broad add work and instead move to a new bounded phase, with separate guardrails, for one of:

1. merge automation for newly attached under-clustered families
2. metadata-anomaly review / cleanup

If merge automation starts next, begin with one reviewed family at a time and keep the same pattern:

- explicit reviewed target
- one mutation at a time
- pre / post evidence capture
- refusal if the expected merge surface is not visible

Current stable stopping point for `002`:

- bounded add automation is proven and usable
- deeper `Kyle Lo` pagination through page `90` did not reveal true missing-paper candidates
- targeted queries remain the better source of under-clustered add candidates
- `2 OLMo 2 Furious` should be treated as successfully attached and ready for later merge cleanup
- `Molmo/Pixmo` should be treated as add-attempted and likely attached, but not yet strongly verified from fresh evidence
- if `002` resumes again, the most useful hardening is freshness handling for successful adds
- after that hardening, the next optional `002` continuation is a systematic all-profile targeted-query campaign for under-clustering discovery
