"""
Scrape Google Scholar for a given author and save to a local SQLite DB.

The script writes to the DB as it scrapes. If interrupted, restarting will skip
adding papers that already exist (based on a unique hash of the title).

Call:
    python scripts/scrape_google_scholar.py

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

from scholarly import scholarly
from tqdm import tqdm

TODAY = datetime.today().strftime("%Y-%m-%d")
MY_SCHOLAR_ID = "VJS12uMAAAAJ"
# SQLite DB file to store publications
DB_FILE = f"_bibliography/gscholar_export.db"


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


def publication_exists(conn, pub_id):
    """Check if a publication with the given id already exists."""
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM publications WHERE id = ?", (pub_id,))
    return cur.fetchone() is not None


def insert_publication(conn, pub):
    """Insert publication data into the DB."""
    title = pub.get("bib", {}).get("title", "")
    if not title:
        print("Warning: publication without a title encountered. Skipping.")
        return

    pub_id = hash_title(title)
    date_added = TODAY
    full_json = json.dumps(pub)

    insert_query = """
    INSERT OR IGNORE INTO publications (id, title, date_added, full_json, validated)
    VALUES (?, ?, ?, ?, ?)
    """
    conn.execute(insert_query, (pub_id, title, date_added, full_json, 0))
    conn.commit()


if __name__ == "__main__":
    # Ensure output directory exists
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)

    # Connect to SQLite DB
    conn = sqlite3.connect(DB_FILE)
    create_db_table(conn)

    # Fetch author using ID
    author = scholarly.search_author_id(MY_SCHOLAR_ID)
    author = scholarly.fill(author)
    print(f"Processing publications for: {author['name']}")
    print(f"Total publications found: {len(author['publications'])}")

    # Process each publication and insert into DB as it is scraped
    for i, pub in enumerate(tqdm(author["publications"], desc="Publications")):
        # Extract title from summary and compute unique hash
        title = pub.get("bib", {}).get("title", "")
        if not title:
            print(f"Publication {i + 1} is missing a title. Skipping.")
            continue

        pub_id = hash_title(title)
        if publication_exists(conn, pub_id):
            print(f"Skipping publication {i + 1} (already exists): {title}")
            continue

        # Delay to avoid rate-limiting
        time.sleep(1)
        pub_filled = scholarly.fill(pub)
        print(f"Processing publication {i + 1}: {pub_filled['bib']['title']}")
        insert_publication(conn, pub_filled)

    conn.close()
    print(f"Scraping complete. {i + 1} publications have been saved to the database.")
