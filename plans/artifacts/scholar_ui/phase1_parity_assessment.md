# Playwright Scholar Read-Only Parity Assessment: Profile, Detail, and Versions

## What Was Captured

The following read-only Scholar artifacts were successfully collected through a logged-in Playwright browser session:

- `profile_page_20260409_202233.html`
- `profile_page_20260409_202233.png`
- `detail_page_20260409_203515.html`
- `detail_page_20260409_203515.png`
- `detail_page_20260409_203952.html`
- `detail_page_20260409_203952.png`

The following offline parsed JSON artifacts were produced from those snapshots:

- `profile_page_20260409_202233_rows.json`
- `detail_page_20260409_203515_parsed.json`
- `detail_page_20260409_203952_versions.json`

## What Is Proven So Far

### 1. Logged-in browser access works

Playwright can launch a real Chromium browser, open Scholar, and remain stable in a human-supervised session.

This matters because the direct `scholarly` path currently fails on a CAPTCHA page for the public profile URL.

### 2. Profile row parity is viable

From the saved profile page and offline parser, we successfully extracted:

- visible article count label
- visible publication rows
- per-row title
- per-row detail URL
- per-row authors
- per-row venue text
- per-row citations
- per-row citation URL
- per-row year

This is enough to support a medium-term replacement for the visible-row portion of `publications` ingestion.

### 3. Detail-page parity is viable

From the saved paper detail page and offline parser, we successfully extracted:

- canonical title
- title URL
- PDF URL
- authors
- publication date
- venue/conference
- pages
- description
- total citation summary
- merged Scholar article snippets
- per-snippet links including `All 8 versions`

This is enough to support:

- metadata anomaly analysis
- paper identity resolution
- version-link discovery
- cluster-variant inspection

### 4. Versions-page parity is viable

From the saved versions/results page and offline parser, we successfully extracted:

- cluster id: `7377999893003631695`
- result count: `8`
- per-result rank
- per-result title
- per-result title URL
- per-result meta line
- per-result snippet
- per-result footer links

This is enough to support a medium-term replacement for much of the current `versions` evidence collection.

## Current Parity Against The Hygiene Pipeline

### `publications`-equivalent data

Status:

- mostly proven for visible rows

Already available from profile snapshot:

- title
- citations
- year
- authors
- venue text
- detail URL

Remaining gaps:

- better profile header parsing
- pagination / “show more” collection for rows beyond the first visible set
- a clean mapping from profile rows into the existing `publications.full_json`-style downstream shape

### `versions`-equivalent data

Status:

- strongly proven for one sampled cluster page

Already available from versions snapshot:

- cluster id
- per-version title
- per-version destination URL
- source/domain signal in meta
- snippet
- footer links

Remaining gaps:

- parser should split the `meta` line into authors / venue / year / source domain fields instead of leaving it as one string
- need to test one more versions page to ensure this was not a one-off structure
- need to check whether pagination exists on larger version sets

### Detail-page metadata parity

Status:

- strongly proven for one sampled paper

Already available:

- title
- authors
- publication date
- conference / venue
- pages
- description
- total citations
- merged Scholar article snippets

Remaining gaps:

- normalize field extraction into a cleaner downstream schema
- verify another detail page with a different structure, such as an arXiv paper or a metadata-anomaly case

### Coauthor parity

Status:

- not yet tested

Needed next:

- one bounded coauthor profile capture
- first-page visible rows only
- no broader crawl

### Add-articles candidate parity

Status:

- not yet tested

Needed next:

- one tiny read-only add-articles candidate search
- capture visible candidate rows only
- no clicks on add/select/confirm actions

## What Still Looks Risky Or Incomplete

### 1. Header parsing on the profile page

The current offline profile parser recovered rows correctly but misparsed the profile affiliation.

Interpretation:

- row extraction is strong
- header parsing needs refinement before relying on profile-level metadata

### 2. Result footer links still include non-read-only actions

The versions-page parser currently captures footer links such as:

- `Save`
- `Cite`

These are fine to parse as labels, but downstream logic should either:

- discard them, or
- explicitly mark them as non-target links

The important links for hygiene are things like:

- `Cited by ...`
- `Related articles`
- `View as HTML`

### 3. Current parsed shapes are investigation artifacts, not final ingestion schema

The JSON files produced so far are useful proof artifacts, but they are not yet drop-in replacements for:

- `publications.full_json`
- `versions.source_json`
- `coauthors.source_json`

An adapter layer will be needed later if this path is promoted into the main pipeline.

## Recommended Next Live Test

The next bounded live Playwright test should be:

### One coauthor profile capture

Why this is the next highest-value step:

- coauthor evidence is currently the biggest missing piece in the hygiene workflow
- it is required for missing-paper and under-clustering evidence
- it tests whether the logged-in browser session remains stable when moving from your profile to another Scholar profile

Safety constraints for that test:

- exactly one coauthor profile
- single page only
- no pagination
- screenshot + HTML snapshot only
- then offline parse

## Recommended Next Offline Work

Before or after the coauthor test:

- improve the profile header parser
- split versions-page `meta` into structured fields
- create a small parity matrix mapping:
  - profile rows -> `publications`
  - detail page -> metadata anomaly inputs
  - versions page -> `versions`

## Current Conclusion

At this point, Playwright has already demonstrated meaningful medium-term read-only viability for:

- profile browsing
- profile-row extraction
- detail-page capture
- merged-cluster inspection
- versions-page capture
- cluster-id extraction

The biggest unproven parts are now:

- coauthor profile collection
- add-articles candidate collection

If coauthor collection also works in the same low-rate read-only mode, then Playwright becomes a serious candidate to replace a large part of the current `scholarly` ingestion path.
