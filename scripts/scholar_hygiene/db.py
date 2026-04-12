from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .config import DB_FILE


def connect(db_file: Path = DB_FILE) -> sqlite3.Connection:
    return sqlite3.connect(str(db_file))


def ensure_base_tables(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS publications (
            id TEXT PRIMARY KEY,
            title TEXT,
            date_added TEXT,
            full_json TEXT,
            validated INTEGER DEFAULT 0
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS versions (
            id TEXT PRIMARY KEY,
            publication_id TEXT NOT NULL,
            cluster_id TEXT NOT NULL,
            pub_url TEXT NOT NULL,
            source_json TEXT NOT NULL,
            date_scraped TEXT NOT NULL,
            FOREIGN KEY (publication_id) REFERENCES publications(id)
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_versions_pub ON versions(publication_id)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_versions_cluster ON versions(cluster_id)"
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS coauthors (
            scholar_id TEXT PRIMARY KEY,
            source_json TEXT NOT NULL,
            date_scraped TEXT NOT NULL
        )
        """
    )
    conn.commit()


def load_publications(conn: sqlite3.Connection) -> list[dict]:
    cur = conn.cursor()
    cur.execute("SELECT id, title, full_json FROM publications ORDER BY title")
    rows = cur.fetchall()
    publications = []
    for pub_id, title, full_json in rows:
        data = json.loads(full_json)
        bib = data.get("bib", {})
        publications.append(
            {
                "id": pub_id,
                "title": bib.get("title", title or ""),
                "author": bib.get("author", ""),
                "venue": bib.get("conference")
                or bib.get("journal")
                or bib.get("citation")
                or bib.get("venue", ""),
                "year": bib.get("pub_year", ""),
                "publisher": bib.get("publisher", ""),
                "num_citations": data.get("num_citations", 0),
                "pub_url": data.get("pub_url", ""),
                "cites_id": data.get("cites_id", []),
                "full_json": data,
            }
        )
    return publications


def load_versions_for_publication_ids(
    conn: sqlite3.Connection, publication_ids: set[str] | None = None
) -> dict[str, list[dict]]:
    cur = conn.cursor()
    if publication_ids:
        placeholders = ",".join("?" for _ in publication_ids)
        cur.execute(
            f"""
            SELECT publication_id, cluster_id, pub_url, source_json
            FROM versions
            WHERE publication_id IN ({placeholders})
            """,
            tuple(sorted(publication_ids)),
        )
    else:
        cur.execute("SELECT publication_id, cluster_id, pub_url, source_json FROM versions")
    grouped: dict[str, list[dict]] = {}
    for publication_id, cluster_id, pub_url, source_json in cur.fetchall():
        grouped.setdefault(publication_id, []).append(
            {
                "cluster_id": cluster_id,
                "pub_url": pub_url,
                "source_json": json.loads(source_json) if source_json else {},
            }
        )
    return grouped


def load_cached_coauthors(conn: sqlite3.Connection) -> list[dict]:
    cur = conn.cursor()
    cur.execute("SELECT scholar_id, source_json, date_scraped FROM coauthors")
    coauthors = []
    for scholar_id, source_json, date_scraped in cur.fetchall():
        payload = json.loads(source_json)
        payload["_cached_scholar_id"] = scholar_id
        payload["_date_scraped"] = date_scraped
        coauthors.append(payload)
    return coauthors

