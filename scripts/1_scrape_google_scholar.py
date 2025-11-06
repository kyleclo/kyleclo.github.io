# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "scholarly",
#     "tqdm",
# ]
# ///
"""
Scrape Google Scholar for a given author and save to a local SQLite DB.

The script writes to the DB as it scrapes. If interrupted, restarting will skip
adding papers that already exist (based on a unique hash of the title).

Call:
    uv run scripts/1_scrape_google_scholar.py

Local testing of DB:

    sqlite3 _bibliography/gscholar_export.db
    .tables
    .schema publications
    .mode column
    .headers on
    SELECT * FROM publications LIMIT 1;
    SELECT COUNT(*) FROM publications;
"""

import hashlib
import json
import os
import sqlite3
import time
from datetime import datetime
from difflib import SequenceMatcher

from scholarly import scholarly
from tqdm import tqdm

TODAY = datetime.today().strftime("%Y-%m-%d")
MY_SCHOLAR_ID = "VJS12uMAAAAJ"
# SQLite DB file to store papers
DB_FILE = os.path.join(os.path.dirname(__file__), "../_bibliography/gscholar_export.db")


def create_db_table(conn): 
    """Create publications table if it does not exist."""
    create_table_query = """
    CREATE TABLE IF NOT EXISTS publications (
        id TEXT PRIMARY KEY,
        title TEXT,
        date_added TEXT,
        full_json TEXT,
        validated INTEGER DEFAULT 0
    )
    """
    conn.execute(create_table_query)
    conn.commit()


def hash_title(title):
    """Generate MD5 hash of the title."""
    return hashlib.md5(title.encode("utf-8")).hexdigest()


def is_paper_exists(conn, paper_id) -> bool:
    """Check if a publication with the given id already exists."""
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM publications WHERE id = ?", (paper_id,))
    return cur.fetchone() is not None


def insert_paper(conn, paper):
    """Insert paper data into the DB."""
    title = paper.get("bib", {}).get("title", "")
    if not title:
        print("Warning: paper without a title encountered. Skipping.")
        return

    paper_id = hash_title(title)
    date_added = TODAY
    full_json = json.dumps(paper)

    insert_query = """
    INSERT OR IGNORE INTO publications (id, title, date_added, full_json, validated)
    VALUES (?, ?, ?, ?, ?)
    """
    conn.execute(insert_query, (paper_id, title, date_added, full_json, 0))
    conn.commit()


def title_similarity(title1, title2):
    """Calculate similarity ratio between two titles (0.0 to 1.0)."""
    # Normalize titles: lowercase and strip whitespace
    t1 = title1.lower().strip()
    t2 = title2.lower().strip()
    return SequenceMatcher(None, t1, t2).ratio()


def find_similar_title(removed_title, current_titles, threshold=0.7):
    """Find the most similar title from current_titles.
    Returns (best_match, similarity_score) or (None, 0.0) if none found."""
    best_match = None
    best_score = 0.0

    for title in current_titles:
        score = title_similarity(removed_title, title)
        if score > best_score:
            best_score = score
            best_match = title

    if best_score >= threshold:
        return best_match, best_score
    return None, 0.0


def clean_rows(conn, visited_paper_ids, current_titles):
    """Remove rows from the DB if their publication ID is not in visited_paper_ids,
    check for similar papers, and log which papers were removed."""
    cur = conn.cursor()

    removed_papers = []
    if visited_paper_ids:
        placeholders = ",".join("?" for _ in visited_paper_ids)
        # Select rows that will be deleted so we can log them.
        select_query = (
            f"SELECT id, title FROM publications WHERE id NOT IN ({placeholders})"
        )
        cur.execute(select_query, tuple(visited_paper_ids))
        removed_papers = cur.fetchall()

        delete_query = f"DELETE FROM publications WHERE id NOT IN ({placeholders})"
        conn.execute(delete_query, tuple(visited_paper_ids))
    else:
        # If no papers were scraped, remove all rows.
        cur.execute("SELECT id, title FROM publications")
        removed_papers = cur.fetchall()
        conn.execute("DELETE FROM publications")
    conn.commit()

    if removed_papers:
        print("\n" + "=" * 80)
        print("PAPERS REMOVED FROM DATABASE")
        print("=" * 80)
        for paper_id, removed_title in removed_papers:
            similar_title, score = find_similar_title(removed_title, current_titles)

            print(f"\n❌ Removed: {removed_title}")
            print(f"   ID: {paper_id}")

            if similar_title:
                print(f"   ⚠️  SIMILAR PAPER FOUND (similarity: {score:.1%}):")
                print(f"   ✓  Current: {similar_title}")
                print(f"   → Likely a duplicate/merge on Google Scholar")
            else:
                print(f"   ⚠️  NO SIMILAR PAPER FOUND")
                print(f"   → This paper may have been genuinely removed from your profile")
        print("=" * 80 + "\n")


if __name__ == "__main__":
    # Ensure output directory exists
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)

    # Connect to SQLite DB
    conn = sqlite3.connect(DB_FILE)
    create_db_table(conn)

    # Fetch author using ID
    author = scholarly.search_author_id(MY_SCHOLAR_ID)
    author = scholarly.fill(author)
    print(f"Processing papers for: {author['name']}")
    print(f"Total papers found: {len(author['publications'])}")

    # Set to store publication IDs from the website
    scraped_paper_ids = set()
    # List to store current paper titles for similarity checking
    current_titles = []

    # Process each publication and insert into DB as it is scraped
    for i, paper in enumerate(tqdm(author["publications"])):
        # Extract title from summary and compute unique hash
        title = paper.get("bib", {}).get("title", "")
        if not title:
            print(f"Paper {i + 1} is missing a title. Skipping.")
            continue

        paper_id = hash_title(title)
        scraped_paper_ids.add(paper_id)
        current_titles.append(title)

        if is_paper_exists(conn, paper_id):
            print(f"Skipping paper {i + 1} (already exists): {title}")
            continue

        # Delay to avoid rate-limiting
        time.sleep(1)
        paper_filled = scholarly.fill(paper)
        print(f"Inserting paper {i + 1}: {paper_filled['bib']['title']}")
        insert_paper(conn, paper_filled)

    # After scraping, remove papers that are no longer present on the website.
    clean_rows(conn, scraped_paper_ids, current_titles)

    conn.close()
    print("Scraping complete. Database has been updated.")
