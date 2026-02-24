#!/usr/bin/env python3
"""Generate publications.tex from papers.bib and push to Overleaf CV project.

Usage:
    python scripts/generate_cv.py              # generate long (academic) CV and push
    python scripts/generate_cv.py --short      # generate short (industry) CV and push
    python scripts/generate_cv.py --dry-run    # print generated LaTeX to stdout
    python scripts/generate_cv.py --local-only # write files locally, no push
"""

import argparse
import re
import subprocess
from collections import OrderedDict
from pathlib import Path

import bibtexparser

# Paths
REPO_ROOT = Path(__file__).resolve().parent.parent
BIB_FILE = REPO_ROOT / "_bibliography" / "papers.bib"
OVERLEAF_DIR = REPO_ROOT / "_overleaf"
OVERLEAF_REPO = "https://git.overleaf.com/699953a3998c0935e906c402"
OUTPUT_FILE = "publications.tex"
MODE_FILE = "cvmode.tex"

# Month name → number mapping (handles various abbreviations in the bib file)
MONTH_MAP = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "september": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}

# Publication categories in display order
CATEGORIES = OrderedDict([
    ("conference_journal", "Conference \\& Journal Papers"),
    ("demo", "Demo Papers"),
    ("workshop", "Workshop Papers"),
    ("extended_abstract", "Extended Abstracts"),
    ("preprint", "Preprints"),
    ("other", "Other Scholarly Publications"),
    ("dataset", "Datasets and Resources"),
])


def parse_bib(bib_path: Path) -> list[dict]:
    """Parse a .bib file and return list of entry dicts."""
    text = bib_path.read_text()
    parser = bibtexparser.bparser.BibTexParser(common_strings=True)
    parser.ignore_nonstandard_types = False
    bib_db = bibtexparser.loads(text, parser=parser)
    entries = []
    for entry in bib_db.entries:
        record = dict(entry)
        record["type"] = record.pop("ENTRYTYPE", "")
        record["key"] = record.pop("ID", "")
        entries.append(record)
    return entries


def month_to_num(month_str: str) -> int:
    """Convert month string to number. Returns 0 if unknown."""
    return MONTH_MAP.get(month_str.strip().lower(), 0)


def get_year(entry: dict) -> int:
    """Extract year as int from entry."""
    try:
        return int(entry.get("year", "0"))
    except (ValueError, TypeError):
        return 0


def get_month_num(entry: dict) -> int:
    """Extract month as number from entry."""
    m = entry.get("month", "")
    if not m:
        return 0
    return month_to_num(m)


def classify_entry(entry: dict) -> str:
    """Classify a bib entry into a publication category."""
    title = entry.get("title", "").lower()
    journal = entry.get("journal", "")
    booktitle = entry.get("booktitle", "")
    journal_lower = journal.lower()
    booktitle_lower = booktitle.lower()

    # Demo papers
    if "system demonstration" in booktitle_lower or "demo" in booktitle_lower:
        return "demo"

    # Extended abstracts
    if "extended abstract" in booktitle_lower:
        return "extended_abstract"

    # Workshop overview / shared task overview / other scholarly
    if title.startswith("overview"):
        return "other"
    if "sigir forum" in journal_lower:
        return "other"
    if "text analysis conference" in booktitle_lower:
        return "other"

    # Workshop papers (research contributions at workshops)
    if "workshop" in booktitle_lower:
        return "workshop"

    # Datasets and resources
    if "tech. rep" in journal_lower:
        return "dataset"

    # Preprints
    if journal_lower == "arxiv":
        return "preprint"

    # Everything else is conference & journal
    return "conference_journal"


def escape_latex(text: str) -> str:
    """Escape LaTeX special characters in plain text, preserving existing LaTeX commands."""
    if "\\" in text or "{" in text:
        return text
    text = text.replace("&", r"\&")
    text = text.replace("%", r"\%")
    text = text.replace("#", r"\#")
    text = text.replace("_", r"\_")
    return text


def normalize_author_name(name: str) -> tuple[str, str]:
    """Parse an author name into (first, last) tuple."""
    name = name.strip()
    if not name:
        return ("", "")
    if "," in name:
        parts = [p.strip() for p in name.split(",", 1)]
        last, first = parts[0], parts[1] if len(parts) > 1 else ""
    else:
        parts = name.split()
        if len(parts) == 1:
            return ("", parts[0])
        first = " ".join(parts[:-1])
        last = parts[-1]
    return (first, last)


def is_kyle_lo(first: str, last: str) -> bool:
    """Check if this author is Kyle Lo."""
    return last.lower() == "lo" and first.lower().startswith("kyle")


def _match_author(first: str, last: str, target: str) -> bool:
    """Check if (first, last) matches a target name string (case-insensitive)."""
    target_parts = target.strip().split()
    if not target_parts:
        return False
    target_last = target_parts[-1].lower()
    target_first = " ".join(target_parts[:-1]).lower()
    return last.lower() == target_last and first.lower().startswith(target_first[:3] if target_first else "")


def format_authors(author_str: str, entry: dict | None = None) -> str:
    """Format author string, bolding Kyle Lo's name.

    If entry has cv_authors_after and cv_authors_before, truncate the author
    list: show authors up to and including cv_authors_after, then "...",
    then from cv_authors_before onward (always including Kyle Lo if in the
    truncated range).
    """
    authors = re.split(r"\s+and\s+", author_str)
    parsed = [normalize_author_name(a) for a in authors]

    after_name = (entry or {}).get("cv_authors_after", "").strip()
    before_name = (entry or {}).get("cv_authors_before", "").strip()

    if after_name and before_name:
        after_idx = None
        before_idx = None
        for i, (f, l) in enumerate(parsed):
            if after_idx is None and _match_author(f, l, after_name):
                after_idx = i
            if before_idx is None and _match_author(f, l, before_name):
                before_idx = i

        if after_idx is not None and before_idx is not None:
            if after_idx == before_idx:
                # Same author: show only that author, no ellipsis
                parsed = parsed[:after_idx + 1]
                head = None
            else:
                head = parsed[:after_idx + 1]
                tail = parsed[before_idx:]
                # Include Kyle Lo from the truncated middle if not already in head/tail
                kyle_in_head_tail = any(is_kyle_lo(f, l) for f, l in head + tail)
                if not kyle_in_head_tail:
                    for f, l in parsed[after_idx + 1:before_idx]:
                        if is_kyle_lo(f, l):
                            head.append((f, l))
                            break
            if head is not None:
                parsed = list(head) + [("...", "")] + list(tail)

    formatted = []
    for first, last in parsed:
        if first == "..." and last == "":
            formatted.append("\\ldots")
        elif is_kyle_lo(first, last):
            formatted.append(r"\textbf{" + f"{first} {last}" + "}")
        else:
            display = f"{first} {last}".strip() if first else last
            formatted.append(escape_latex(display))
    return ", ".join(formatted)


def clean_title(title: str) -> str:
    """Clean a bib title: remove outer braces used for capitalization protection."""
    title = re.sub(r"\{([^{}])\}", r"\1", title)
    title = re.sub(r"\{([^{}]+)\}", r"\1", title)
    return title


def get_venue(entry: dict) -> str:
    """Extract venue name from entry."""
    venue = entry.get("journal") or entry.get("booktitle") or ""
    if "Proceedings of" in venue:
        short = entry.get("booktitle", venue)
        venue = short
    return clean_title(venue)


def format_entry(entry: dict) -> str:
    """Format a single bib entry as a LaTeX \\item."""
    authors = format_authors(entry.get("author", ""), entry)
    title = clean_title(entry.get("title", ""))
    venue = get_venue(entry)
    year = entry.get("year", "")
    award = entry.get("award", "")

    parts = []
    parts.append(f"  \\item {authors}.")
    parts.append(f"  ``{escape_latex(title)}.''")

    if venue:
        parts.append(f"  \\textit{{{escape_latex(venue)}}}, {year}.")
    else:
        parts.append(f"  {year}.")

    if award:
        parts.append(f"  \\textbf{{{escape_latex(award)}}}.")

    return "\n".join(parts)


def generate_latex(entries: list[dict]) -> str:
    """Generate the full publications.tex content.

    Always emits all content. The \\ifshortcv conditional in LaTeX controls
    what is shown — Selected Works only (short) or full categorized list (long).
    """
    # Filter to entries with bibtex_show = true
    shown = [e for e in entries if e.get("bibtex_show", "").lower() == "true"]

    # Sort by year descending, then by month descending within year
    shown.sort(key=lambda e: (get_year(e), get_month_num(e)), reverse=True)

    lines = []
    lines.append("% Auto-generated by scripts/generate_cv.py — do not edit manually")
    lines.append(r"% \textsuperscript{*} indicates equal contribution.")
    lines.append("")

    # Selected Works section (only shown in short CV mode)
    selected = [e for e in shown if e.get("selected", "").lower() == "true"]
    if selected:
        lines.append("\\ifshortcv")
        lines.append("\\begin{itemize}[leftmargin=*]")
        for entry in selected:
            lines.append(format_entry(entry))
        lines.append("\\end{itemize}")
        lines.append("\\fi")
        lines.append("")

    # Full publication list by category (only shown in long CV mode)
    lines.append("\\ifshortcv\\else")
    by_category: dict[str, list[dict]] = {cat: [] for cat in CATEGORIES}
    for entry in shown:
        cat = classify_entry(entry)
        by_category[cat].append(entry)

    for cat_key, cat_label in CATEGORIES.items():
        entries_in_cat = by_category[cat_key]
        if not entries_in_cat:
            continue

        lines.append(f"\\subsection*{{{cat_label}}}")
        lines.append("\\begin{itemize}[leftmargin=*]")
        for entry in entries_in_cat:
            lines.append(format_entry(entry))
        lines.append("\\end{itemize}")
        lines.append("")

    lines.append("\\fi")

    return "\n".join(lines) + "\n"


def generate_cvmode(short: bool = False) -> str:
    """Generate cvmode.tex that sets the \\ifshortcv boolean."""
    lines = [
        "% Auto-generated by scripts/generate_cv.py — do not edit manually",
        "% Controls which sections appear in the CV.",
        r"\newif\ifshortcv",
    ]
    if short:
        lines.append(r"\shortcvtrue")
    else:
        lines.append(r"\shortcvfalse")
    return "\n".join(lines) + "\n"


def clone_or_pull_overleaf() -> None:
    """Clone the Overleaf repo if needed, or pull latest changes."""
    if (OVERLEAF_DIR / ".git").is_dir():
        print("Pulling latest from Overleaf...")
        subprocess.run(["git", "pull"], cwd=OVERLEAF_DIR, check=True)
    else:
        print("Cloning Overleaf project...")
        OVERLEAF_DIR.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["git", "clone", OVERLEAF_REPO, str(OVERLEAF_DIR)], check=True
        )


def push_to_overleaf(short: bool = False) -> None:
    """Commit and push generated files if changed."""
    files = [OUTPUT_FILE, MODE_FILE]
    result_status = subprocess.run(
        ["git", "status", "--porcelain"] + files,
        cwd=OVERLEAF_DIR,
        capture_output=True,
        text=True,
    )
    if not result_status.stdout.strip():
        print("No changes — skipping push.")
        return

    subprocess.run(
        ["git", "add"] + files, cwd=OVERLEAF_DIR, check=True
    )
    mode = "short" if short else "long"
    subprocess.run(
        ["git", "commit", "-m", f"Update publications ({mode} CV) from papers.bib"],
        cwd=OVERLEAF_DIR,
        check=True,
    )
    print("Pushing to Overleaf...")
    subprocess.run(["git", "push"], cwd=OVERLEAF_DIR, check=True)
    print("Done — pushed to Overleaf.")


def main():
    parser = argparse.ArgumentParser(
        description="Generate publications.tex from papers.bib"
    )
    parser.add_argument(
        "--short",
        action="store_true",
        help="Generate short (industry) CV: selected works only, hide service/talks/press",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print generated LaTeX to stdout without writing or pushing",
    )
    parser.add_argument(
        "--local-only",
        action="store_true",
        help="Write files locally in _overleaf/ but don't push",
    )
    args = parser.parse_args()

    # Parse and generate
    entries = parse_bib(BIB_FILE)
    latex = generate_latex(entries)
    cvmode = generate_cvmode(short=args.short)

    if args.dry_run:
        print("=== cvmode.tex ===")
        print(cvmode)
        print("=== publications.tex ===")
        print(latex)
        return

    # Clone/pull Overleaf repo
    clone_or_pull_overleaf()

    # Write files
    (OVERLEAF_DIR / OUTPUT_FILE).write_text(latex)
    (OVERLEAF_DIR / MODE_FILE).write_text(cvmode)
    mode = "short" if args.short else "long"
    print(f"Wrote {OUTPUT_FILE} and {MODE_FILE} ({mode} mode)")

    if args.local_only:
        print("Local-only mode — skipping push.")
        return

    # Commit and push
    push_to_overleaf(short=args.short)


if __name__ == "__main__":
    main()
