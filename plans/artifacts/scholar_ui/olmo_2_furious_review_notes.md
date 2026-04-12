# OLMo 2 Furious Review Notes

## Purpose

This note captures the concrete `Add articles` evidence for the `olmo 2 furious` query family.

The main interpretation is:

- this looks like an under-clustering case, not just a missing-paper case
- multiple closely related variants are already marked `in profile`
- multiple additional variants remain `not in profile`

## Source Artifacts

- `plans/artifacts/scholar_ui/current_page_20260411_171606_add_articles.json`
- `plans/artifacts/scholar_ui/current_page_20260411_171615_add_articles.json`
- `plans/artifacts/scholar_ui/current_page_20260411_171624_add_articles.json`

## Likely In-Profile Anchor Rows

- `doc_id = YMXJ3gTQoygJ`
  - title: `2 OLMo 2 Furious`
- `doc_id = u0s43F4mZm0J`
  - title: `2 olmo 2 furious`
- `doc_id = wHpDbR9Nw7wJ`
  - title: `2 OLMo 2 Furious (COLM's Version)`
- `doc_id = VfY8gkIE6_gJ`
  - title: `Faeze Brahman, Christopher Clark, Pradeep Dasigi, Nouha Dziri, and 21 others. 2025. 2 olmo 2 furious`

## Not-In-Profile Variants Worth Manual Review

- `doc_id = o054MLHYLD4J`
  - title: `olmo 2 furious, 2025`
  - artifact: `plans/artifacts/scholar_ui/current_page_20260411_171606_add_articles.json`
- `doc_id = vpfBpp8-EFEJ`
  - title: `others. 2024. 2 olmo 2 furious`
  - artifact: `plans/artifacts/scholar_ui/current_page_20260411_171606_add_articles.json`
- `doc_id = i7ywIpNfJpQJ`
  - title: `Faeze Brahman, Christopher Clark, Pradeep Dasigi, Nouha Dziri, and 21 others. 2024. 2 olmo 2 furious`
  - artifact: `plans/artifacts/scholar_ui/current_page_20260411_171606_add_articles.json`
- `doc_id = RFXe98qWDzMJ`
  - title: `OLMo 2 Furious. arXiv 2024`
  - artifact: `plans/artifacts/scholar_ui/current_page_20260411_171606_add_articles.json`
- `doc_id = tAX08StN4NIJ`
  - title: `olmo 2 furious`
  - artifact: `plans/artifacts/scholar_ui/current_page_20260411_171615_add_articles.json`
- `doc_id = LIUPXrPTFKwJ`
  - title: `& Hajishirzi, H.(2024). 2 OLMo 2 Furious`
  - artifact: `plans/artifacts/scholar_ui/current_page_20260411_171615_add_articles.json`

## Recommended Manual Review Flow

1. Open the existing Scholar profile entry or entries already marked `in profile`.
2. Open the candidate rows above by `doc_id` / title URL from the JSON artifacts.
3. Decide which `not in profile` rows are true duplicates / variants of the same paper family.
4. Add and merge only the rows that clearly belong in the same Scholar cluster.

## Working Conclusion

This query family is now a strong example for under-clustering review and should remain in the curated query set.
