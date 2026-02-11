# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "python-slugify",
# ]
# ///
"""
Auto-generate gold BibTeX from Google Scholar data.

Loads papers from the Scholar DB, preserves existing papers.bib entries,
and generates new entries for unmatched papers using comprehensive rules.
Flags incomplete entries with needs_review={true}.

Call:
    uv run scripts/6_auto_generate_bib.py
    uv run scripts/6_auto_generate_bib.py --dry-run   # preview without writing

Output:
    _bibliography/papers.bib (updated with new entries)
"""

import argparse
import json
import os
import re
import sqlite3
from difflib import SequenceMatcher

DB_FILE = os.path.join(os.path.dirname(__file__), "../_bibliography/gscholar_export.db")
BIB_FILE = os.path.join(os.path.dirname(__file__), "../_bibliography/papers.bib")


# ---------------------------------------------------------------------------
# Venue normalization table
# Maps substrings (lowercased) found in Scholar venue strings to short names.
# Order matters: first match wins, so put more specific patterns first.
# ---------------------------------------------------------------------------
VENUE_RULES: list[tuple[str, str, str]] = [
    # (substring to match in lowercase venue, short_name, type)
    # type is "conference" or "journal"

    # --- Major ML/AI conferences ---
    ("computer vision and pattern recognition", "CVPR", "conference"),
    ("cvpr", "CVPR", "conference"),
    ("international conference on computer vision", "ICCV", "conference"),
    ("iccv", "ICCV", "conference"),
    ("european conference on computer vision", "ECCV", "conference"),
    ("eccv", "ECCV", "conference"),
    ("neural information processing systems", "NeurIPS", "conference"),
    ("neurips", "NeurIPS", "conference"),
    ("nips", "NeurIPS", "conference"),
    ("international conference on machine learning", "ICML", "conference"),
    ("icml", "ICML", "conference"),
    ("international conference on learning representations", "ICLR", "conference"),
    ("iclr", "ICLR", "conference"),
    ("aaai conference on artificial intelligence", "AAAI", "conference"),
    ("aaai", "AAAI", "conference"),
    ("international joint conference on artificial intelligence", "IJCAI", "conference"),
    ("ijcai", "IJCAI", "conference"),
    ("conference on language modeling", "COLM", "conference"),
    ("colm", "COLM", "conference"),

    # --- NLP conferences ---
    ("empirical methods in natural language processing", "EMNLP", "conference"),
    ("emnlp", "EMNLP", "conference"),
    ("north american chapter of the association for computational linguistics", "NAACL", "conference"),
    ("naacl", "NAACL", "conference"),
    ("association for computational linguistics", "ACL", "conference"),
    ("acl", "ACL", "conference"),
    ("european chapter of the association for computational linguistics", "EACL", "conference"),
    ("eacl", "EACL", "conference"),
    ("computational linguistics", "CoNLL", "conference"),  # careful - also a journal name
    ("conll", "CoNLL", "conference"),

    # --- IR conferences ---
    ("sigir", "SIGIR", "conference"),
    ("information retrieval", "SIGIR", "conference"),
    ("web search and data mining", "WSDM", "conference"),
    ("wsdm", "WSDM", "conference"),

    # --- HCI conferences ---
    ("chi conference on human factors", "CHI", "conference"),
    ("chi conference", "CHI", "conference"),

    # --- Systems/Web ---
    ("world wide web", "WWW", "conference"),
    ("www", "WWW", "conference"),
    ("knowledge discovery and data mining", "KDD", "conference"),
    ("kdd", "KDD", "conference"),

    # --- Workshops (keep full name but mark as conference) ---
    ("scholarly document processing", "Workshop on Scholarly Document Processing", "conference"),
    ("findings of", "Findings", "conference"),

    # --- Journals ---
    ("transactions of the association for computational linguistics", "Transactions of ACL (TACL)", "journal"),
    ("tacl", "Transactions of ACL (TACL)", "journal"),
    ("nature", "Nature", "journal"),
    ("science", "Science", "journal"),
    ("acm transactions on computer-human interaction", "ACM Transactions on Computer-Human Interaction", "journal"),
    ("journal of the american medical informatics", "JAMIA", "journal"),
    ("journal of biomedical informatics", "Journal of Biomedical Informatics", "journal"),
    ("bioinformatics", "Bioinformatics", "journal"),
    ("plos one", "PLOS ONE", "journal"),
    ("advances in neural information processing systems", "NeurIPS", "conference"),

    # --- ArXiv (must come after conference checks) ---
    ("arxiv preprint", "ArXiv", "journal"),
    ("arxiv", "ArXiv", "journal"),
]

# Conference month schedule: normalized venue name -> typical month abbreviation
CONFERENCE_MONTHS: dict[str, str] = {
    "AAAI": "Feb",
    "ICLR": "May",
    "CHI": "May",
    "WWW": "May",
    "NAACL": "Jun",
    "CVPR": "Jun",
    "ACL": "Jul",
    "ICML": "Jul",
    "SIGIR": "Jul",
    "KDD": "Aug",
    "ICCV": "Oct",
    "ECCV": "Oct",
    "COLM": "Oct",
    "EMNLP": "Nov",
    "NeurIPS": "Dec",
    "CoNLL": "Nov",
    "EACL": "May",
    "WSDM": "Mar",
    "Findings": "Nov",
    "IJCAI": "Aug",
}

ARXIV_MONTH_MAP = {
    "01": "Jan", "02": "Feb", "03": "Mar", "04": "Apr",
    "05": "May", "06": "Jun", "07": "Jul", "08": "Aug",
    "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dec",
}

MONTH_TO_SCORE = {
    "jan": 0, "feb": 1, "mar": 2, "apr": 3, "may": 4, "jun": 5,
    "jul": 6, "aug": 7, "sep": 8, "oct": 9, "nov": 10, "dec": 11,
}


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def normalize_title(title: str) -> str:
    """Normalize a title for fuzzy matching: lowercase, strip punctuation/whitespace."""
    t = title.lower()
    t = re.sub(r"[^a-z0-9\s]", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def titles_match(a: str, b: str, threshold: float = 0.85) -> bool:
    """Check if two titles match using normalized comparison."""
    na, nb = normalize_title(a), normalize_title(b)
    if na == nb:
        return True
    # Check substring containment
    if na in nb or nb in na:
        return True
    return SequenceMatcher(None, na, nb).ratio() >= threshold


def extract_arxiv_id(text: str) -> str:
    """Extract arXiv ID from a string (venue, URL, citation)."""
    match = re.search(r"(?:arXiv[:\s]+)?(\d{4}\.\d{4,5})", text, re.IGNORECASE)
    return match.group(1) if match else ""


def slugify_title(title: str) -> str:
    """Convert title to slug for PDF/preview filenames."""
    from slugify import slugify as _slugify
    return _slugify(title, replacements=[("'", "")])


def generate_bibtex_key(title: str, author: str, year: str) -> str:
    """Generate a BibTeX citation key like 'LastName2024TitleWords'."""
    if author:
        first_author = author.split(" and ")[0].strip()
        last_name = first_author.split()[-1]
        last_name = re.sub(r"[^a-zA-Z]", "", last_name)
    else:
        last_name = "Unknown"

    if title:
        title_words = title.split()[:3]
        title_part = "".join(
            w.capitalize() for w in title_words if w.lower() not in ("a", "an", "the")
        )
        title_part = re.sub(r"[^a-zA-Z0-9]", "", title_part)
    else:
        title_part = "Paper"

    return f"{last_name}{year}{title_part}"


def extract_month_from_citation(citation: str) -> str:
    """Extract month from citation string if present."""
    month_map = {
        "january": "Jan", "february": "Feb", "march": "Mar",
        "april": "Apr", "may": "May", "june": "Jun",
        "july": "Jul", "august": "Aug", "september": "Sep",
        "october": "Oct", "november": "Nov", "december": "Dec",
    }
    citation_lower = citation.lower()
    for month_name, month_abbr in month_map.items():
        if month_name in citation_lower:
            return month_abbr
    return ""


def classify_venue(venue: str) -> tuple[str, str, str]:
    """
    Classify a venue string into (short_name, entry_type, venue_type).

    Returns:
        (short_name, entry_type, venue_type)
        entry_type is "inproceedings" or "article"
        venue_type is "conference", "journal", or "unknown"
    """
    venue_lower = venue.lower()

    for pattern, short_name, vtype in VENUE_RULES:
        if pattern in venue_lower:
            entry_type = "inproceedings" if vtype == "conference" else "article"
            return short_name, entry_type, vtype

    # Check for generic conference keywords
    if any(kw in venue_lower for kw in ("proceedings", "conference", "workshop", "symposium")):
        return venue, "inproceedings", "conference"

    # Unknown
    if venue.strip():
        return venue, "article", "unknown"

    return "", "article", "unknown"


def infer_month(citation: str, venue_short: str, arxiv_id: str) -> str:
    """
    Infer publication month using cascading strategies.
    Returns month abbreviation (e.g., "Dec") or empty string.
    """
    # Try 1: from citation string
    month = extract_month_from_citation(citation)
    if month:
        return month

    # Try 2: from conference schedule
    if venue_short in CONFERENCE_MONTHS:
        return CONFERENCE_MONTHS[venue_short]

    # Try 3: from arxiv ID (YYMM.NNNNN)
    if arxiv_id and len(arxiv_id) >= 4:
        mm = arxiv_id[2:4]
        if mm in ARXIV_MONTH_MAP:
            return ARXIV_MONTH_MAP[mm]

    return ""


# ---------------------------------------------------------------------------
# Core: transform a Scholar paper into a BibTeX entry dict
# ---------------------------------------------------------------------------

def scholar_to_bibtex(paper_data: dict) -> tuple[dict, list[str]]:
    """
    Transform a Scholar paper JSON into a gold-quality BibTeX entry.

    Returns:
        (entry_dict, issues) where issues is a list of problems found.
    """
    bib = paper_data.get("bib", {})
    issues: list[str] = []

    title = bib.get("title", "")
    author = bib.get("author", "")
    year = str(bib.get("pub_year", ""))
    url = paper_data.get("pub_url", "")
    abstract = bib.get("abstract", "")
    citation = bib.get("citation", "")

    # Get venue from Scholar fields
    venue_raw = bib.get("conference") or bib.get("journal") or citation or ""

    # --- Rule 1: ArXiv ID extraction (from URL, citation, venue) ---
    arxiv_id = extract_arxiv_id(url) or extract_arxiv_id(citation) or extract_arxiv_id(venue_raw)

    # --- Rule 2: Venue classification ---
    venue_short, entry_type, venue_type = classify_venue(venue_raw)

    if venue_type == "unknown" and venue_raw.strip():
        issues.append(f"unrecognized venue: {venue_raw.strip()}")

    # --- Rule 3: Month inference ---
    month = infer_month(citation, venue_short, arxiv_id)
    if not month:
        issues.append("could not infer month")

    # --- Rule 4: Build entry ---
    entry = {
        "ID": generate_bibtex_key(title, author, year),
        "ENTRYTYPE": entry_type,
        "title": title,
        "author": author,
        "year": year,
        "url": url,
        "bibtex_show": "true",
    }

    if month:
        entry["month"] = month

    if abstract:
        entry["abstract"] = abstract
        if abstract.endswith("…") or abstract.endswith("..."):
            issues.append("abstract appears truncated")
    else:
        issues.append("missing abstract")

    # --- Rule 5: Entry-type-specific fields ---
    if entry_type == "inproceedings":
        if venue_short and venue_short != "ArXiv":
            entry["booktitle"] = venue_short
        elif venue_raw.strip():
            entry["booktitle"] = venue_raw.strip()
        else:
            issues.append("missing booktitle")
    else:
        # article
        if venue_short == "ArXiv":
            entry["journal"] = "ArXiv"
            if arxiv_id:
                entry["volume"] = arxiv_id
        elif venue_short:
            entry["journal"] = venue_short
        else:
            issues.append("missing journal")

    # --- Rule 6: ArXiv field ---
    if arxiv_id:
        entry["arxiv"] = arxiv_id

    # --- Rule 7: DOI extraction ---
    if url and "doi.org" in url:
        doi = url.split("doi.org/")[-1]
        if doi:
            entry["doi"] = doi

    # --- Rule 8: PDF and preview filenames ---
    slug = slugify_title(title)
    if slug:
        entry["pdf"] = f"{slug}.pdf"
        entry["preview"] = f"{slug}.png"

    # --- Rule 9: Flag for review if issues ---
    if issues:
        entry["needs_review"] = "; ".join(issues)

    return entry, issues


# ---------------------------------------------------------------------------
# BibTeX I/O (hand-rolled to preserve gold formatting exactly)
# ---------------------------------------------------------------------------

def parse_bib_file(filepath: str) -> list[dict]:
    """
    Parse a .bib file into a list of entry dicts.
    Each dict has 'ID', 'ENTRYTYPE', and field key/value pairs.
    Also stores '_raw' with the original text chunk for exact preservation.
    """
    with open(filepath) as f:
        content = f.read()

    # Strip YAML front matter
    content = re.sub(r"^---\s*\n---\s*\n", "", content)

    entries = []
    # Split on entry boundaries
    chunks = re.split(r"(?=@\w+\{)", content)

    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue

        # Parse entry type and key
        header = re.match(r"@(\w+)\{([^,]+),", chunk)
        if not header:
            continue

        entry = {
            "ENTRYTYPE": header.group(1).lower(),
            "ID": header.group(2).strip(),
            "_raw": chunk,
        }

        # Parse fields: match field = {value} or field = value
        # Use a regex that handles multi-line brace-delimited values
        field_pattern = re.compile(
            r"^\s*(\w+)\s*=\s*\{(.*?)\}\s*[,}]?\s*$|"
            r"^\s*(\w+)\s*=\s*(\S.*?)\s*[,}]?\s*$",
            re.MULTILINE | re.DOTALL,
        )

        # Better approach: find fields one by one
        body = chunk[chunk.index(",") + 1:] if "," in chunk else ""
        # Use a state machine to parse fields properly
        fields = _parse_fields(body)
        entry.update(fields)

        entries.append(entry)

    return entries


def _parse_fields(body: str) -> dict:
    """Parse BibTeX fields from the body of an entry."""
    fields = {}
    i = 0
    lines = body.split("\n")

    for line in lines:
        line_stripped = line.strip().rstrip(",").rstrip("}")
        match = re.match(r"(\w+)\s*=\s*(.*)", line_stripped)
        if not match:
            continue

        key = match.group(1).lower()
        val = match.group(2).strip()

        # Remove surrounding braces (may be nested or partially stripped)
        while val.startswith("{") and val.endswith("}"):
            val = val[1:-1]
        # Handle case where trailing brace was stripped by rstrip above
        if val.startswith("{") and "}" not in val:
            val = val[1:]

        if key not in ("entrytype", "id") and val:
            fields[key] = val

    return fields


def format_entry(entry: dict) -> str:
    """Format a BibTeX entry dict into a string matching gold style."""
    entry_type = entry.get("ENTRYTYPE", "article")
    entry_id = entry.get("ID", "unknown")

    # Fields to skip
    skip = {"ENTRYTYPE", "ID", "_raw"}

    # Collect fields, alphabetized
    fields = sorted(
        ((k, v) for k, v in entry.items() if k not in skip and v),
        key=lambda x: x[0],
    )

    # Find max field name length for alignment
    if fields:
        max_len = max(len(k) for k, _ in fields)
    else:
        max_len = 0

    lines = [f"@{entry_type}{{{entry_id},"]
    for key, value in fields:
        padding = " " * (max_len - len(key))
        # Don't wrap month in braces (BibTeX convention for month abbreviations)
        if key == "month":
            lines.append(f"  {key}{padding} = {{{value}}},")
        else:
            lines.append(f"  {key}{padding} = {{{value}}},")

    lines.append("}")
    return "\n".join(lines)


def sort_entries(entries: list[dict]) -> list[dict]:
    """Sort entries reverse-chronologically (newest first)."""
    def sort_key(entry):
        year_str = re.sub(r"[^0-9]", "", entry.get("year", "0") or "0")
        year = int(year_str) if year_str else 0
        month_str = entry.get("month", "").lower().strip("{} ")
        month_score = MONTH_TO_SCORE.get(month_str[:3], 0)
        return -(year * 100 + month_score)

    return sorted(entries, key=sort_key)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Auto-generate gold BibTeX from Google Scholar data"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without writing to papers.bib",
    )
    args = parser.parse_args()

    # 1. Load existing papers.bib
    print("Loading existing papers.bib...")
    if os.path.exists(BIB_FILE):
        existing_entries = parse_bib_file(BIB_FILE)
    else:
        existing_entries = []
    print(f"  Found {len(existing_entries)} existing entries")

    # 2. Load Scholar DB
    print("Loading papers from Scholar database...")
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT id, title, full_json FROM publications ORDER BY title")
    rows = cur.fetchall()
    conn.close()
    scholar_papers = [
        {"id": row[0], "title": row[1], "full_json": row[2]} for row in rows
    ]
    print(f"  Found {len(scholar_papers)} Scholar entries")

    # 3. Match Scholar entries to existing ground truth
    existing_titles = [(e.get("title", ""), i) for i, e in enumerate(existing_entries)]
    matched_scholar_ids = set()

    for scholar in scholar_papers:
        for existing_title, idx in existing_titles:
            if titles_match(scholar["title"], existing_title):
                matched_scholar_ids.add(scholar["id"])
                break

    new_papers = [p for p in scholar_papers if p["id"] not in matched_scholar_ids]
    print(f"\n  Existing (preserved): {len(matched_scholar_ids)}")
    print(f"  New (to generate):    {len(new_papers)}")

    # 4. Detect stale bib entries (in papers.bib but no longer in Scholar DB)
    scholar_titles = [p["title"] for p in scholar_papers]
    stale_entries = []
    for entry in existing_entries:
        bib_title = entry.get("title", "")
        if not bib_title:
            continue
        matched = any(titles_match(bib_title, st) for st in scholar_titles)
        if not matched:
            stale_entries.append(bib_title)

    # 5. Detect duplicate arxiv IDs across all bib entries (existing + incoming)
    #    This catches papers that were merged on Scholar but both versions remain in bib
    arxiv_dupes = []
    all_arxiv: dict[str, list[str]] = {}  # arxiv_id -> list of titles
    for entry in existing_entries:
        aid = entry.get("arxiv", "").strip("{} ")
        title = entry.get("title", "")
        if aid:
            all_arxiv.setdefault(aid, []).append(title)

    # 6. Generate entries for new papers
    new_entries = []
    flagged = []

    for paper in new_papers:
        paper_data = json.loads(paper["full_json"])
        entry, issues = scholar_to_bibtex(paper_data)
        new_entries.append(entry)
        if issues:
            flagged.append((entry.get("title", "?"), issues))
        # Track arxiv IDs from new entries too
        aid = entry.get("arxiv", "")
        if aid:
            all_arxiv.setdefault(aid, []).append(entry.get("title", ""))

    for aid, titles in all_arxiv.items():
        if len(titles) > 1:
            arxiv_dupes.append((aid, titles))

    # 7. Combine: existing (preserved raw) + new (formatted)
    # For existing entries, preserve their exact formatting via _raw
    all_entries = []

    # Add existing entries (preserve as-is)
    for e in existing_entries:
        all_entries.append(e)

    # Add new entries
    for e in new_entries:
        all_entries.append(e)

    # 6. Sort all entries
    all_entries = sort_entries(all_entries)

    # 7. Write output
    if not args.dry_run:
        print(f"\nWriting {len(all_entries)} entries to {BIB_FILE}...")
        with open(BIB_FILE, "w") as f:
            f.write("---\n---\n\n")
            for entry in all_entries:
                if "_raw" in entry:
                    f.write(entry["_raw"])
                    if not entry["_raw"].endswith("\n"):
                        f.write("\n")
                    f.write("\n")
                else:
                    f.write(format_entry(entry))
                    f.write("\n\n")
        print("Done!")
    else:
        print("\n[DRY RUN] Would write the following new entries:\n")
        for entry in new_entries:
            print(format_entry(entry))
            print()

    # 8. Print summary
    if new_entries:
        print(f"\n{'='*60}")
        print(f"NEW ENTRIES ADDED: {len(new_entries)}")
        print(f"{'='*60}")
        for e in new_entries:
            flag = " [NEEDS REVIEW]" if e.get("needs_review") else ""
            print(f"  - {e.get('title', '?')}{flag}")

    if flagged:
        print(f"\n{'='*60}")
        print(f"FLAGGED FOR REVIEW: {len(flagged)}")
        print(f"{'='*60}")
        for title, issues in flagged:
            print(f"\n  {title}")
            for issue in issues:
                print(f"    - {issue}")

    # Report stale entries (in bib but not in Scholar)
    if stale_entries:
        print(f"\n{'='*60}")
        print(f"STALE ENTRIES (in papers.bib but not in Scholar): {len(stale_entries)}")
        print(f"These may have been merged or removed on Google Scholar.")
        print(f"Review and manually remove if appropriate.")
        print(f"{'='*60}")
        for title in stale_entries:
            print(f"  - {title}")

    # Report duplicate arxiv IDs
    if arxiv_dupes:
        print(f"\n{'='*60}")
        print(f"DUPLICATE ARXIV IDs: {len(arxiv_dupes)}")
        print(f"These entries share an arxiv ID and are likely the same paper")
        print(f"(e.g., preprint upgraded to published version).")
        print(f"Review and manually remove the older version.")
        print(f"{'='*60}")
        for aid, titles in arxiv_dupes:
            print(f"\n  arxiv: {aid}")
            for t in titles:
                print(f"    - {t}")

    if not new_entries and not stale_entries and not arxiv_dupes:
        print("\nNo new papers to add. papers.bib is up to date.")


if __name__ == "__main__":
    main()
