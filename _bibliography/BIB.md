# BibTeX Field Requirements

This document specifies the required BibTeX fields for papers on the website.

## Universal Fields (All Papers)

These fields are **required for all papers**:

- `title` - Paper title
- `author` - Authors in "Name1 and Name2 and Name3" format
- `url` - Link to paper (DOI URL, arXiv URL, or paper website)
- `month` - Publication month (jan, feb, mar, etc.)
- `year` - Publication year

## Entry Type Specific Fields

### Conference Papers (`@inproceedings`)

**Required:**
- `booktitle` - Name of the conference (e.g., "Proceedings of ACL 2024")

**Optional:**
- `doi` - Digital Object Identifier (common for ACM conferences)

**Example:**
```bibtex
@inproceedings{Lo2024ExamplePaper,
  title = {Example Conference Paper},
  author = {Kyle Lo and Jane Doe},
  booktitle = {Proceedings of ACL 2024},
  month = aug,
  year = {2024},
  url = {https://aclanthology.org/2024.acl-long.123},
  doi = {10.18653/v1/2024.acl-long.123}
}
```

### Journal Papers (`@article`)

**Required:**
- `journal` - Name of the journal
- `volume` - Volume number
- `doi` - Digital Object Identifier

**Example:**
```bibtex
@article{Lo2024ExampleJournal,
  title = {Example Journal Paper},
  author = {Kyle Lo and Jane Doe},
  journal = {Nature Machine Intelligence},
  volume = {6},
  month = mar,
  year = {2024},
  url = {https://doi.org/10.1038/s42256-024-00000-0},
  doi = {10.1038/s42256-024-00000-0}
}
```

### ArXiv Preprints (`@article`)

**Required:**
- `journal` - Must be "ArXiv" (case-insensitive)
- `volume` - ArXiv ID (e.g., "2024.12345")

**Optional:**
- `doi` - Typically not present for preprints

**Example:**
```bibtex
@article{Lo2024ExampleArxiv,
  title = {Example ArXiv Preprint},
  author = {Kyle Lo and Jane Doe},
  journal = {ArXiv},
  volume = {2405.12345},
  month = may,
  year = {2024},
  url = {https://arxiv.org/abs/2405.12345}
}
```

## Fields to Exclude

The following fields should **not** be generated or scored:

- `pages` - Not required
- `publisher` - Not required
- `abstract` - Too long, not needed for bibliography
- `number` - Not required
- `address` - Not required
- `editor` - Not required
- `organization` - Not required

## Entry Type Selection Rules

1. If venue contains "proceedings", "conference", "workshop", "symposium" → `@inproceedings`
2. If venue contains "arxiv" (case-insensitive) → `@article` with journal="ArXiv"
3. If venue contains "journal", "transactions", or is from a known journal → `@article`
4. Default fallback → `@article`

## Month Format

Months should use BibTeX abbreviations (no quotes):
- `jan`, `feb`, `mar`, `apr`, `may`, `jun`, `jul`, `aug`, `sep`, `oct`, `nov`, `dec`

## Scoring Criteria

When evaluating generated BibTeX against ground truth:

1. **Universal fields** (5 fields): title, author, url, month, year
2. **Entry-type specific fields**:
   - Conference: +1 for booktitle, +1 for doi (if present in ground truth)
   - Journal: +3 for journal, volume, doi
   - ArXiv: +2 for journal, volume

**Score = (matching fields) / (total required fields in ground truth)**

Similarity threshold for matching: 85%
