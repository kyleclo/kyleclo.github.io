# Bibliography Rules for `papers.bib`

This document is the authoritative reference for formatting entries in `_bibliography/papers.bib`. Claude Code must read this file before editing `papers.bib`.

---

## Entry Types

| Type             | When to use                                                                                                                                                          |
| ---------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `@inproceedings` | Conference papers, workshop papers, system demos, tutorials. Use when the venue has "proceedings", "conference", "workshop", "symposium", or "tutorial" in its name. |
| `@article`       | Journal papers and ArXiv preprints.                                                                                                                                  |

---

## Citation Key Format

All citation keys follow `{FirstAuthorLastName}{Year}{TitleWords}`:

- **FirstAuthorLastName**: Last name of the first author, capitalized (e.g., `Lo`, `Groeneveld`). For team papers like "Team OLMo", use the team name (e.g., `Olmo`).
- **Year**: 4-digit publication year.
- **TitleWords**: First 2–3 meaningful words from the title in CamelCase. Skip articles ("a", "an", "the") and short prepositions. Capitalize each word.

Examples:

- `Lo2024ScalableData`
- `Groeneveld2024OlmoAccelerating`
- `Soldaini2024DolmaOpen`

---

## Required Fields (All Entries)

Every entry **must** have these fields:

| Field         | Description                                                    |
| ------------- | -------------------------------------------------------------- |
| `abstract`    | Full paper abstract.                                           |
| `author`      | Authors in `{Name1 and Name2 and Name3}` format.               |
| `bibtex_show` | Always `{true}`.                                               |
| `month`       | 3-letter capitalized abbreviation (see Month Format).          |
| `pdf`         | Slugified title + `.pdf` (e.g., `scalable-data-curation.pdf`). |
| `preview`     | Slugified title + `.png` (e.g., `scalable-data-curation.png`). |
| `title`       | Paper title.                                                   |
| `url`         | Link to paper (DOI URL, ArXiv URL, or venue page).             |
| `year`        | 4-digit publication year.                                      |

---

## Entry-Type-Specific Fields

### `@inproceedings` (Conference/Workshop Papers)

| Field       | Required? | Description                                                |
| ----------- | --------- | ---------------------------------------------------------- |
| `booktitle` | Yes       | Short-form venue name (see Venue Standardization).         |
| `doi`       | Optional  | DOI when available (see DOI Availability below).           |
| `arxiv`     | Optional  | ArXiv ID if the paper had a preprint (e.g., `2405.12345`). |

### `@article` (Journal Papers)

| Field     | Required? | Description                                    |
| --------- | --------- | ---------------------------------------------- |
| `journal` | Yes       | Full journal name (see Venue Standardization). |
| `volume`  | Yes       | Volume number.                                 |
| `doi`     | Yes       | DOI.                                           |
| `arxiv`   | Optional  | ArXiv ID if the paper had a preprint.          |

### `@article` (ArXiv Preprints)

| Field     | Required? | Description                                                   |
| --------- | --------- | ------------------------------------------------------------- |
| `journal` | Yes       | Always `{ArXiv}` (capital A, capital X).                      |
| `volume`  | Yes       | ArXiv ID (e.g., `{2405.12345}`).                              |
| `arxiv`   | Optional  | Same ArXiv ID (e.g., `{2405.12345}`). Include when available. |

---

## DOI Availability

Not all venues assign DOIs. Only include publisher-assigned DOIs; do not use ACM Digital Library virtual DOIs (`10.5555/...`).

**Venues that assign DOIs:**

- ACL Anthology venues: ACL, EMNLP, NAACL, EACL, COLING, Findings, System Demos, and ACL-hosted workshops (DOI prefix `10.18653/v1/`)
- ACM venues: CHI, IUI, FAccT, CIKM, KDD, WWW, and ACM journals (`10.1145/`)
- AAAI (`10.1609/`)
- CVPR, ICCV, ECCV via IEEE (`10.1109/`)
- Journals: Nature, IEEE, Elsevier, OUP, JAMA, etc.

**Venues that do NOT assign DOIs:**

- COLM (OpenReview only)
- ICLR (OpenReview only)
- ICML / PMLR
- NeurIPS (may appear in ACM DL later, but only as virtual DOIs — skip these)
- Text Analysis Conference (TAC)

For venues without DOIs, use the `openreview` field or proceedings URL instead.

---

## Preprint → Camera-Ready Transition

When a preprint gets accepted at a venue, update the **existing** entry in place. Do NOT create a second entry.

1. Change entry type if needed (e.g., `@article` → `@inproceedings`).
2. Update: `booktitle`/`journal`, `month`, `year`, `url`, `doi`, `title`, `author`, `abstract` to match the published version.
3. Keep the `arxiv = {YYMM.NNNNN}` field to preserve the preprint link.
4. Remove `volume` if it was only the ArXiv ID.
5. Re-download PDF from published source and regenerate thumbnail. Update `pdf` and `preview` filenames if the title changed.

---

## Venue Standardization

### Main Conferences (short form for `booktitle`)

`ACL`, `EMNLP`, `NAACL`, `EACL`, `COLING`, `NeurIPS`, `ICML`, `ICLR`, `COLM`, `CHI`, `CVPR`, `ICCV`, `ECCV`, `SIGIR`, `KDD`, `AAAI`, `IJCAI`, `IUI`, `FAccT`, `CIKM`, `WWW`

### Conference Tracks

- `NeurIPS (Datasets and Benchmarks)`
- `Findings of ACL`, `Findings of EMNLP`, `Findings of NAACL`

### Workshops

Format: `{Workshop Name} Workshop` or `{Workshop Name} Workshop at {Conference}`

Examples:

- `Scholarly Document Processing (SDP) Workshop`
- `NLP for COVID-19 Workshop`
- `BioNLP Workshop`
- `Intelligent and Interactive Writing Assistants (In2Writing) Workshop`

Workshops use `@inproceedings` with `booktitle`.

### System Demonstrations

Format: `{Conference} System Demonstrations`

Example: `EMNLP System Demonstrations`

### Tutorials

Tutorials at conferences use `@inproceedings` with the conference as `booktitle` (e.g., `booktitle = {ACL}`).

### Journals (full name for `journal`)

- `Nature`
- `Communications of the ACM`
- `Transactions of ACL (TACL)`
- `ACM Transactions on Interactive Intelligent Systems`
- `ACM Transactions of Computer-Human Interaction (TOCHI)`
- `Scientific Data`
- `Journal of Biomedical Informatics`
- `Journal of the American Medical Informatics Association`
- `Briefings in Bioinformatics`
- `SIGIR Forum`
- `AI Magazine`
- `Frontiers in Research Metrics and Analytics`
- `IEEE Internet of Things Journal`

### ArXiv

Always: `journal = {ArXiv}` — capital A, capital X.

---

## Month Format

Use 3-letter capitalized abbreviations:

`Jan`, `Feb`, `Mar`, `Apr`, `May`, `Jun`, `Jul`, `Aug`, `Sep`, `Oct`, `Nov`, `Dec`

---

## Optional Fields

| Field               | Description                                                                                            |
| ------------------- | ------------------------------------------------------------------------------------------------------ |
| `selected`          | `{true}` — marks paper for selected works on CV/website.                                               |
| `tags`              | Comma-separated research-area tags (see Tag Vocabulary below). Every entry must have 1–3 tags.         |
| `award`             | Award text, e.g., `{Best Paper Award}`, `{Outstanding Paper Award}`, `{Best Paper Honorable Mention}`. |
| `cv_authors_after`  | Truncate author list on CV after this author name.                                                     |
| `cv_authors_before` | Truncate author list on CV before this author name.                                                    |
| `arxiv`             | ArXiv ID (e.g., `2405.12345`). Keep on published papers that had preprints.                            |
| `doi`               | Digital Object Identifier.                                                                             |
| `needs_review`      | `{true}` — flags entries needing manual review.                                                        |

---

## Tag Vocabulary

Every entry must have 1–3 tags from this fixed vocabulary. Tags are pipe-separated in the `tags` field, e.g., `tags = {Scaling Data Curation | Training Language Models}`.

| Tag                                                     | Description                                                                                                                                                                           |
| ------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Training Language Models`                              | LM pretraining, architecture, training recipes (OLMo, OLMoE, FlexOlmo, etc.)                                                                                                          |
| `Scaling Data Curation`                                 | Training data, corpora, data mixing, filtering (Dolma, DCLM, Olmix, etc.)                                                                                                             |
| `Fundamentals of LM Evaluation`                         | Benchmarks, metrics, evaluation methodology (Paloma, Signal & Noise, Fluid, etc.)                                                                                                     |
| `AI for Science`                                        | NLP for scientific documents, citation analysis, literature graphs (S2ORC, SciBERT, PaperMage, TLDR, etc.)                                                                            |
| `Retrieval-Augmented LMs`                               | Search, retrieval models, claim verification (SciFact, RouterRetriever, FollowIR, etc.)                                                                                               |
| `AI-powered Reading Interfaces`                         | Augmented reading, paper UIs (Semantic Reader, ScholarPhi, CiteSee, Scim, etc.)                                                                                                       |
| `Summarization, Simplification, Information Extraction` | Summarization, text simplification, relation extraction, table extraction, definition detection (BooookScore, FABLES, Multi-LexSum, Paper Plain, MultiCite, PaperMage, SciRIFF, etc.) |
| `Long Context`                                          | Long-document understanding, book-length tasks (BooookScore, NoCha, LongEval, etc.)                                                                                                   |
| `OCR`                                                   | Document processing, PDF extraction (olmOCR, VILA, etc.)                                                                                                                              |
| `Responsible AI`                                        | Data governance, responsible development, bias (FAccT, ROOTS, etc.)                                                                                                                   |
| `Explainable AI`                                        | AI explanations, advice taking, interpretability (LIMEADE, etc.)                                                                                                                      |
| `Mixture of Experts`                                    | MoE architectures (OLMoE, FlexOlmo, etc.)                                                                                                                                             |
| `Vision-Language`                                       | VLMs, multimodal models (Molmo, olmOCR, DrawEduMath, etc.)                                                                                                                            |
| `AI for Education`                                      | Educational applications, math reasoning in curricula (MathFish, DrawEduMath, etc.)                                                                                                   |
| `AI for Biomedicine`                                    | Clinical text, biomedical ontologies, COVID-19, pandemic NLP (CORD-19, TREC-COVID, Feldman2019, etc.)                                                                                 |
| `Domain Adaptation, Specialization, Generalization`     | Domain-specific pretraining, transfer learning (Don't Stop Pretraining, SciBERT, etc.)                                                                                                |
| `Science of Science`                                    | Metascience, research practices, open science, citation analysis (Rise of Open Science, Citation Count Analysis, etc.)                                                                |
| `Workshops and Tutorials`                               | Workshop overviews, shared tasks, tutorials (SDP, SciVer, etc.)                                                                                                                       |

---

## Fields to NOT Include

Do not add these fields to entries:

`pages`, `publisher`, `number`, `address`, `editor`, `organization`, `isbn`, `issn`, `numpages`, `articleno`, `series`, `location`, `keywords`, `issue_date`, `day`, `eprint`

## Optional Paper-ID Fields

These fields store alternate identifiers that enable linking to specific publisher pages. They are optional but should be preserved when present:

| Field           | Description                                              |
| --------------- | -------------------------------------------------------- |
| `acl`           | ACL Anthology ID (e.g., `2024.acl-long.841`)             |
| `acm`           | ACM Digital Library ID (e.g., `10.1145/3544548.3580847`) |
| `openreview`    | OpenReview ID (e.g., `z1d8fUiS8Cr`)                      |
| `nature`        | Nature article ID (e.g., `s41597-022-01533-w`)           |
| `sciencedirect` | ScienceDirect article ID                                 |
| `oup`           | Oxford University Press article path                     |
| `pmc`           | PubMed Central ID (e.g., `PMC8025972`)                   |
| `jama`          | JAMA Network article ID                                  |
| `aaai`          | AAAI article path                                        |

---

## Field Ordering

Fields within an entry should be in alphabetical order:

`abstract`, `arxiv`, `author`, `award`, `bibtex_show`, `booktitle`, `cv_authors_after`, `cv_authors_before`, `doi`, `journal`, `month`, `needs_review`, `pdf`, `preview`, `selected`, `tags`, `title`, `url`, `volume`, `year`

---

## Entry Sorting

Entries in `papers.bib` are sorted in **reverse chronological order** (newest first):

1. By `year` (descending)
2. By `month` (descending within the same year)

---

## Pinned Entries

Some entries don't fit standard categories. These must be preserved exactly as documented here. If you encounter one of these entries, use the exact format below — do not modify their fields or structure to match general rules.

### peS2o Dataset (Technical Report)

```bibtex
@article{Soldaini2023PeS2oPretraining,
  author       = {Luca Soldaini and Kyle Lo},
  bibtex_show  = {true},
  journal      = {Allen Institute for AI, Tech. Rep},
  needs_review = {true},
  pdf          = {pes2o-pretraining-efficiently-on-s2orc-dataset.pdf},
  preview      = {pes2o-pretraining-efficiently-on-s2orc-dataset.png},
  title        = {peS2o (Pretraining Efficiently on S2ORC) Dataset},
  url          = {https://scholar.google.com/scholar?cluster=2312374705071487035&hl=en&oi=scholarr},
  year         = {2023},
}
```

### CORD-19 Dataset (Workshop paper at NLP for COVID-19)

```bibtex
@inproceedings{Wang2020CordNineteen,
  abstract    = {...},
  author      = {Lucy Lu Wang and Kyle Lo and ...},
  bibtex_show = {true},
  booktitle   = {NLP for COVID-19 Workshop},
  month       = {Jul},
  pdf         = {cord-19-the-covid-19-open-research-dataset.pdf},
  preview     = {cord-19-the-covid-19-open-research-dataset.png},
  title       = {{CORD-19}: The {COVID-19} Open Research Dataset},
  url         = {https://aclanthology.org/2020.nlpcovid19-acl.1},
  year        = {2020}
}
```

### Epidemic QA (Text Analysis Conference)

```bibtex
@inproceedings{Goodwin2020OverviewEpidemic,
  abstract     = {...},
  author       = {Travis R Goodwin and Dina Demner-Fushman and Kyle Lo and Lucy Lu Wang and William R Hersh and HT Dang and Ian M Soboroff},
  bibtex_show  = {true},
  booktitle    = {Text Analysis Conference},
  needs_review = {true},
  pdf          = {overview-of-the-2020-epidemic-question-answering-track.pdf},
  preview      = {overview-of-the-2020-epidemic-question-answering-track.png},
  title        = {Overview of the 2020 epidemic question answering track},
  url          = {https://tac.nist.gov/publications/2020/additional.papers/TAC2020.EPIC-QA.overview.notebook.pdf},
  year         = {2020},
}
```

### IoT COVID-19 Paper (needs review)

```bibtex
@article{Firouzi2021HarnessingPower,
  abstract     = {...},
  author       = {Farshad Firouzi and Bahar Farahani and ...},
  bibtex_show  = {true},
  journal      = {IEEE Internet of Things Journal},
  needs_review = {true},
  pdf          = {harnessing-the-power-of-smart-and-connected-health-to-tackle-covid-19-iot-ai-robotics-and-blockchain-for-a-better-world.pdf},
  preview      = {harnessing-the-power-of-smart-and-connected-health-to-tackle-covid-19-iot-ai-robotics-and-blockchain-for-a-better-world.png},
  title        = {Harnessing the power of smart and connected health to tackle COVID-19: IoT, AI, robotics, and blockchain for a better world},
  url          = {https://ieeexplore.ieee.org/abstract/document/9406879/},
  year         = {2021},
}
```

---

## Complete Example: New ArXiv Preprint

```bibtex
@article{Lo2025ExamplePreprint,
  abstract    = {We present a new method for...},
  arxiv       = {2501.12345},
  author      = {Kyle Lo and Jane Doe and John Smith},
  bibtex_show = {true},
  journal     = {ArXiv},
  month       = {Jan},
  pdf         = {example-preprint-title.pdf},
  preview     = {example-preprint-title.png},
  tags        = {Scaling Data Curation | Training Language Models},
  title       = {Example Preprint Title},
  url         = {https://arxiv.org/abs/2501.12345},
  volume      = {2501.12345},
  year        = {2025},
}
```

## Complete Example: Published Conference Paper

```bibtex
@inproceedings{Lo2025ExampleConference,
  abstract    = {We present a new method for...},
  arxiv       = {2501.12345},
  author      = {Kyle Lo and Jane Doe and John Smith},
  award       = {Best Paper Award},
  bibtex_show = {true},
  booktitle   = {ACL},
  doi         = {10.18653/v1/2025.acl-long.123},
  month       = {Jul},
  pdf         = {example-conference-paper.pdf},
  preview     = {example-conference-paper.png},
  selected    = {true},
  tags        = {AI for Science, Evaluation},
  title       = {Example Conference Paper},
  url         = {https://aclanthology.org/2025.acl-long.123},
  year        = {2025},
}
```

## Complete Example: Published Journal Paper

```bibtex
@article{Lo2025ExampleJournal,
  abstract    = {We present a new method for...},
  arxiv       = {2501.12345},
  author      = {Kyle Lo and Jane Doe and John Smith},
  bibtex_show = {true},
  doi         = {10.1038/s41586-025-00000-0},
  journal     = {Nature},
  month       = {Feb},
  pdf         = {example-journal-paper.pdf},
  preview     = {example-journal-paper.png},
  tags        = {AI for Science},
  title       = {Example Journal Paper},
  url         = {https://www.nature.com/articles/s41586-025-00000-0},
  volume      = {620},
  year        = {2025},
}
```
