from __future__ import annotations

import json
import random
import sqlite3
import time
from datetime import datetime, timedelta

from .config import get_scholar_user_id

CACHE_DAYS = 30


def _scholarly():
    from scholarly import scholarly

    return scholarly


def is_coauthor_cached(conn: sqlite3.Connection, scholar_id: str) -> bool:
    cur = conn.cursor()
    cur.execute(
        "SELECT date_scraped FROM coauthors WHERE scholar_id = ?",
        (scholar_id,),
    )
    row = cur.fetchone()
    if not row:
        return False
    scraped_date = datetime.strptime(row[0], "%Y-%m-%d")
    return (datetime.today() - scraped_date) < timedelta(days=CACHE_DAYS)


def fetch_my_coauthors() -> list[dict]:
    scholarly = _scholarly()
    author = scholarly.search_author_id(get_scholar_user_id())
    author = scholarly.fill(author, sections=["coauthors"])
    return author.get("coauthors", [])


def fetch_and_cache_coauthor_profile(
    conn: sqlite3.Connection, coauthor_stub: dict, today: str
) -> dict | None:
    scholar_id = coauthor_stub.get("scholar_id", "")
    if not scholar_id:
        return None

    cur = conn.cursor()
    if is_coauthor_cached(conn, scholar_id):
        cur.execute(
            "SELECT source_json FROM coauthors WHERE scholar_id = ?",
            (scholar_id,),
        )
        row = cur.fetchone()
        if row:
            return json.loads(row[0])

    scholarly = _scholarly()
    try:
        author = scholarly.search_author_id(scholar_id)
        author = scholarly.fill(author, sections=["publications"])
        filled_pubs = []
        for pub in author.get("publications", []):
            try:
                filled_pubs.append(scholarly.fill(pub))
                time.sleep(random.uniform(1, 2))
            except Exception:
                filled_pubs.append(pub)
        author["publications"] = filled_pubs
        conn.execute(
            """
            INSERT OR REPLACE INTO coauthors (scholar_id, source_json, date_scraped)
            VALUES (?, ?, ?)
            """,
            (scholar_id, json.dumps(author), today),
        )
        conn.commit()
        return author
    except Exception:
        return None


def refresh_coauthor_cache(conn: sqlite3.Connection, today: str) -> dict:
    coauthors = fetch_my_coauthors()
    refreshed = 0
    for stub in coauthors:
        scholar_id = stub.get("scholar_id", "")
        if not scholar_id:
            continue
        cached = is_coauthor_cached(conn, scholar_id)
        profile = fetch_and_cache_coauthor_profile(conn, stub, today)
        if profile and not cached:
            refreshed += 1
            time.sleep(random.uniform(5, 8))
    return {"coauthor_count": len(coauthors), "refreshed_profiles": refreshed}

