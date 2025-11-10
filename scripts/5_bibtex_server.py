# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "flask",
#     "flask-cors",
#     "bibtexparser",
# ]
# ///
"""
BibTeX Update Server

Runs a local Flask server to handle BibTeX updates from the evaluation HTML report.

Usage:
    uv run scripts/5_bibtex_server.py

The server runs on http://localhost:5000 and provides an endpoint to update
the ground truth BibTeX file when you save edits from the HTML report.
"""

import os
import sys
import re
from typing import List, Tuple
from flask import Flask, request, jsonify
from flask_cors import CORS
import bibtexparser
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.bibdatabase import BibDatabase

app = Flask(__name__)
CORS(app)  # Enable CORS for local HTML files

# Path to ground truth BibTeX file
GROUND_TRUTH_BIB = os.path.join(
    os.path.dirname(__file__), "../_bibliography/papers.bib"
)


def load_bibtex_with_frontmatter(filepath):
    """Load BibTeX file, preserving YAML front matter."""
    with open(filepath, "r") as f:
        content = f.read()

    front_matter = ""
    bibtex_content = content

    # Check for YAML front matter
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            front_matter = f"---{parts[1]}---\n"
            bibtex_content = parts[2]

    parser = bibtexparser.bparser.BibTexParser(common_strings=True)
    bib_db = bibtexparser.loads(bibtex_content, parser)

    return front_matter, bib_db


def save_bibtex_with_frontmatter(filepath, front_matter, bib_db):
    """Save BibTeX file, preserving YAML front matter."""
    writer = BibTexWriter()
    writer.indent = "  "
    bibtex_str = writer.write(bib_db)

    with open(filepath, "w") as f:
        if front_matter:
            f.write(front_matter)
        f.write(bibtex_str)


def get_bib_chunks(lines: List[str]) -> List[str]:
    """Get bib chunks from lines."""
    index_starts = []
    for i, line in enumerate(lines):
        if line.startswith('@'):
            index_starts.append(i)

    bibs = []
    for i in range(len(index_starts) - 1):
        start = index_starts[i]
        end = index_starts[i + 1]
        bibs.append(''.join(lines[start: end]))

    if index_starts:
        bibs.append(''.join(lines[index_starts[-1]:]))
    return bibs


def sort_bibtex_file(filepath):
    """Sort BibTeX entries in reverse chronological order."""
    month_to_score = {
        'jan': 0, 'feb': 1, 'mar': 2, 'apr': 3, 'may': 4, 'jun': 5,
        'jul': 6, 'aug': 7, 'sep': 8, 'oct': 9, 'nov': 10, 'dec': 11
    }

    with open(filepath) as f:
        lines = f.readlines()

    bib_chunks: List[str] = get_bib_chunks(lines=lines)

    bib_chunks_with_scores: List[Tuple] = []
    for bib_chunk in bib_chunks:
        if 'year' not in bib_chunk or 'month' not in bib_chunk:
            continue

        month_line = [line.lower() for line in bib_chunk.split('\n')
                     if re.match(r'\s*month\s*=', line.lower())]
        year_line = [line.lower() for line in bib_chunk.split('\n')
                    if re.match(r'\s*year\s*=', line.lower())]

        if not month_line or not year_line:
            continue

        month_score = [score for month, score in month_to_score.items()
                      if month in month_line[0]]
        if not month_score:
            continue

        year_match = re.search(r'[0-9]{4}', year_line[0])
        if not year_match:
            continue

        year_score = int(year_match.group(0))
        score = year_score * 100 + month_score[0]
        bib_chunks_with_scores.append((bib_chunk, score))

    sorted_bib_chunks = sorted(bib_chunks_with_scores,
                               key=lambda tup: tup[-1],
                               reverse=True)

    with open(filepath, 'w') as f:
        f.write('---\n---\n\n')
        for bib_chunk, _ in sorted_bib_chunks:
            f.write(bib_chunk)


@app.route('/update_bibtex', methods=['POST'])
def update_bibtex():
    """Update or add an entry in the ground truth BibTeX file."""
    try:
        data = request.json
        citation_key = data.get('citation_key')
        entry_type = data.get('entry_type', 'article')
        fields = data.get('fields', {})
        fields_to_remove = data.get('fields_to_remove', [])

        if not citation_key:
            return jsonify({'error': 'Citation key is required'}), 400

        # Load current BibTeX with front matter
        front_matter, bib_db = load_bibtex_with_frontmatter(GROUND_TRUTH_BIB)

        # Find existing entry or create new one
        existing_entry = None
        for entry in bib_db.entries:
            if entry.get('ID') == citation_key:
                existing_entry = entry
                break

        if existing_entry:
            # Update existing entry
            for field, value in fields.items():
                if value:  # Update field with new value
                    existing_entry[field] = value
                elif field in existing_entry:  # Empty value means delete field
                    del existing_entry[field]

            # Remove ground truth exclusive fields that were unchecked
            for field in fields_to_remove:
                if field in existing_entry:
                    del existing_entry[field]
                    print(f"  ✗ Removed field: {field}")

            print(f"✓ Updated entry: {citation_key}")
        else:
            # Create new entry
            new_entry = {
                'ID': citation_key,
                'ENTRYTYPE': entry_type,
            }
            for field, value in fields.items():
                if value:  # Only add if value is not empty
                    new_entry[field] = value
            bib_db.entries.append(new_entry)
            print(f"✓ Added new entry: {citation_key}")

        # Save back to file
        save_bibtex_with_frontmatter(GROUND_TRUTH_BIB, front_matter, bib_db)

        # Sort the file in reverse chronological order
        print(f"  ↻ Sorting entries...")
        sort_bibtex_file(GROUND_TRUTH_BIB)

        return jsonify({
            'success': True,
            'message': f'Updated {citation_key}',
            'citation_key': citation_key
        })

    except Exception as e:
        print(f"✗ Error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'ok', 'message': 'BibTeX server is running'})


def main():
    print("=" * 60)
    print("🚀 BibTeX Update Server")
    print("=" * 60)
    print(f"Ground truth file: {GROUND_TRUTH_BIB}")
    print()
    print("Server running on: http://localhost:5001")
    print()
    print("Open your evaluation HTML report and click 'Save to Ground Truth'")
    print("to update entries.")
    print()
    print("⚠️  NOTE: Using port 5001 (port 5000 is in use by AirPlay)")
    print()
    print("Press Ctrl+C to stop the server.")
    print("=" * 60)
    print()

    # Check if ground truth file exists
    if not os.path.exists(GROUND_TRUTH_BIB):
        print(f"⚠️  Warning: Ground truth file not found: {GROUND_TRUTH_BIB}")
        print()

    app.run(debug=True, port=5001, use_reloader=False)


if __name__ == "__main__":
    main()
