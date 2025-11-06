# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "bibtexparser",
#     "litellm",
#     "tqdm",
# ]
# ///
"""
Convert Google Scholar papers from SQLite to BibTeX format.

Generates BibTeX entries from the scraped papers and evaluates against
the existing manually-curated papers.bib file.

Call:
    uv run scripts/3_convert_to_bibtex.py --method=rules
    uv run scripts/3_convert_to_bibtex.py --method=llm
    uv run scripts/3_convert_to_bibtex.py --method=llm --batch-size=5

Options:
    --method=rules|llm     Generation method (default: rules)
    --model=MODEL          LLM model to use (default: gpt-4o-mini)
    --batch-size=N         Papers per LLM call (default: 1, slow)
    --sample=N             Only process first N papers for testing

Output:
    _bibliography/papers_generated_{method}.bib - Auto-generated BibTeX
    _bibliography/bibtex_evaluation_{method}.html - Comparison report
"""

import argparse
import json
import os
import re
import sqlite3
import sys
from collections import defaultdict
from difflib import SequenceMatcher

import bibtexparser
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.bibdatabase import BibDatabase
from litellm import completion
from tqdm import tqdm

DB_FILE = os.path.join(os.path.dirname(__file__), "../_bibliography/gscholar_export.db")
GROUND_TRUTH_BIB = os.path.join(
    os.path.dirname(__file__), "../_bibliography/papers.bib"
)


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


def load_ground_truth_bibtex(filepath):
    """Load the manually-curated BibTeX file."""
    with open(filepath, "r") as f:
        content = f.read()
        # Skip YAML front matter if present
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                content = parts[2]
        parser = bibtexparser.bparser.BibTexParser(common_strings=True)
        bib_db = bibtexparser.loads(content, parser)
        return bib_db.entries


def normalize_title(title):
    """Normalize title for comparison."""
    # Convert to lowercase
    t = title.lower().strip()
    # Remove extra whitespace
    t = " ".join(t.split())
    # Normalize punctuation spacing
    t = re.sub(r'\s*:\s*', ': ', t)
    t = re.sub(r'\s*\.\s*', '. ', t)
    return t


def title_similarity(title1, title2):
    """Calculate similarity between two titles."""
    t1 = normalize_title(title1)
    t2 = normalize_title(title2)

    # Try exact substring match for truncated titles
    if len(t1) < len(t2):
        if t2.startswith(t1):
            return 1.0  # Perfect match if shorter title is prefix
    elif len(t2) < len(t1):
        if t1.startswith(t2):
            return 1.0  # Perfect match if shorter title is prefix

    return SequenceMatcher(None, t1, t2).ratio()


def match_papers(generated_entries, ground_truth_entries):
    """Match generated entries to ground truth entries by title."""
    matches = []
    unmatched_generated = []
    unmatched_ground_truth = list(ground_truth_entries)

    for gen_entry in generated_entries:
        gen_title = gen_entry.get("title", "")
        best_match = None
        best_score = 0.0

        for gt_entry in unmatched_ground_truth:
            gt_title = gt_entry.get("title", "")
            score = title_similarity(gen_title, gt_title)
            if score > best_score:
                best_score = score
                best_match = gt_entry

        if best_score >= 0.85:  # High similarity threshold
            matches.append({
                "generated": gen_entry,
                "ground_truth": best_match,
                "similarity": best_score
            })
            unmatched_ground_truth.remove(best_match)
        else:
            unmatched_generated.append(gen_entry)

    return matches, unmatched_generated, unmatched_ground_truth


def field_similarity(val1, val2):
    """Calculate similarity between two field values."""
    if not val1 or not val2:
        return 0.0
    v1 = normalize_name(val1)
    v2 = normalize_name(val2)
    if v1 == v2:
        return 1.0
    return SequenceMatcher(None, v1, v2).ratio()


def get_required_fields(entry):
    """Get list of required fields for this entry based on BIB.md rules.

    Universal fields (all papers): title, author, url, month, year
    Conference (@inproceedings): + booktitle, [doi]
    Journal (@article): + journal, volume, doi
    ArXiv (@article): + journal, volume
    """
    # Universal fields required for all papers
    required = {"title", "author", "url", "month", "year"}

    entry_type = entry.get("ENTRYTYPE", "article")
    journal = entry.get("journal", "").lower()

    if entry_type == "inproceedings":
        # Conference paper
        required.add("booktitle")
        # DOI is optional but we check if it exists in ground truth
        if entry.get("doi", "").strip():
            required.add("doi")
    elif "arxiv" in journal:
        # ArXiv preprint
        required.update(["journal", "volume"])
        # ArXiv typically doesn't have DOI
    else:
        # Regular journal article
        required.update(["journal", "volume", "doi"])

    return required


def score_entry(gen_entry, gt_entry, similarity_threshold=0.85):
    """Score a generated entry against ground truth entry based on BIB.md rules.

    Returns:
        dict with:
            - total_fields: number of required fields in ground truth
            - points: number of fields that match above threshold
            - score: points / total_fields
            - field_scores: dict of field -> similarity score
    """
    # Get required fields for this entry type
    required_fields = get_required_fields(gt_entry)

    # Only score required fields that exist in ground truth
    gt_fields = {field for field in required_fields if gt_entry.get(field, "").strip()}

    field_scores = {}
    points = 0

    for field in gt_fields:
        gt_val = gt_entry.get(field, "").strip()
        gen_val = gen_entry.get(field, "").strip()

        similarity = field_similarity(gen_val, gt_val)
        field_scores[field] = similarity

        if similarity >= similarity_threshold:
            points += 1

    total_fields = len(gt_fields)
    score = points / total_fields if total_fields > 0 else 0.0

    return {
        "total_fields": total_fields,
        "points": points,
        "score": score,
        "field_scores": field_scores
    }


def compare_entries(gen_entry, gt_entry):
    """Compare fields between generated and ground truth entries."""
    differences = []

    # Only compare required fields per BIB.md
    required_fields = get_required_fields(gt_entry)

    for field in required_fields:
        gen_val = gen_entry.get(field, "").strip()
        gt_val = gt_entry.get(field, "").strip()

        if gen_val and gt_val:
            if normalize_name(gen_val) != normalize_name(gt_val):
                differences.append({
                    "field": field,
                    "generated": gen_val,
                    "ground_truth": gt_val
                })
        elif gt_val and not gen_val:
            differences.append({
                "field": field,
                "generated": "(missing)",
                "ground_truth": gt_val
            })

    return differences


def generate_evaluation_report(matches, unmatched_generated, unmatched_ground_truth, similarity_threshold=0.85):
    """Generate HTML evaluation report."""
    total_gt = len(matches) + len(unmatched_ground_truth)
    total_gen = len(matches) + len(unmatched_generated)

    # Calculate field-level scores for all matched papers
    field_stats = defaultdict(lambda: {"total": 0, "correct": 0})
    paper_scores = []

    for match in matches:
        score_result = score_entry(match["generated"], match["ground_truth"], similarity_threshold)
        paper_scores.append({
            "title": match["ground_truth"].get("title", "Untitled"),
            "score": score_result["score"],
            "points": score_result["points"],
            "total": score_result["total_fields"],
            "field_scores": score_result["field_scores"]
        })

        # Aggregate field-level stats
        for field, similarity in score_result["field_scores"].items():
            field_stats[field]["total"] += 1
            if similarity >= similarity_threshold:
                field_stats[field]["correct"] += 1

    # Sort papers by score (worst first)
    paper_scores.sort(key=lambda x: x["score"])

    # Calculate average score
    avg_score = sum(p["score"] for p in paper_scores) / len(paper_scores) if paper_scores else 0

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>BibTeX Conversion Evaluation</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #007bff;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #555;
            margin-top: 40px;
            padding: 10px;
            background: #f8f9fa;
            border-left: 4px solid #007bff;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .stat-box {{
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
            text-align: center;
        }}
        .stat-number {{
            font-size: 32px;
            font-weight: bold;
            color: #007bff;
        }}
        .stat-label {{
            color: #666;
            margin-top: 5px;
        }}
        .match {{
            background: #fff;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 20px;
            margin: 15px 0;
        }}
        .paper-title {{
            font-weight: bold;
            color: #212529;
            margin-bottom: 10px;
            font-size: 16px;
        }}
        .similarity {{
            display: inline-block;
            background: #28a745;
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            margin-bottom: 10px;
        }}
        .differences {{
            margin-top: 15px;
        }}
        .diff {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 10px;
            margin: 10px 0;
            border-radius: 4px;
        }}
        .field-name {{
            font-weight: bold;
            color: #856404;
        }}
        .value {{
            font-family: monospace;
            font-size: 13px;
            margin: 5px 0;
            padding: 5px;
            background: white;
            border-radius: 4px;
        }}
        .unmatched {{
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
        }}
        .success {{
            color: #28a745;
            font-weight: bold;
        }}
        .warning {{
            color: #ffc107;
            font-weight: bold;
        }}
        .error {{
            color: #dc3545;
            font-weight: bold;
        }}
        .score-bar {{
            width: 100%;
            height: 20px;
            background: #e9ecef;
            border-radius: 10px;
            overflow: hidden;
            margin: 5px 0;
        }}
        .score-fill {{
            height: 100%;
            background: linear-gradient(90deg, #dc3545 0%, #ffc107 50%, #28a745 100%);
            transition: width 0.3s;
        }}
        .field-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        .field-table th, .field-table td {{
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #dee2e6;
        }}
        .field-table th {{
            background: #f8f9fa;
            font-weight: bold;
        }}
        .field-score {{
            font-family: monospace;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 BibTeX Conversion Evaluation Report</h1>

        <div class="summary">
            <div class="stat-box">
                <div class="stat-number">{total_gt}</div>
                <div class="stat-label">Ground Truth Papers</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{total_gen}</div>
                <div class="stat-label">Generated Papers</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{len(matches)}</div>
                <div class="stat-label">Matched Papers</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{avg_score * 100:.1f}%</div>
                <div class="stat-label">Avg Field Score</div>
            </div>
        </div>

        <h2>📈 Field-Level Performance</h2>
        <p>Accuracy for individual BibTeX fields across all matched papers (threshold: {similarity_threshold * 100:.0f}% similarity).</p>
        <table class="field-table">
            <tr>
                <th>Field</th>
                <th>Correct / Total</th>
                <th>Accuracy</th>
                <th>Score Bar</th>
            </tr>
"""

    # Add field stats rows in stable order
    field_order = ["title", "author", "year", "month", "booktitle", "journal", "volume", "doi", "url"]
    ordered_field_stats = [f for f in field_order if f in field_stats]

    for field in ordered_field_stats:
        stats = field_stats[field]
        accuracy = stats["correct"] / stats["total"] if stats["total"] > 0 else 0
        html += f"""
            <tr>
                <td><strong>{field}</strong></td>
                <td class="field-score">{stats["correct"]} / {stats["total"]}</td>
                <td class="field-score">{accuracy * 100:.1f}%</td>
                <td>
                    <div class="score-bar">
                        <div class="score-fill" style="width: {accuracy * 100}%"></div>
                    </div>
                </td>
            </tr>
"""

    html += f"""
        </table>

        <h2>✓ Matched Papers ({len(matches)})</h2>
        <p>Papers found in both generated and ground truth BibTeX files.</p>
"""

    for match_idx, match in enumerate(matches):
        gen = match["generated"]
        gt = match["ground_truth"]
        paper_id = f"paper-{match_idx}"

        # Get required fields for this entry
        required_fields = get_required_fields(gt)

        # Calculate field similarities
        score_result = score_entry(gen, gt, similarity_threshold)
        field_scores = score_result["field_scores"]

        html += f"""
        <div class="match">
            <div class="paper-title">{gen.get('title', 'Untitled')}</div>
            <span class="similarity">{match['similarity']:.1%} title match</span>
            <div style="margin: 10px 0;">
                <strong>Score:</strong> {score_result['points']}/{score_result['total_fields']} fields
                ({score_result['score'] * 100:.1f}%)
            </div>
            <table class="field-table" style="margin-top: 15px;">
                <tr>
                    <th style="width: 150px;">Field</th>
                    <th>Generated</th>
                    <th>Ground Truth</th>
                    <th style="width: 80px;">Match</th>
                </tr>
"""

        # Show all required fields in stable order
        field_order = ["title", "author", "year", "month", "booktitle", "journal", "volume", "doi", "url"]
        ordered_fields = [f for f in field_order if f in required_fields]

        for field in ordered_fields:
            gen_val = gen.get(field, "").strip()
            gt_val = gt.get(field, "").strip()

            # Calculate similarity
            if field in field_scores:
                similarity = field_scores[field]
            else:
                similarity = 0.0 if (gen_val or gt_val) else 1.0

            # Color code based on match
            if similarity >= similarity_threshold:
                row_class = 'style="background: #d4edda;"'  # Green
                match_icon = "✓"
                match_color = "#28a745"
            elif similarity > 0:
                row_class = 'style="background: #fff3cd;"'  # Yellow
                match_icon = f"{similarity * 100:.0f}%"
                match_color = "#ffc107"
            else:
                row_class = 'style="background: #f8d7da;"'  # Red
                match_icon = "✗"
                match_color = "#dc3545"

            # Handle missing values
            gen_display = gen_val if gen_val else "<em>(missing)</em>"
            gt_display = gt_val if gt_val else "<em>(missing)</em>"

            html += f"""
                <tr {row_class}>
                    <td><strong>{field}</strong></td>
                    <td style="font-family: monospace; font-size: 12px; max-width: 400px; overflow: hidden; text-overflow: ellipsis;">{gen_display}</td>
                    <td style="font-family: monospace; font-size: 12px; max-width: 400px; overflow: hidden; text-overflow: ellipsis;">{gt_display}</td>
                    <td style="color: {match_color}; font-weight: bold; text-align: center;">{match_icon}</td>
                </tr>
"""

        html += """
            </table>
        </div>
"""

    html += f"""
        <h2>➕ In Generated Only ({len(unmatched_generated)})</h2>
        <p>Papers in the generated BibTeX that aren't in ground truth (new papers).</p>
"""

    field_order = ["title", "author", "year", "month", "booktitle", "journal", "volume", "doi", "url"]

    for entry_idx, entry in enumerate(unmatched_generated[:20]):  # Show first 20
        paper_id = f"generated-only-{entry_idx}"
        required_fields = get_required_fields(entry)
        ordered_fields = [f for f in field_order if f in required_fields]

        html += f"""
        <div class="match">
            <div class="paper-title">{entry.get('title', 'Untitled')}</div>
            <table class="field-table">
                <tr><th>Field</th><th>Generated</th><th>Ground Truth</th><th>Match</th></tr>
"""

        for field in ordered_fields:
            gen_val = entry.get(field, "").strip()
            gen_display = gen_val if gen_val else "<em>(missing)</em>"
            gt_display = "<em>(missing)</em>"

            row_class = 'style="background: #fff3cd;"'  # Yellow for missing ground truth
            match_icon = "—"
            match_color = "#6c757d"

            html += f"""
                <tr {row_class}>
                    <td><strong>{field}</strong></td>
                    <td style="font-family: monospace; font-size: 12px; max-width: 400px; overflow: hidden; text-overflow: ellipsis;">{gen_display}</td>
                    <td style="font-family: monospace; font-size: 12px; max-width: 400px; overflow: hidden; text-overflow: ellipsis;">{gt_display}</td>
                    <td style="color: {match_color}; font-weight: bold; text-align: center;">{match_icon}</td>
                </tr>
"""

        html += """
            </table>
        </div>
"""

    if len(unmatched_generated) > 20:
        html += f"<p><em>... and {len(unmatched_generated) - 20} more</em></p>"

    html += f"""
        <h2>➖ In Ground Truth Only ({len(unmatched_ground_truth)})</h2>
        <p>Papers in ground truth that weren't found in generated (missing from Google Scholar scrape).</p>
"""

    for entry_idx, entry in enumerate(unmatched_ground_truth[:20]):  # Show first 20
        paper_id = f"gt-only-{entry_idx}"
        required_fields = get_required_fields(entry)
        ordered_fields = [f for f in field_order if f in required_fields]

        html += f"""
        <div class="match">
            <div class="paper-title">{entry.get('title', 'Untitled')}</div>
            <table class="field-table">
                <tr><th>Field</th><th>Generated</th><th>Ground Truth</th><th>Match</th></tr>
"""

        for field in ordered_fields:
            gt_val = entry.get(field, "").strip()
            gen_display = "<em>(missing)</em>"
            gt_display = gt_val if gt_val else "<em>(missing)</em>"

            row_class = 'style="background: #f8d7da;"'  # Red for missing generated
            match_icon = "—"
            match_color = "#6c757d"

            html += f"""
                <tr {row_class}>
                    <td><strong>{field}</strong></td>
                    <td style="font-family: monospace; font-size: 12px; max-width: 400px; overflow: hidden; text-overflow: ellipsis;">{gen_display}</td>
                    <td style="font-family: monospace; font-size: 12px; max-width: 400px; overflow: hidden; text-overflow: ellipsis;">{gt_display}</td>
                    <td style="color: {match_color}; font-weight: bold; text-align: center;">{match_icon}</td>
                </tr>
"""

        html += """
            </table>
        </div>
"""

    if len(unmatched_ground_truth) > 20:
        html += f"<p><em>... and {len(unmatched_ground_truth) - 20} more</em></p>"

    html += """
    </div>
</body>
</html>
"""
    return html


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

    # Set output filenames based on method
    generated_bib = os.path.join(
        os.path.dirname(__file__), f"../_bibliography/papers_generated_{args.method}.bib"
    )
    evaluation_report = os.path.join(
        os.path.dirname(__file__), f"../_bibliography/bibtex_evaluation_{args.method}.html"
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
    print(f"\nGenerated BibTeX written to: {generated_bib}\n")

    print("Loading ground truth BibTeX...")
    ground_truth_entries = load_ground_truth_bibtex(GROUND_TRUTH_BIB)
    print(f"Loaded {len(ground_truth_entries)} ground truth entries\n")

    print("Matching papers...")
    matches, unmatched_gen, unmatched_gt = match_papers(
        generated_entries, ground_truth_entries
    )

    print(f"\nEvaluation Summary ({args.method} method):")
    print(f"  - Ground truth papers: {len(ground_truth_entries)}")
    print(f"  - Generated papers: {len(generated_entries)}")
    print(f"  - Matched: {len(matches)}")
    print(f"  - Coverage: {len(matches) / len(ground_truth_entries) * 100:.1f}%")
    print(f"  - In generated only (new papers): {len(unmatched_gen)}")
    print(f"  - In ground truth only (missing): {len(unmatched_gt)}")

    # Count field differences in matched papers
    total_diffs = 0
    for match in matches:
        diffs = compare_entries(match["generated"], match["ground_truth"])
        total_diffs += len(diffs)

    avg_diffs = total_diffs / len(matches) if matches else 0
    print(f"  - Average field differences per matched paper: {avg_diffs:.2f}")

    print(f"\nGenerating evaluation report...")
    html = generate_evaluation_report(matches, unmatched_gen, unmatched_gt, similarity_threshold=0.85)
    with open(evaluation_report, "w") as f:
        f.write(html)

    print(f"✓ Evaluation report written to: {evaluation_report}")
    print(f"\nOpen the report in your browser to review detailed comparisons.")


if __name__ == "__main__":
    main()
