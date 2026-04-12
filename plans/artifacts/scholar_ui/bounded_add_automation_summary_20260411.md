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

## Final Queue State

After backfilling the final verification captures and rerunning:

```bash
python3 scripts/scholar_hygiene.py detect
python3 scripts/scholar_hygiene.py review --type under_clustered_profile_article
```

The result was:

- total issue count: `81`
- open under-clustered add queue: `0`
- `review --type under_clustered_profile_article` returns `No issues found.`

## Evidence Pattern

For each successful bounded add, useful evidence is typically:

- `mutation_pre_*_capture.json`
- `mutation_post_*_capture.json`
- a later `mutation_pre_*_capture.json` from the verification reopen showing `status_label = "in profile"`

## Next Phase

The next phase should not continue Add Articles automation.

The next practical step is a new bounded phase, with separate guardrails, for one of:

1. merge automation for newly attached under-clustered families
2. metadata-anomaly review / cleanup

If merge automation starts next, begin with one reviewed family at a time and keep the same pattern:

- explicit reviewed target
- one mutation at a time
- pre / post evidence capture
- refusal if the expected merge surface is not visible
