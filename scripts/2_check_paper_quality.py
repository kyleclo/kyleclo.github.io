# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "tqdm",
# ]
# ///
"""
Data quality checker for Google Scholar papers.

Runs automated checks and generates a report highlighting potential issues:
- Duplicate/similar paper titles
- Duplicate/similar author lists
- Missing critical fields
- Suspicious patterns

Call:
    uv run scripts/2_check_paper_quality.py

Output:
    _bibliography/quality_report.html
"""

import hashlib
import json
import os
import sqlite3
from collections import defaultdict
from difflib import SequenceMatcher
from itertools import combinations

from tqdm import tqdm

DB_FILE = os.path.join(os.path.dirname(__file__), "../_bibliography/gscholar_export.db")
REPORT_FILE = os.path.join(
    os.path.dirname(__file__), "../_bibliography/quality_report.html"
)


def text_similarity(text1, text2):
    """Calculate similarity ratio between two texts (0.0 to 1.0)."""
    t1 = text1.lower().strip()
    t2 = text2.lower().strip()
    return SequenceMatcher(None, t1, t2).ratio()


def load_papers_from_db():
    """Load all papers from the SQLite database."""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT id, title, full_json FROM publications ORDER BY title")
    rows = cur.fetchall()
    conn.close()

    papers = []
    for paper_id, title, full_json in rows:
        paper_data = json.loads(full_json)
        bib = paper_data.get("bib", {})
        # Google Scholar uses different fields for venue:
        # - 'conference' for conference papers
        # - 'journal' for journal/preprint papers
        # - 'citation' as fallback (contains venue + year)
        venue = bib.get("conference") or bib.get("journal") or bib.get("citation") or bib.get("venue", "")
        papers.append(
            {
                "id": paper_id,
                "title": bib.get("title", ""),
                "author": bib.get("author", ""),
                "venue": venue,
                "year": bib.get("pub_year", ""),
                "publisher": bib.get("publisher", ""),
                "num_citations": paper_data.get("num_citations", 0),
                "pub_url": paper_data.get("pub_url", ""),
            }
        )
    return papers


def check_similar_titles(papers, threshold=0.85):
    """Find pairs of papers with very similar titles."""
    print("Checking for similar titles...")
    similar_pairs = []

    for (i, p1), (j, p2) in tqdm(
        list(combinations(enumerate(papers), 2)), desc="Comparing titles"
    ):
        if not p1["title"] or not p2["title"]:
            continue

        similarity = text_similarity(p1["title"], p2["title"])
        if similarity >= threshold:
            similar_pairs.append(
                {
                    "paper1": p1,
                    "paper2": p2,
                    "similarity": similarity,
                    "type": "title",
                }
            )

    # Sort by similarity descending
    similar_pairs.sort(key=lambda x: x["similarity"], reverse=True)
    return similar_pairs


def check_similar_authors(papers, threshold=0.90):
    """Find pairs of papers with very similar author lists."""
    print("Checking for similar author lists...")
    similar_pairs = []

    for (i, p1), (j, p2) in tqdm(
        list(combinations(enumerate(papers), 2)), desc="Comparing authors"
    ):
        if not p1["author"] or not p2["author"]:
            continue

        similarity = text_similarity(p1["author"], p2["author"])
        if similarity >= threshold:
            similar_pairs.append(
                {
                    "paper1": p1,
                    "paper2": p2,
                    "similarity": similarity,
                    "type": "author",
                }
            )

    similar_pairs.sort(key=lambda x: x["similarity"], reverse=True)
    return similar_pairs


def check_missing_fields(papers):
    """Find papers with missing critical fields."""
    print("Checking for missing fields...")
    issues = []

    for paper in papers:
        missing = []
        if not paper["title"]:
            missing.append("title")
        if not paper["author"]:
            missing.append("author")
        if not paper["year"]:
            missing.append("year")

        if missing:
            issues.append({"paper": paper, "missing_fields": missing})

    return issues


def check_suspicious_patterns(papers):
    """Find papers with suspicious patterns."""
    print("Checking for suspicious patterns...")
    issues = []

    for paper in papers:
        flags = []

        # All caps title
        if paper["title"] and paper["title"].isupper():
            flags.append("ALL CAPS TITLE")

        # Very short title
        if paper["title"] and len(paper["title"]) < 10:
            flags.append(f"Very short title ({len(paper['title'])} chars)")

        # Very long title
        if paper["title"] and len(paper["title"]) > 200:
            flags.append(f"Very long title ({len(paper['title'])} chars)")

        # Missing venue and publisher
        if not paper["venue"] and not paper["publisher"]:
            flags.append("No venue or publisher")

        # Year outliers
        if paper["year"]:
            try:
                year = int(paper["year"])
                if year < 2000:
                    flags.append(f"Old paper ({year})")
                elif year > 2025:
                    flags.append(f"Future year ({year})")
            except ValueError:
                flags.append(f"Invalid year format: {paper['year']}")

        if flags:
            issues.append({"paper": paper, "flags": flags})

    return issues


def generate_html_report(
    papers, title_similarities, author_similarities, missing_fields, suspicious_patterns
):
    """Generate an HTML report with all findings."""
    total_papers = len(papers)
    total_issues = (
        len(title_similarities)
        + len(author_similarities)
        + len(missing_fields)
        + len(suspicious_patterns)
    )

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Paper Quality Report</title>
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
        .issue {{
            background: #fff;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 20px;
            margin: 15px 0;
        }}
        .similarity-score {{
            display: inline-block;
            background: #ffc107;
            color: #000;
            padding: 4px 12px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 14px;
        }}
        .paper-detail {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 4px;
            margin: 10px 0;
            font-family: monospace;
            font-size: 13px;
        }}
        .paper-title {{
            font-weight: bold;
            color: #212529;
            margin-bottom: 8px;
        }}
        .paper-meta {{
            color: #6c757d;
            font-size: 12px;
            margin-top: 5px;
        }}
        .flag {{
            display: inline-block;
            background: #dc3545;
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            margin: 2px;
            font-size: 12px;
        }}
        .section-count {{
            color: #dc3545;
            font-weight: bold;
        }}
        .no-issues {{
            text-align: center;
            padding: 40px;
            color: #28a745;
            font-size: 18px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Paper Quality Report</h1>

        <div class="summary">
            <div class="stat-box">
                <div class="stat-number">{total_papers}</div>
                <div class="stat-label">Total Papers</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{total_issues}</div>
                <div class="stat-label">Total Issues Found</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{len(title_similarities)}</div>
                <div class="stat-label">Similar Titles</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{len(author_similarities)}</div>
                <div class="stat-label">Similar Authors</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{len(missing_fields)}</div>
                <div class="stat-label">Missing Fields</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{len(suspicious_patterns)}</div>
                <div class="stat-label">Suspicious Patterns</div>
            </div>
        </div>
"""

    # Similar titles section
    if title_similarities:
        html += f"""
        <h2>🔍 Similar Titles <span class="section-count">({len(title_similarities)} pairs)</span></h2>
        <p>Papers with highly similar titles that might be duplicates or variations.</p>
"""
        for pair in title_similarities:
            p1, p2 = pair["paper1"], pair["paper2"]
            html += f"""
        <div class="issue">
            <span class="similarity-score">{pair['similarity']:.1%} similar</span>
            <div class="paper-detail">
                <div class="paper-title">Paper 1: {p1['title']}</div>
                <div class="paper-meta">
                    Authors: {p1['author'] or 'N/A'} |
                    Year: {p1['year'] or 'N/A'} |
                    Citations: {p1['num_citations']}
                </div>
            </div>
            <div class="paper-detail">
                <div class="paper-title">Paper 2: {p2['title']}</div>
                <div class="paper-meta">
                    Authors: {p2['author'] or 'N/A'} |
                    Year: {p2['year'] or 'N/A'} |
                    Citations: {p2['num_citations']}
                </div>
            </div>
        </div>
"""
    else:
        html += """
        <h2>🔍 Similar Titles</h2>
        <div class="no-issues">✓ No similar titles found</div>
"""

    # Similar authors section
    if author_similarities:
        html += f"""
        <h2>👥 Similar Author Lists <span class="section-count">({len(author_similarities)} pairs)</span></h2>
        <p>Papers with nearly identical author lists that might be duplicates.</p>
"""
        for pair in author_similarities:
            p1, p2 = pair["paper1"], pair["paper2"]
            html += f"""
        <div class="issue">
            <span class="similarity-score">{pair['similarity']:.1%} similar</span>
            <div class="paper-detail">
                <div class="paper-title">{p1['title']}</div>
                <div class="paper-meta">Authors: {p1['author'] or 'N/A'}</div>
            </div>
            <div class="paper-detail">
                <div class="paper-title">{p2['title']}</div>
                <div class="paper-meta">Authors: {p2['author'] or 'N/A'}</div>
            </div>
        </div>
"""
    else:
        html += """
        <h2>👥 Similar Author Lists</h2>
        <div class="no-issues">✓ No similar author lists found</div>
"""

    # Missing fields section
    if missing_fields:
        html += f"""
        <h2>⚠️ Missing Critical Fields <span class="section-count">({len(missing_fields)} papers)</span></h2>
        <p>Papers missing important metadata.</p>
"""
        for issue in missing_fields[:50]:  # Limit to first 50
            paper = issue["paper"]
            missing = ", ".join(issue["missing_fields"])
            html += f"""
        <div class="issue">
            <div class="paper-title">{paper['title'] or '(No Title)'}</div>
            <div>Missing fields: <span class="flag">{missing}</span></div>
        </div>
"""
        if len(missing_fields) > 50:
            html += f"<p><em>... and {len(missing_fields) - 50} more</em></p>"
    else:
        html += """
        <h2>⚠️ Missing Critical Fields</h2>
        <div class="no-issues">✓ No missing fields found</div>
"""

    # Suspicious patterns section
    if suspicious_patterns:
        html += f"""
        <h2>🚩 Suspicious Patterns <span class="section-count">({len(suspicious_patterns)} papers)</span></h2>
        <p>Papers with unusual characteristics that might indicate data quality issues.</p>
"""
        for issue in suspicious_patterns[:50]:  # Limit to first 50
            paper = issue["paper"]
            html += f"""
        <div class="issue">
            <div class="paper-title">{paper['title']}</div>
            <div class="paper-meta">
                Authors: {paper['author'] or 'N/A'} |
                Year: {paper['year'] or 'N/A'} |
                Venue: {paper['venue'] or 'N/A'}
            </div>
            <div style="margin-top: 10px;">
"""
            for flag in issue["flags"]:
                html += f'<span class="flag">{flag}</span> '
            html += """
            </div>
        </div>
"""
        if len(suspicious_patterns) > 50:
            html += f"<p><em>... and {len(suspicious_patterns) - 50} more</em></p>"
    else:
        html += """
        <h2>🚩 Suspicious Patterns</h2>
        <div class="no-issues">✓ No suspicious patterns found</div>
"""

    html += """
    </div>
</body>
</html>
"""
    return html


def main():
    print(f"Loading papers from {DB_FILE}...")
    papers = load_papers_from_db()
    print(f"Loaded {len(papers)} papers\n")

    # Run all checks
    title_similarities = check_similar_titles(papers, threshold=0.85)
    author_similarities = check_similar_authors(papers, threshold=0.90)
    missing_fields = check_missing_fields(papers)
    suspicious_patterns = check_suspicious_patterns(papers)

    # Generate report
    print(f"\nGenerating report...")
    html = generate_html_report(
        papers,
        title_similarities,
        author_similarities,
        missing_fields,
        suspicious_patterns,
    )

    with open(REPORT_FILE, "w") as f:
        f.write(html)

    print(f"\n✓ Report generated: {REPORT_FILE}")
    print(f"\nSummary:")
    print(f"  - Similar titles: {len(title_similarities)} pairs")
    print(f"  - Similar authors: {len(author_similarities)} pairs")
    print(f"  - Missing fields: {len(missing_fields)} papers")
    print(f"  - Suspicious patterns: {len(suspicious_patterns)} papers")
    print(f"\nOpen the report in your browser to review the findings.")


if __name__ == "__main__":
    main()
