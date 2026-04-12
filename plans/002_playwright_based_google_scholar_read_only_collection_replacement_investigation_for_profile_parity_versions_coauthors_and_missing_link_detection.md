# Playwright-Based Google Scholar Read-Only Collection Replacement Investigation for Profile Parity, Versions, Coauthors, and Missing-Link Detection

## Why This File Exists

This file defines the medium-term investigation plan for replacing or supplementing `scholarly` with a **logged-in, read-only Playwright workflow** for Google Scholar data collection.

This is not a mutation/automation plan for add, merge, edit, or delete actions. It is a **data collection parity investigation** only.

The purpose is to determine whether a persistent, human-supervised browser session can safely and reliably gather the Scholar data needed to support later hygiene workflows:

- paper backfilling
- version / cluster discovery
- coauthor comparison
- missing-paper detection
- under-clustering detection
- metadata anomaly review

This file is meant to be resumable in a later session with minimal re-discovery.

## Current Findings Snapshot

As of April 11, 2026, the Playwright investigation has cleared all major read-only parity surfaces, including the previously hardest one: the logged-in `Add articles` modal.

Confirmed working:

- logged-in profile-page capture
- offline profile-row parsing
- paper-detail capture and parsing
- versions-page capture and parsing
- bounded coauthor profile capture and parsing
- logged-in `Add articles` modal capture and offline parsing

Most important concrete result:

- a real missing-paper candidate was captured from the `Add articles` UI on the `kyle lo` query, page `131-140`
- the candidate row was:
  - `Cord-19: The COVID-19 open research dataset. arXiv 2020`
  - `doc_id = lY3Lk2jqby8J`
  - `cluster = 3418208377074584981`
  - `in_profile = false`
- artifacts:
  - `plans/artifacts/scholar_ui/current_page_20260411_112522.html`
  - `plans/artifacts/scholar_ui/current_page_20260411_112522.png`
  - `plans/artifacts/scholar_ui/current_page_20260411_112522_capture.json`
  - `plans/artifacts/scholar_ui/current_page_20260411_112522_add_articles.json`

Operational conclusion:

- trying to log into a Playwright-launched browser directly failed because Google flagged the browser as insecure
- the reliable workflow is:
  - launch your own Chrome with remote debugging
  - log in manually there
  - attach Playwright to that existing Chrome session over CDP
  - capture the already-open Scholar tab without navigation

This should now be treated as the default investigation workflow.

Repo capability added after the initial read-only parity pass:

- `scripts/investigate_scholar_ui.py` now supports immediate `Add articles` parsing into `*_add_articles.json`
- the same investigator now supports bounded capture of up to 3 `Add articles` pages in one supervised run
- important implementation detail discovered during live validation:
  - raw navigation to the parsed `data-next` URL did not preserve modal state reliably
  - using the modal's own `Next` button and verifying that `#gsc_iadb_data[data-start]` changes does work

Live validation result now recorded:

- page `141-150` capture succeeded live:
  - `plans/artifacts/scholar_ui/current_page_20260411_145716_add_articles.json`
- page `151-160` capture succeeded live via modal-next pagination:
  - `plans/artifacts/scholar_ui/current_page_20260411_145725_add_articles.json`
- page-2 evidence confirms true advancement:
  - `start = 151`
  - `end = 160`
  - distinct `doc_id` set from page 1
- page-3 live validation also succeeded via the same modal-next path:
  - `plans/artifacts/scholar_ui/current_page_20260411_152058_add_articles.json`
  - `plans/artifacts/scholar_ui/current_page_20260411_152106_add_articles.json`
  - `start = 161`, `end = 170`
  - `start = 171`, `end = 180`
- curated multi-query scan loop also succeeded live after hardening query turnover and modal-button activation:
  - `plans/artifacts/scholar_ui/current_page_20260411_154755_add_articles.json`
  - `plans/artifacts/scholar_ui/current_page_20260411_154825_add_articles.json`
  - `plans/artifacts/scholar_ui/current_page_20260411_154856_add_articles.json`
  - query-to-query transitions now preserve modal state while rewinding each new query to page 1 before capture
- a file-based wrapper now exists for curated scans:
  - `scripts/run_scholar_add_articles_scan.py`
  - query file:
    - `plans/artifacts/scholar_ui/curated_queries.txt`
- the curated query set has been updated from historical examples to the current operational set:
  - `Kyle Lo`
  - `"OpenScholar"`
  - `olmo 2 furious`
- `olmo 2 furious` is now a confirmed high-value under-clustering query family:
  - page 1:
    - `plans/artifacts/scholar_ui/current_page_20260411_171606_add_articles.json`
  - page 2:
    - `plans/artifacts/scholar_ui/current_page_20260411_171615_add_articles.json`
  - page 3:
    - `plans/artifacts/scholar_ui/current_page_20260411_171624_add_articles.json`
  - review note:
    - `plans/artifacts/scholar_ui/olmo_2_furious_review_notes.md`
- detector and review output have been updated to make this evidence actionable:
  - under-clustered review now shows the profile anchor plus related in-profile and not-in-profile variants
  - targeted query bundles such as `olmo 2 furious` are now preferred over weaker broad-query candidates when both match the same paper family
- add-articles artifact loading is now explicitly robust to empty scans:
  - zero-row artifacts do not supersede previously captured positive evidence
  - this matters especially for broad discovery queries such as `Kyle Lo`

## Fully Validated End-To-End Cases

Two full human-fix / evidence-refresh / detector-refresh loops have now been validated.

### Case 1: Under-clustering / unlinked variant

Paper:

- `CORD-19: The COVID-19 Open Research Dataset`

Pre-fix evidence:

- query: `kyle lo`
- add-articles page: `131-140`
- candidate:
  - `Cord-19: The COVID-19 open research dataset. arXiv 2020`
  - `doc_id = lY3Lk2jqby8J`
  - `cluster = 3418208377074584981`
  - `in_profile = false`
- artifacts:
  - `plans/artifacts/scholar_ui/current_page_20260411_112522_add_articles.json`

Manual action performed:

- add the arXiv row to the profile
- merge it with the existing CORD-19 profile entry

Post-fix evidence:

- same query / same page recaptured
- same `doc_id`
- row became `in_profile = true`
- artifacts:
  - `plans/artifacts/scholar_ui/current_page_20260411_114842_add_articles.json`

System change required:

- add-articles artifacts must be freshness-aware
- newest artifact for the same `doc_id` must supersede older contradictory artifacts

Outcome:

- after freshness handling was added, the under-clustering issue disappeared naturally

### Case 2: True missing-paper case

Paper:

- `GORC: A large contextual citation graph of academic papers`

Pre-fix evidence:

- query: `Kyle Lo`
- add-articles page: `141-150`
- candidate:
  - `GORC: A large contextual citation graph of academic papers`
  - `doc_id = _CPxyc95K8sJ`
  - `cluster = 14639928947051144188`
  - `in_profile = false`
- artifacts:
  - `plans/artifacts/scholar_ui/current_page_20260411_120156_add_articles.json`

Manual action performed:

- add the GORC row to the profile

Post-fix evidence:

- same query / same page recaptured
- same `doc_id`
- row became `in_profile = true`
- artifacts:
  - `plans/artifacts/scholar_ui/current_page_20260411_120358_add_articles.json`

Outcome:

- after refreshing evidence and rerunning detection, missing-paper review returned `No issues found.`

## Detector/Product Lessons Learned

These implementation lessons are now established and should not need to be rediscovered.

### 1. Add-articles evidence must be treated as time-varying

- A parsed `Add articles` artifact is not evergreen.
- Once a paper is added or merged, older artifacts may become stale and misleading.
- Artifact loading must prefer the newest evidence for a stable candidate key, currently `doc_id`.

### 2. Missing-paper detection must ignore `in profile` rows

- An add-articles candidate already marked `in profile` is not evidence of a missing paper.
- This created false positives until the detector was tightened.

### 3. Add-articles evidence supports two distinct issue types

- `missing_profile_article`
  - when no convincing profile match exists and add-articles shows a candidate not in profile
- `under_clustered_profile_article`
  - when a convincing profile match already exists but add-articles shows an additional candidate not yet in profile that likely belongs in the same cluster

### 4. CLI review should surface UI evidence directly

For add-articles-backed issues, review output should include:

- candidate title
- candidate `doc_id`
- candidate Scholar URL
- local artifact path

This materially speeds up manual Scholar cleanup.

### 5. Add-articles evidence is now a first-class CLI surface

The hygiene CLI now exposes the newest known add-articles evidence directly:

- `python3 scripts/scholar_hygiene.py evidence add-articles --status not-in-profile --limit 20`
- `python3 scripts/scholar_hygiene.py evidence add-articles --status in-profile --limit 20`

This command:

- deduplicates by stable candidate key, currently `doc_id`
- prefers the newest artifact for each candidate
- shows title, `doc_id`, query, Scholar URL, and artifact path

This is now the preferred way to inspect the current add-articles queue outside raw JSON.

## Additional Repeated Validation

After the initial CORD-19 and GORC validations, the same workflow was repeated successfully on:

- `Longchecker: Improving scientific claim verification by modeling full-abstract context`

Evidence:

- pre-fix:
  - `doc_id = 6VRrsR6nJ60J`
  - `in_profile = false`
  - artifact: `plans/artifacts/scholar_ui/current_page_20260411_132053_add_articles.json`
- post-fix:
  - same `doc_id`
  - `in_profile = true`
  - artifact: `plans/artifacts/scholar_ui/current_page_20260411_132400_add_articles.json`

This repeated validation matters because it shows the workflow is not a one-off success. The loop is stable across multiple real papers:

1. capture pre-fix add-articles evidence
2. manually add / merge in Scholar
3. capture post-fix evidence
4. rerun detector
5. newest artifact supersedes stale evidence
6. queue updates naturally

## Readiness Assessment

The read-only browser path is now sufficiently investigated to move to the next phase.

What is considered done:

- authenticated read-only capture is viable through CDP-attached Chrome
- all major read-only data surfaces have been parsed successfully
- add-articles evidence has been integrated into the hygiene system
- stale-vs-fresh artifact behavior is handled
- both missing-paper and under-clustering loops have been validated end to end
- bounded same-tab add-articles pagination is live-validated through page 3
- curated multi-query add-articles scanning is live-validated
- a file-based wrapper exists for rerunning curated scans safely
- detector and review output now surface the strongest targeted add-articles evidence instead of only broad-query matches

What is still optional, not blocking:

- improve selector robustness further
- investigate opening the add-articles modal automatically rather than attaching to an already-open tab
- investigate metadata-anomaly-specific browser captures

Conclusion:

- yes, this is enough to move on from pure read-only investigation into the next implementation phase: bounded assistive automation of add-articles scanning
- the remaining blocker is no longer evidence collection quality
- the remaining blocker is that actual Scholar mutations (`Add`, `Merge`, `Save`) are still manual

## Context From Prior Work

This investigation exists because the current `scholarly` path is operationally blocked.

Confirmed in `plans/001_google_scholar_hygiene_system_design_implementation_status_and_scraper_failure_debugging_resume_plan.md`:

- the refactored `1_` scraper is still SQLite-compatible
- the real temp-DB integration test reached Google Scholar
- Google Scholar returned a reCAPTCHA / anti-bot page for the public profile URL
- `scholarly` then failed while parsing the blocked page
- the scraper has since been hardened to fail safely with `ScholarCaptchaError`

The core issue is therefore:

- not local DB compatibility
- not the new wrapper design
- but anti-bot gating on direct scraping

This makes a browser-based, logged-in, low-rate path worth investigating.

## Investigation Goal

Determine whether Playwright can, in a safe and read-only way, collect all Scholar data required to reach functional parity with the current hygiene pipeline inputs.

“Parity” here means collecting enough data to later support:

1. Profile publication ingestion
2. Version / cluster evidence collection
3. Coauthor profile evidence collection
4. Missing-paper candidate discovery
5. Under-clustering evidence
6. Metadata anomaly evidence

The bar is not “general web scraping.” The bar is “can we extract the bounded Scholar data needed for the hygiene workflow without performing any account mutations.”

## Resume Workflow

When resuming this investigation in a later session, use this exact flow:

1. Launch Chrome manually with remote debugging enabled.
2. Log into Google Scholar in that Chrome session.
3. Navigate manually to the Scholar surface of interest.
4. Use `scripts/investigate_scholar_ui.py --cdp-url http://127.0.0.1:9222 --use-existing-page ...` to capture the already-open tab.
5. Parse the saved HTML offline with the dedicated parser for that page type.

For `Add articles`, the capture and parse steps can now be combined in one investigator run.

Important:

- do not rely on Playwright-created browser sessions for Google login
- do not open a fresh tab when the goal is to preserve an already-open modal state
- `--use-existing-page` is required when capturing an existing `Add articles` modal

## Current Repo State Relevant To This Investigation

### Existing Playwright Stub

There is already a minimal read-only helper:

- `scripts/investigate_scholar_ui.py`

Current behavior:

- opens your Scholar profile page
- optionally opens a search query
- headful browser only
- supports CDP attach to an existing logged-in Chrome session
- supports capture of the current page without navigation
- can parse captured `Add articles` pages immediately
- can perform bounded same-tab `Add articles` pagination capture with strict caps

This started as the seed of the Playwright investigation, but it is now materially closer to the data surfaces needed by the hygiene pipeline.

### Existing Data Consumers That Define Parity Needs

The current hygiene workflow expects enough data to support:

- `publications`
- `versions`
- `coauthors`
- issue detection for:
  - `missing_profile_article`
  - `under_clustered_profile_article`
  - `metadata_anomaly`

These expectations are embodied in:

- `scripts/scholar_hygiene/db.py`
- `scripts/scholar_hygiene/detector.py`
- `scripts/scholar_hygiene/coauthors.py`
- `scripts/scholar_hygiene/ingest.py`

The Playwright investigation must measure itself against those needs, not against an abstract scraping goal.

## Non-Negotiable Constraints

This investigation must remain within a strict read-only safety envelope.

### Allowed

- open Scholar pages in a real browser
- manually log in
- inspect DOM
- capture screenshots
- capture HTML snapshots
- extract visible metadata
- traverse a small number of directly relevant pages
- run very small, deliberate query experiments

### Not Allowed

- clicking Add / Merge / Save / Delete / Confirm actions
- bulk crawling across Scholar
- unattended large-scale harvesting
- parallel tabs doing repeated requests
- repeated reload loops
- paging through long result lists without strict caps
- any attempt to bypass anti-bot mechanisms

### Human Supervision Requirement

Early phases must be human-supervised:

- headful browser
- manual login
- no background daemon behavior
- explicit stop on CAPTCHA or unusual friction

## Safety Defaults For All Playwright Experiments

These defaults should be treated as hard rules unless a later note explicitly justifies changing them.

- Use one persistent browser context.
- Use one tab by default.
- Use headful mode only during investigation.
- Reuse the same authenticated session rather than repeatedly re-logging in.
- Wait 5-15 seconds between navigations by default.
- Do not issue more than a handful of page loads per run during early phases.
- Do not run multiple Scholar requests in parallel.
- Stop immediately if CAPTCHA appears.
- Stop immediately if the UI starts behaving unusually or selectors stop being stable.

### Suggested Initial Hard Caps Per Run

For early experiments, do not exceed:

- 1 profile page visit
- 5 paper detail page visits
- 5 versions-page visits
- 3 coauthor profile visits
- 3 add-articles candidate searches

These caps can be revisited later only if the session remains stable and clearly within a low-rate, human-guided pattern.

## Data Parity Targets

Playwright is only worth continuing if it can gather the data needed by the hygiene system.

### A. Own Profile Publication Row Parity

For each visible paper on your own Scholar profile, determine whether we can collect:

- displayed title
- displayed citation count
- displayed year
- row link or detail link
- publication / view URL
- any profile-specific identifier exposed in the URL or DOM

Why this matters:

- this is the minimum replacement for `publications` ingestion

### B. Paper Detail Parity

For each selected paper detail page, determine whether we can collect:

- canonical title
- author list
- venue / journal / conference / citation text
- publication year
- citation count
- “all versions” link if present
- URL-based identifiers
- any machine-usable paper / cluster handle

Why this matters:

- needed for metadata anomaly analysis
- needed for alignment between profile rows, local bibliography, and versions

### C. Versions / Cluster Parity

For each sampled paper with versions, determine whether we can collect:

- version page URL
- cluster-like identifier from URL if present
- version row title
- version row authors
- version row venue / year text
- version destination URL
- citation signal on the version page if present
- whether pagination exists
- how many pages were traversed

Why this matters:

- needed for under-linking discovery
- needed for under-clustering evidence
- needed for metadata anomaly evidence

### D. Coauthor Profile Parity

For each sampled coauthor profile, determine whether we can collect:

- coauthor name
- coauthor Scholar id / profile URL
- visible publication rows
- paper titles
- citation counts
- year
- detail links or view URLs

Why this matters:

- needed for citation-gap comparison
- needed for missing-paper and cluster-gap evidence

### E. Add-Articles Candidate Search Parity

This is the most sensitive and most valuable parity target.

Without mutating anything, determine whether the logged-in UI can safely expose candidate rows for a search query in the “Add articles” flow.

For each sampled query, determine whether we can collect:

- candidate title
- candidate authors
- candidate venue / year
- candidate citation count if shown
- any row URL / detail URL
- enough visible metadata to align the candidate to a known local paper

Why this matters:

- this is the key medium-term data source for under-linking / backfill support

If this is not viable, Playwright may still be useful for profile, paper-detail, versions, and coauthor scraping, but not for add-articles candidate discovery.

Status update:

- this parity target is now viable in a read-only workflow
- the live selector assumptions were initially wrong
- the real row structure is under `.gsc_iadb_art`, with paging metadata in `#gsc_iadb_data`, and the modal container `#gsc_md_iad`
- parsed add-articles snapshots can now be turned into structured evidence for missing-profile detection

## Investigation Phases

This must be run as a ladder with explicit go/no-go checks after each phase.

### Phase 0: Session Viability and Gating Check

Goal:

- verify a persistent Playwright profile can open Scholar in a manual-login session
- verify whether normal profile browsing is possible without immediate CAPTCHA

Actions:

- launch headful browser with persistent context
- open your profile page
- manually log in if needed
- reload once after login
- reopen the same page in the same session

Collect:

- screenshot of the loaded profile page
- raw HTML snapshot
- note whether login was required
- note whether CAPTCHA appeared

Success criteria:

- page content is readable from DOM
- no immediate CAPTCHA after normal profile open / reload

Stop conditions:

- CAPTCHA
- repeated login loops
- unexpected gate page

### Phase 1: Own-Profile Row Extraction

Goal:

- parse visible publication rows from your own profile page

Actions:

- inspect row selectors
- extract first-page visible rows only
- do not paginate yet

Collect:

- raw extracted JSON fixture for the first visible set of rows
- screenshot showing row structure
- selector notes

Compare against:

- current local DB sample
- current visible Scholar UI

Success criteria:

- stable extraction of title / citations / year / row link for visible rows
- enough data to align a sample of rows back to current `publications` records

### Phase 2: Paper Detail Extraction

Goal:

- parse paper detail pages linked from sampled profile rows

Actions:

- open 5-10 handpicked papers
- prefer a mix of clean papers and suspicious papers

Collect:

- per-paper detail JSON fixture
- raw HTML snapshot for each detail page
- screenshot for each detail page

Required fields:

- title
- authors
- venue text
- year
- citations
- versions link

Success criteria:

- stable extraction on a mixed sample
- enough metadata to support later detector inputs

### Phase 3: Versions / Cluster Extraction

Goal:

- parse “all versions” pages from sampled papers

Actions:

- select 5-10 papers known or suspected to have multiple versions
- open versions pages one by one
- follow pagination only if clearly necessary and only with strict caps

Collect:

- per-paper version JSON fixture
- version-page HTML snapshots
- screenshots
- extracted cluster-like identifier if present in URL

Success criteria:

- can extract enough fields to later populate the semantic equivalent of `versions`
- can identify whether pagination is manageable

### Phase 4: Coauthor Profile Extraction

Goal:

- determine whether coauthor profile browsing is stable and bounded in the same session

Actions:

- manually choose 3-5 coauthors first
- open their profile pages one at a time
- extract first-page visible publication rows only

Collect:

- coauthor profile fixtures
- screenshots
- note whether any coauthor profile visit changes rate-limit behavior

Success criteria:

- can capture bounded coauthor evidence without broad crawling
- can extract enough row data for later title/citation alignment

### Phase 5: Add-Articles Candidate Reading

Goal:

- determine whether the logged-in add/search flow can be used read-only to inspect candidate rows

Actions:

- use a tiny curated set of known paper queries
- navigate to the add/search UI
- enter the query
- wait for results
- read visible candidate rows only
- do not click add/select/confirm buttons

Collect:

- screenshots before and after search
- HTML snapshots if feasible
- candidate-row JSON fixtures
- note whether search itself increases blocking risk

Success criteria:

- candidate rows can be seen and parsed
- row metadata is rich enough to align back to local expected papers

Stop conditions:

- CAPTCHA
- warnings / unusual gating
- any UI state that looks close to mutation or confirmation workflows

### Phase 6: Parity Review and Decision

Goal:

- compare Playwright-collected data against the current hygiene pipeline input requirements

Possible outcomes:

1. Full read-only replacement candidate
2. Partial replacement candidate
3. Assistive navigation tool only
4. Not viable

Decision should be based on actual fixtures, not impressions.

## Incremental Testing Strategy

Every phase should be tested independently before composing them.

### Required Testing Pattern

For each page type:

1. Manual open and visual inspect
2. Capture screenshot
3. Capture HTML snapshot
4. Extract minimal JSON
5. Compare against expected fields
6. Note selector stability and page friction

Do not generalize selectors across page types prematurely.

### Minimal Sample Set For Initial Investigation

Use handpicked small samples:

- 1 clean profile page
- 5 profile rows
- 5 paper detail pages
- 5 version pages
- 3 coauthor profiles
- 3 add-articles queries

This is enough to establish viability without behaving like a crawler.

### Logging Requirements

Each run should record:

- date/time
- whether the browser session was already logged in
- pages visited
- delays used
- CAPTCHA seen or not
- fields successfully extracted
- parse failures
- selector names used
- notes about instability or risk

## Artifacts To Produce During This Investigation

This investigation should create durable evidence, not just code.

### Required Artifacts

- `plans/002_...md` itself
- a small run log per investigation session
- screenshots for each page type
- raw HTML snapshots for each page type
- extracted JSON fixtures for:
  - profile rows
  - paper details
  - versions pages
  - coauthor profile rows
  - add-articles candidate rows
- a parity matrix comparing Playwright fields to current hygiene inputs

### Parity Matrix Questions

The parity matrix should answer:

- can we replace current `publications` semantics?
- can we replace current `versions` semantics?
- can we replace current `coauthors` evidence semantics?
- can we support missing-paper detection?
- can we support under-clustering detection?
- can we support metadata anomaly review?
- where are the blind spots?

## Sample Scenarios To Include

The investigation should explicitly use and document a small curated sample of paper types.

### Scenario 1: Clean Profile Paper

Use a paper with straightforward metadata and no known issues.

Purpose:

- validate baseline row and detail extraction

### Scenario 2: Paper With Many Versions

Use a paper known to have multiple Scholar versions.

Purpose:

- validate versions-page extraction
- test pagination and cluster-handle capture

### Scenario 3: Suspected Metadata-Anomaly Paper

Use one of the papers currently surfacing in `metadata_anomaly`.

Purpose:

- check whether Playwright detail/versions collection is rich enough for anomaly review

### Scenario 4: Coauthored Paper With Citation Discrepancy Potential

Use a paper where a coauthor is likely to have stronger citation evidence.

Purpose:

- validate coauthor comparison viability

### Scenario 5: Suspected Missing-Paper Query

Use a query for a paper that is likely missing or historically difficult to find in “Add articles”.

Purpose:

- validate add-articles candidate reading

### Scenario 6: Blocking / Gating Case

Document any page that produces CAPTCHA, consent, or unusual friction.

Purpose:

- validate stop policy and evidence capture

## Intended Medium-Term Deliverables

If Playwright proves viable, the likely next medium-term deliverables are:

1. Persistent-session Playwright investigation tool with explicit read-only modes
2. Page-type-specific extractors:
   - profile rows
   - paper details
   - versions pages
   - coauthor profiles
   - add-articles candidates
3. Fixture-based parser tests using captured HTML
4. A parity adapter that converts Playwright JSON into the shapes needed by the hygiene pipeline

Current repo status:

- the persistent-session investigator exists in a basic but usable form
- offline parsers exist for profile, detail, versions, and add-articles snapshots
- add-articles artifacts are already wired into issue detection and CLI evidence review
- the remaining gap is broader live validation plus a cleaner parity adapter around browser-collected data

## Success Criteria

Playwright is a viable medium-term replacement candidate only if, in a low-rate, human-supervised, read-only workflow, it can reliably collect:

- your own profile publication rows
- paper detail metadata
- version-page data
- bounded coauthor evidence
- add-articles candidate rows for a tiny sampled query set

and it must do so with:

- lower practical blockage than direct `scholarly` scraping
- durable selectors or snapshot-based fallback parsing
- bounded, explainable navigation behavior

If one or more of these cannot be achieved safely, Playwright should be retained only as an assistive inspection tool, not the main ingestion replacement.

## Recommended First Steps When Resuming This Investigation

Resume in this order:

1. Expand `scripts/investigate_scholar_ui.py` into a persistent-session, read-only investigator.
2. Add screenshot + HTML snapshot capture for the profile page only.
3. Build profile-row extraction against one page only.
4. Build paper-detail extraction for 5 sampled papers.
5. Build versions-page extraction for 5 sampled papers.
6. Test 3 coauthor profiles.
7. Test 3 add-articles searches without mutating anything.
8. Produce the parity matrix before attempting any broader collection.

Current next practical step:

1. The bounded assistive Add Articles mutation phase is now complete enough to close.
2. Keep the completed add-phase notes and evidence in:
   - `plans/artifacts/scholar_ui/bounded_add_automation_summary_20260411.md`
3. The next phase should be separate from add automation:
   - bounded merge automation for newly attached families
   - or metadata-anomaly review if merge automation is deferred
4. Keep raw URL navigation out of mutation flows; use DOM-level Scholar actions only.

## Useful Commands To Remember

### Existing UI Investigation Seed

```bash
uv run playwright install chromium
uv run scripts/investigate_scholar_ui.py --query "\"paper title\""
```

### Current Add-Articles Resume Pattern

```bash
uv run scripts/investigate_scholar_ui.py \
  --cdp-url http://127.0.0.1:9222 \
  --use-existing-page \
  --capture-current-page \
  --wait-for-add-articles \
  --parse-add-articles \
  --capture-add-articles-pages 3
```

### Curated Multi-Query Scan Pattern

```bash
uv run scripts/investigate_scholar_ui.py \
  --cdp-url http://127.0.0.1:9222 \
  --use-existing-page \
  --capture-current-page \
  --wait-for-add-articles \
  --parse-add-articles \
  --capture-add-articles-pages 3 \
  --add-articles-query "Kyle Lo" \
  --add-articles-query "\"OpenScholar\"" \
  --add-articles-query "olmo 2 furious"
```

### File-Based Curated Scan Pattern

Create a small text file with up to 3 queries, one per line, for example:

```text
Kyle Lo
"OpenScholar"
olmo 2 furious
```

Then run:

```bash
uv run scripts/run_scholar_add_articles_scan.py plans/artifacts/scholar_ui/curated_queries.txt
```

## Resume Point For Next Session

If this session is lost, resume from here:

1. The read-only investigation and bounded add phase are considered complete enough to proceed.
2. The add queue checkpoint is:
   - `plans/artifacts/scholar_ui/bounded_add_automation_summary_20260411.md`
3. Use these artifacts first when resuming:
   - `plans/artifacts/scholar_ui/bounded_add_automation_summary_20260411.md`
   - `plans/artifacts/scholar_ui/olmo_2_furious_review_notes.md`
   - the latest `mutation_pre_*_capture.json` / `mutation_post_*_capture.json` files in `plans/artifacts/scholar_ui/`
4. Confirm the current post-add state with:
   - `python3 scripts/scholar_hygiene.py detect`
   - `python3 scripts/scholar_hygiene.py review --type under_clustered_profile_article`
   - `python3 scripts/scholar_hygiene.py review --type metadata_anomaly`
5. The next implementation phase should begin in a new plan or section dedicated to bounded merge automation or metadata cleanup.
6. If merge automation starts next, the first automation target should be:
   - selecting one reviewed merge family
   - performing one bounded merge action
   - recapturing evidence afterward to confirm the expected Scholar state change

### Current Hygiene Workflow For Comparison

```bash
uv run scripts/scholar_hygiene.py detect
uv run scripts/scholar_hygiene.py review --type missing_profile_article
uv run scripts/scholar_hygiene.py review --type under_clustered_profile_article
uv run scripts/scholar_hygiene.py review --type metadata_anomaly
```

These commands are useful as the comparison baseline for deciding whether Playwright-collected data reaches functional parity.
