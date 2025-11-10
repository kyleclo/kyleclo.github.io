# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "bibtexparser",
# ]
# ///
"""
Evaluate generated BibTeX against ground truth.

Compares two BibTeX files and generates an HTML evaluation report.

Call:
    uv run scripts/4_evaluate_bibtex.py _bibliography/papers_generated_rules.bib _bibliography/papers.bib
    uv run scripts/4_evaluate_bibtex.py _bibliography/papers_generated_llm.bib _bibliography/papers.bib

Output:
    _bibliography/bibtex_evaluation_{method}.html - Comparison report
"""

import argparse
import os
import re
from collections import defaultdict
from difflib import SequenceMatcher

import bibtexparser


def load_bibtex(filepath):
    """Load a BibTeX file."""
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


def normalize_name(name):
    """Normalize author name for comparison."""
    # Remove extra whitespace, convert to lowercase
    return " ".join(name.lower().split())


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

    # Special handling for bibtex_show field - {true}, {{true}}, and true are all equivalent
    v1_stripped = val1.strip()
    v2_stripped = val2.strip()
    if v1_stripped in ["{true}", "{{true}}", "true"] and v2_stripped in ["{true}", "{{true}}", "true"]:
        return 1.0

    v1 = normalize_name(val1)
    v2 = normalize_name(val2)
    if v1 == v2:
        return 1.0
    return SequenceMatcher(None, v1, v2).ratio()


def get_required_fields(entry):
    """Get list of required fields for this entry based on BIB.md rules.

    Universal fields (all papers): title, author, url, month, year
    Site-specific fields (all papers): bibtex_show, abstract, pdf, preview
    Conference (@inproceedings): + booktitle, [doi]
    Journal (@article): + journal, volume, doi
    ArXiv (@article): + journal, volume, arxiv
    """
    # Universal fields required for all papers
    required = {"title", "author", "url", "month", "year"}

    # Site-specific fields required for all papers
    required.update(["bibtex_show", "abstract", "pdf", "preview"])

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
        required.update(["journal", "volume", "arxiv"])
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
    <script>
        async function savePaper(matchIdx, gtId) {{
            // Collect all editable field values for this paper
            const fields = {{}};
            const matchDiv = document.getElementById(`match-${{matchIdx}}`);
            const editableCells = matchDiv.querySelectorAll('[contenteditable="true"]');

            editableCells.forEach(cell => {{
                const field = cell.dataset.field;
                let value = cell.textContent.trim();
                // Remove "(missing)" placeholder if present
                if (value === '(missing)' || value === '') {{
                    value = '';
                }}
                fields[field] = value;
            }});

            // Collect ground truth exclusive fields that should be removed
            const fieldsToRemove = [];
            const exclusiveCheckboxes = matchDiv.querySelectorAll('.gt-exclusive-checkbox');
            exclusiveCheckboxes.forEach(checkbox => {{
                if (!checkbox.checked) {{
                    // Unchecked means remove this field
                    fieldsToRemove.push(checkbox.dataset.field);
                }}
            }});

            // Get entry type from the fields
            // If journal has value → @article, if booktitle has value → @inproceedings
            const entryType = fields.journal && fields.journal.trim()
                ? 'article'
                : fields.booktitle && fields.booktitle.trim() ? 'inproceedings' : 'article';

            const data = {{
                citation_key: gtId,
                entry_type: entryType,
                fields: fields,
                fields_to_remove: fieldsToRemove
            }};

            try {{
                const response = await fetch('http://localhost:5000/update_bibtex', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                    }},
                    body: JSON.stringify(data)
                }});

                const result = await response.json();

                if (response.ok) {{
                    const statusSpan = document.getElementById(`save-status-${{matchIdx}}`);
                    statusSpan.style.display = 'inline';
                    statusSpan.textContent = '✓ Saved!';
                    setTimeout(() => {{
                        statusSpan.style.display = 'none';
                    }}, 3000);
                }} else {{
                    alert('Error saving: ' + result.error);
                }}
            }} catch (error) {{
                alert('Error: Make sure the BibTeX server is running\\n\\nRun: uv run 5_bibtex_server.py\\n\\nError details: ' + error);
            }}
        }}
    </script>
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
    field_order = ["title", "author", "year", "month", "booktitle", "journal", "volume", "doi", "url", "bibtex_show", "abstract", "pdf", "preview", "arxiv"]
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

        # Get the citation key from ground truth
        gt_id = gt.get('ID', '')

        html += f"""
        <div class="match" id="match-{match_idx}">
            <div class="paper-title">{gen.get('title', 'Untitled')}</div>
            <span class="similarity">{match['similarity']:.1%} title match</span>
            <div style="margin: 10px 0;">
                <strong>Score:</strong> {score_result['points']}/{score_result['total_fields']} fields
                ({score_result['score'] * 100:.1f}%)
                <button onclick="savePaper('{match_idx}', '{gt_id}')" style="margin-left: 20px; padding: 5px 15px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer;">
                    💾 Save to Ground Truth
                </button>
                <span id="save-status-{match_idx}" style="margin-left: 10px; color: green; display: none;">✓ Saved!</span>
            </div>
            <table class="field-table" style="margin-top: 15px;">
                <tr>
                    <th style="width: 150px;">Field</th>
                    <th>Generated (editable)</th>
                    <th>Ground Truth</th>
                    <th style="width: 80px;">Match</th>
                </tr>
"""

        # Show all fields in stable order (always show both booktitle and journal for easier editing)
        field_order = ["title", "author", "year", "month", "booktitle", "journal", "volume", "doi", "url", "bibtex_show", "abstract", "pdf", "preview", "arxiv"]
        # Display all fields in field_order, not just required ones
        ordered_fields = field_order

        for field in ordered_fields:
            gen_val = gen.get(field, "").strip()
            gt_val = gt.get(field, "").strip()

            # Calculate similarity
            if field in field_scores:
                # Field is required for this entry type, use pre-calculated score
                similarity = field_scores[field]
            else:
                # Field is not required for this entry type
                # But we still want to show if values match for easier editing
                if not gen_val and not gt_val:
                    similarity = 1.0  # Both empty - perfect match
                elif gen_val and gt_val:
                    # Both have values - calculate similarity
                    similarity = field_similarity(gen_val, gt_val)
                else:
                    # One has value, one doesn't - mismatch
                    similarity = 0.0

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

            # Handle missing values for display only
            gt_display = gt_val if gt_val else "<em>(missing)</em>"

            # For generated column, make it editable
            # Escape HTML entities in the value
            import html as html_module
            gen_val_escaped = html_module.escape(gen_val) if gen_val else ""

            html += f"""
                <tr {row_class}>
                    <td><strong>{field}</strong></td>
                    <td contenteditable="true"
                        id="field-{match_idx}-{field}"
                        data-field="{field}"
                        data-match="{match_idx}"
                        style="font-family: monospace; font-size: 12px; max-width: 400px; padding: 8px; border: 1px solid #ddd; cursor: text;"
                        onfocus="this.style.outline='2px solid #007bff'"
                        onblur="this.style.outline='none'">{gen_val_escaped if gen_val_escaped else '<em style="color: #999;">(missing)</em>'}</td>
                    <td style="font-family: monospace; font-size: 12px; max-width: 400px; overflow: hidden; text-overflow: ellipsis;">{gt_display}</td>
                    <td style="color: {match_color}; font-weight: bold; text-align: center;">{match_icon}</td>
                </tr>
"""

        # Show ground truth exclusive fields (fields in GT but not in field_order or not shown)
        gt_exclusive_fields = [f for f in gt.keys() if f not in field_order and f not in ['ID', 'ENTRYTYPE']]
        if gt_exclusive_fields:
            html += """
                <tr style="background: #e7f3ff; border-top: 2px solid #007bff;">
                    <td colspan="4" style="padding: 10px; font-weight: bold; color: #007bff;">
                        ⚙️ Ground Truth Exclusive Fields (check to keep, uncheck to remove)
                    </td>
                </tr>
"""
            for field in sorted(gt_exclusive_fields):
                gt_val = gt.get(field, "").strip()
                import html as html_module
                gt_val_escaped = html_module.escape(gt_val) if gt_val else ""

                html += f"""
                <tr style="background: #f0f8ff;">
                    <td><strong>{field}</strong></td>
                    <td style="font-family: monospace; font-size: 12px; color: #666;">
                        <em>(not in generated)</em>
                    </td>
                    <td style="font-family: monospace; font-size: 12px;">{gt_val_escaped}</td>
                    <td style="text-align: center;">
                        <input type="checkbox" class="gt-exclusive-checkbox" data-field="{field}" checked
                               style="width: 18px; height: 18px; cursor: pointer;"
                               title="Uncheck to remove this field from ground truth">
                    </td>
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

    field_order = ["title", "author", "year", "month", "booktitle", "journal", "volume", "doi", "url", "bibtex_show", "abstract", "pdf", "preview", "arxiv"]

    for entry_idx, entry in enumerate(unmatched_generated[:20]):  # Show first 20
        paper_id = f"generated-only-{entry_idx}"
        # Show all fields for easier editing
        ordered_fields = field_order

        # Generate a citation key for this new entry
        # Use simple slug from title for new entries
        title = entry.get('title', 'Untitled')
        author = entry.get('author', '')
        year = entry.get('year', '')

        # Generate key: FirstAuthorLastName + Year + FirstTitleWords
        first_author = author.split(' and ')[0].strip() if author else 'Unknown'
        last_name = first_author.split()[-1] if first_author else 'Unknown'
        last_name = re.sub(r'[^a-zA-Z]', '', last_name)

        title_words = title.split()[:3]
        title_part = ''.join([w.capitalize() for w in title_words if w.lower() not in ['a', 'an', 'the']])
        title_part = re.sub(r'[^a-zA-Z]', '', title_part)

        citation_key = f"{last_name}{year}{title_part}"

        html += f"""
        <div class="match" id="match-gen-{entry_idx}">
            <div class="paper-title">{entry.get('title', 'Untitled')}</div>
            <div style="margin: 10px 0;">
                <strong>New Paper</strong>
                <button onclick="savePaper('gen-{entry_idx}', '{citation_key}')" style="margin-left: 20px; padding: 5px 15px; background: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer;">
                    ➕ Add to Ground Truth
                </button>
                <span id="save-status-gen-{entry_idx}" style="margin-left: 10px; color: green; display: none;">✓ Saved!</span>
            </div>
            <table class="field-table">
                <tr><th>Field</th><th>Generated (editable)</th><th>Ground Truth</th><th>Match</th></tr>
"""

        import html as html_module
        for field in ordered_fields:
            gen_val = entry.get(field, "").strip()
            gen_val_escaped = html_module.escape(gen_val) if gen_val else ""
            gt_display = "<em>(missing)</em>"

            row_class = 'style="background: #fff3cd;"'  # Yellow for missing ground truth
            match_icon = "—"
            match_color = "#6c757d"

            html += f"""
                <tr {row_class}>
                    <td><strong>{field}</strong></td>
                    <td contenteditable="true"
                        id="field-gen-{entry_idx}-{field}"
                        data-field="{field}"
                        data-match="gen-{entry_idx}"
                        style="font-family: monospace; font-size: 12px; max-width: 400px; padding: 8px; border: 1px solid #ddd; cursor: text;"
                        onfocus="this.style.outline='2px solid #007bff'"
                        onblur="this.style.outline='none'">{gen_val_escaped if gen_val_escaped else '<em style="color: #999;">(missing)</em>'}</td>
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
        # Show all fields for consistency
        ordered_fields = field_order

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
    parser = argparse.ArgumentParser(description="Evaluate generated BibTeX against ground truth")
    parser.add_argument(
        "generated",
        help="Path to generated BibTeX file"
    )
    parser.add_argument(
        "ground_truth",
        help="Path to ground truth BibTeX file"
    )
    parser.add_argument(
        "--output",
        help="Path to output HTML report (default: bibtex_evaluation.html)"
    )
    args = parser.parse_args()

    # Determine output filename
    if args.output:
        output_file = args.output
    else:
        # Extract method from generated filename if possible
        basename = os.path.basename(args.generated)
        if "rules" in basename:
            method = "rules"
        elif "llm" in basename:
            method = "llm"
        else:
            method = "custom"
        output_file = os.path.join(
            os.path.dirname(args.generated),
            f"bibtex_evaluation_{method}.html"
        )

    print("Loading generated BibTeX...")
    generated_entries = load_bibtex(args.generated)
    print(f"Loaded {len(generated_entries)} generated entries\n")

    print("Loading ground truth BibTeX...")
    ground_truth_entries = load_bibtex(args.ground_truth)
    print(f"Loaded {len(ground_truth_entries)} ground truth entries\n")

    print("Matching papers...")
    matches, unmatched_gen, unmatched_gt = match_papers(
        generated_entries, ground_truth_entries
    )

    print(f"\nEvaluation Summary:")
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
    with open(output_file, "w") as f:
        f.write(html)

    print(f"✓ Evaluation report written to: {output_file}")
    print(f"\nOpen the report in your browser to review detailed comparisons.")


if __name__ == "__main__":
    main()
