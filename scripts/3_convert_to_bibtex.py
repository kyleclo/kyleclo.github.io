# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "bibtexparser",
#     "litellm",
#     "tqdm",
#     "python-slugify",
# ]
# ///
"""
Convert Google Scholar papers from SQLite to BibTeX format.

Generates BibTeX entries from the scraped papers.

Call:
    uv run scripts/3_convert_to_bibtex.py --method=rules
    uv run scripts/3_convert_to_bibtex.py --method=llm
    uv run scripts/3_convert_to_bibtex.py --method=llm --batch-size=5

Options:
    --method=rules|llm     Generation method (default: rules)
    --model=MODEL          LLM model to use (default: gpt-4o-mini)
    --batch-size=N         Papers per LLM call (default: 1)
    --sample=N             Only process first N papers for testing

Output:
    _bibliography/papers_generated_{method}.bib - Auto-generated BibTeX
"""

import argparse
import json
import os
import re
import sqlite3
import sys

import bibtexparser
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.bibdatabase import BibDatabase
from litellm import completion
from tqdm import tqdm

DB_FILE = os.path.join(os.path.dirname(__file__), "../_bibliography/gscholar_export.db")


def normalize_name(name):
    """Normalize author name for comparison."""
    # Remove extra whitespace, convert to lowercase
    return " ".join(name.lower().split())


def generate_bibtex_key(title, author, year):
    """Generate a BibTeX citation key like 'LastName2024TitleWords'."""
    # Get first author's last name
    if author:
        # Split on "and" to get first author
        first_author = author.split(" and ")[0].strip()
        # Get last name (last word)
        last_name = first_author.split()[-1]
        # Remove special characters
        last_name = re.sub(r"[^a-zA-Z]", "", last_name)
    else:
        last_name = "Unknown"

    # Get first 2-3 words from title (capitalize first letter of each)
    if title:
        title_words = title.split()[:3]
        title_part = "".join(
            [w.capitalize() for w in title_words if w.lower() not in ["a", "an", "the"]]
        )
        title_part = re.sub(r"[^a-zA-Z]", "", title_part)
    else:
        title_part = "Paper"

    return f"{last_name}{year}{title_part}"


def extract_month_from_citation(citation):
    """Extract month from citation string if present."""
    month_map = {
        "january": "jan", "jan": "jan",
        "february": "feb", "feb": "feb",
        "march": "mar", "mar": "mar",
        "april": "apr", "apr": "apr",
        "may": "may",
        "june": "jun", "jun": "jun",
        "july": "jul", "jul": "jul",
        "august": "aug", "aug": "aug",
        "september": "sep", "sep": "sep",
        "october": "oct", "oct": "oct",
        "november": "nov", "nov": "nov",
        "december": "dec", "dec": "dec",
    }
    citation_lower = citation.lower()
    for month_name, month_abbr in month_map.items():
        if month_name in citation_lower:
            return month_abbr
    return ""


def extract_arxiv_id(venue_or_url):
    """Extract arXiv ID from venue or URL string."""
    # Match patterns like "arXiv:2024.12345" or "2024.12345"
    match = re.search(r'(?:arXiv[:\s]+)?(\d{4}\.\d{4,5})', venue_or_url, re.IGNORECASE)
    if match:
        return match.group(1)
    return ""


def slugify_title(title):
    """Convert title to slug for PDF/preview filenames.

    Uses python-slugify to match the behavior of get_pdfs.py.
    """
    from slugify import slugify as _slugify
    # Match the behavior in get_pdfs.py - remove apostrophes
    return _slugify(title, replacements=[("'", "")])


def convert_to_bibtex_rules(papers):
    """Convert papers from SQLite to BibTeX format using rule-based method per BIB.md."""
    entries = []

    for paper in papers:
        paper_data = json.loads(paper["full_json"])
        bib = paper_data.get("bib", {})

        # Get venue info
        venue = (
            bib.get("conference")
            or bib.get("journal")
            or bib.get("citation")
            or ""
        )

        # Determine entry type
        venue_lower = venue.lower()
        if "conference" in bib or any(x in venue_lower for x in ["proceedings", "conference", "workshop", "symposium"]):
            entry_type = "inproceedings"
        else:
            entry_type = "article"

        # Extract basic fields
        title = bib.get("title", "")
        author = bib.get("author", "")
        year = str(bib.get("pub_year", ""))
        url = paper_data.get("pub_url", "")

        # Extract month (from citation or venue string)
        citation = bib.get("citation", "")
        month = extract_month_from_citation(citation or venue)

        # Build entry with universal required fields
        entry = {
            "ID": generate_bibtex_key(title, author, year),
            "ENTRYTYPE": entry_type,
            "title": title,
            "author": author,
            "year": year,
            "url": url,
        }

        if month:
            entry["month"] = month

        # Add entry-specific fields per BIB.md
        arxiv_id = None
        if entry_type == "inproceedings":
            # Conference paper: need booktitle
            if venue:
                entry["booktitle"] = venue
            # DOI extraction from URL if it's a DOI link
            if url and "doi.org" in url:
                doi = url.split("doi.org/")[-1]
                entry["doi"] = doi
        else:
            # Article: check if ArXiv or regular journal
            if "arxiv" in venue_lower:
                entry["journal"] = "ArXiv"
                arxiv_id = extract_arxiv_id(venue or url)
                if arxiv_id:
                    entry["volume"] = arxiv_id
            else:
                # Regular journal
                if venue:
                    entry["journal"] = venue
                # Try to extract DOI from URL
                if url and "doi.org" in url:
                    doi = url.split("doi.org/")[-1]
                    entry["doi"] = doi
                # Note: volume is hard to extract from Google Scholar data for journals

        # Add site-specific fields per BIB.md
        entry["bibtex_show"] = "true"

        # Extract abstract
        abstract = bib.get("abstract", "")
        if abstract:
            entry["abstract"] = abstract

        # Generate PDF and preview filenames from title
        slug = slugify_title(title)
        if slug:
            entry["pdf"] = f"{slug}.pdf"
            entry["preview"] = f"{slug}.png"

        # Add arxiv field for preprints
        if arxiv_id:
            entry["arxiv"] = arxiv_id

        entries.append(entry)

    return entries


def convert_to_bibtex_llm(papers, model="gpt-4o-mini", batch_size=1):
    """Convert papers from SQLite to BibTeX format using LLM."""
    entries = []

    print(f"Using LLM method with model: {model}")
    print(f"Batch size: {batch_size}\n")

    # Process in batches
    num_batches = (len(papers) + batch_size - 1) // batch_size

    for batch_idx in tqdm(range(num_batches), desc="Converting with LLM", unit="batch"):
        batch_start = batch_idx * batch_size
        batch_end = min(batch_start + batch_size, len(papers))
        batch_papers = papers[batch_start:batch_end]

        if batch_size == 1:
            # Single paper mode
            paper = batch_papers[0]
            paper_data = json.loads(paper["full_json"])
            bib = paper_data.get("bib", {})

            paper_json = {
                "title": bib.get("title", ""),
                "author": bib.get("author", ""),
                "year": bib.get("pub_year", ""),
                "venue": (
                    bib.get("conference")
                    or bib.get("journal")
                    or bib.get("citation")
                    or ""
                ),
                "publisher": bib.get("publisher", ""),
                "pages": bib.get("pages", ""),
                "url": paper_data.get("pub_url", ""),
                "abstract": bib.get("abstract", "")[:500] if bib.get("abstract") else "",
            }

            prompt = f"""You are a bibliographer. Convert the following paper metadata to a single BibTeX entry.

Paper metadata:
{json.dumps(paper_json, indent=2)}

Required fields (must include):
- Universal: title, author, url, month, year
- For conferences (@inproceedings): booktitle, doi (if available)
- For journal articles (@article): journal, volume, doi
- For ArXiv preprints (@article): journal="ArXiv", volume=<arxiv_id>

Instructions:
1. Choose entry type: @inproceedings for conferences, @article for journals/arxiv
2. Generate citation key: FirstAuthorLastName<Year><TitleWords>
3. Clean venue names: "arXiv preprint arXiv:2024.12345" → journal="ArXiv", volume="2024.12345"
4. For month, use abbreviations: jan, feb, mar, apr, may, jun, jul, aug, sep, oct, nov, dec (no quotes)
5. Keep author format: "Name1 and Name2 and Name3"
6. DO NOT include: pages, publisher, abstract, address, organization
7. Extract DOI from URL if URL is a DOI link

Return ONLY the BibTeX entry, no explanation."""

        else:
            # Batch mode - multiple papers in one prompt
            papers_json = []
            for i, paper in enumerate(batch_papers):
                paper_data = json.loads(paper["full_json"])
                bib = paper_data.get("bib", {})
                papers_json.append({
                    "index": i + 1,
                    "title": bib.get("title", ""),
                    "author": bib.get("author", ""),
                    "year": bib.get("pub_year", ""),
                    "venue": (
                        bib.get("conference")
                        or bib.get("journal")
                        or bib.get("citation")
                        or ""
                    ),
                    "publisher": bib.get("publisher", ""),
                    "pages": bib.get("pages", ""),
                    "url": paper_data.get("pub_url", ""),
                    "abstract": bib.get("abstract", "")[:200] if bib.get("abstract") else "",  # Shorter for batch
                })

            prompt = f"""You are a bibliographer. Convert the following {len(papers_json)} papers to BibTeX entries.

Papers metadata:
{json.dumps(papers_json, indent=2)}

Required fields (must include):
- Universal: title, author, url, month, year
- For conferences (@inproceedings): booktitle, doi (if available)
- For journal articles (@article): journal, volume, doi
- For ArXiv preprints (@article): journal="ArXiv", volume=<arxiv_id>

Instructions:
1. Choose entry type: @inproceedings for conferences, @article for journals/arxiv
2. Generate citation key: FirstAuthorLastName<Year><TitleWords>
3. Clean venue names: "arXiv preprint arXiv:2024.12345" → journal="ArXiv", volume="2024.12345"
4. For month, use abbreviations: jan, feb, mar, apr, may, jun, jul, aug, sep, oct, nov, dec (no quotes)
5. Keep author format: "Name1 and Name2 and Name3"
6. DO NOT include: pages, publisher, abstract, address, organization
7. Extract DOI from URL if URL is a DOI link

Return ONLY the {len(papers_json)} BibTeX entries (one per paper, in order), no explanation."""

        try:
            response = completion(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
            )

            bibtex_text = response.choices[0].message.content.strip()

            # Parse the generated BibTeX to extract fields
            try:
                # Remove markdown code blocks if present
                if "```" in bibtex_text:
                    match = re.search(r'```(?:bibtex)?\n(.*?)\n```', bibtex_text, re.DOTALL)
                    if match:
                        bibtex_text = match.group(1)

                parser = bibtexparser.bparser.BibTexParser(common_strings=True)
                parsed = bibtexparser.loads(bibtex_text, parser)

                if parsed.entries:
                    # Add site-specific fields to each parsed entry
                    for i, entry in enumerate(parsed.entries):
                        if i < len(batch_papers):
                            paper = batch_papers[i]
                            paper_data = json.loads(paper["full_json"])
                            bib = paper_data.get("bib", {})

                            # Add site-specific fields per BIB.md
                            entry["bibtex_show"] = "true"

                            # Extract abstract
                            abstract = bib.get("abstract", "")
                            if abstract:
                                entry["abstract"] = abstract

                            # Generate PDF and preview filenames from title
                            title = entry.get("title", "")
                            slug = slugify_title(title)
                            if slug:
                                entry["pdf"] = f"{slug}.pdf"
                                entry["preview"] = f"{slug}.png"

                            # Add arxiv field for preprints
                            journal = entry.get("journal", "").lower()
                            if "arxiv" in journal:
                                volume = entry.get("volume", "")
                                if volume:
                                    entry["arxiv"] = volume

                    entries.extend(parsed.entries)
                else:
                    print(f"  Warning: Failed to parse LLM output for batch {batch_idx+1}")
                    # Fallback to rules-based for this batch
                    entries.extend(convert_to_bibtex_rules(batch_papers))
            except Exception as parse_error:
                print(f"  Warning: Parse error for batch {batch_idx+1}: {parse_error}")
                # Fallback to rules-based for this batch
                entries.extend(convert_to_bibtex_rules(batch_papers))

        except Exception as e:
            print(f"  Error calling LLM for batch {batch_idx+1}: {e}")
            # Fallback to rules-based for this batch
            entries.extend(convert_to_bibtex_rules(batch_papers))

    return entries


def main():
    parser = argparse.ArgumentParser(description="Convert Google Scholar papers to BibTeX")
    parser.add_argument(
        "--method",
        choices=["rules", "llm"],
        default="rules",
        help="Generation method (default: rules)"
    )
    parser.add_argument(
        "--model",
        default="gpt-4o-mini",
        help="LLM model to use (default: gpt-4o-mini)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1,
        help="Number of papers to process in each LLM call (default: 1)"
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=None,
        help="Only process first N papers for testing"
    )
    args = parser.parse_args()

    # Set output filename based on method
    generated_bib = os.path.join(
        os.path.dirname(__file__), f"../_bibliography/papers_generated_{args.method}.bib"
    )

    print(f"Generation method: {args.method}")
    if args.method == "llm":
        print(f"LLM model: {args.model}")
    print()

    print("Loading papers from database...")
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT id, title, full_json FROM publications ORDER BY title")
    rows = cur.fetchall()
    conn.close()

    papers = [{"id": row[0], "title": row[1], "full_json": row[2]} for row in rows]

    if args.sample:
        papers = papers[:args.sample]
        print(f"Sampling first {args.sample} papers for testing")

    print(f"Loaded {len(papers)} papers\n")

    print("Converting to BibTeX format...")
    if args.method == "rules":
        generated_entries = convert_to_bibtex_rules(papers)
    elif args.method == "llm":
        generated_entries = convert_to_bibtex_llm(papers, model=args.model, batch_size=args.batch_size)
    else:
        print(f"Unknown method: {args.method}")
        sys.exit(1)

    # Write generated BibTeX
    db = BibDatabase()
    db.entries = generated_entries
    writer = BibTexWriter()
    writer.indent = "  "
    with open(generated_bib, "w") as f:
        f.write(writer.write(db))
    print(f"\nGenerated BibTeX written to: {generated_bib}")


if __name__ == "__main__":
    main()
