from __future__ import annotations

import hashlib
import json
import random
import sqlite3
import time
import urllib.request
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path

try:
    from tqdm import tqdm
except ImportError:  # pragma: no cover - local fallback
    def tqdm(iterable, **_kwargs):
        return iterable

from .config import DB_FILE, get_scholar_user_id
from .db import ensure_base_tables


class ScholarFetchError(RuntimeError):
    """Raised when Google Scholar cannot be fetched reliably."""


class ScholarCaptchaError(ScholarFetchError):
    """Raised when Google Scholar returns a CAPTCHA or anti-bot page."""


def _scholarly():
    from scholarly import scholarly

    return scholarly


def today_string() -> str:
    return datetime.today().strftime("%Y-%m-%d")


def profile_url_for_user(scholar_user_id: str) -> str:
    return f"https://scholar.google.com/citations?user={scholar_user_id}&hl=en"


def fetch_profile_html(scholar_user_id: str, timeout_seconds: int = 20) -> str:
    request = urllib.request.Request(
        profile_url_for_user(scholar_user_id),
        headers={"User-Agent": "Mozilla/5.0"},
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        return response.read().decode("utf-8", errors="replace")


def detect_blocked_scholar_page(html: str) -> str | None:
    lowered = html.lower()
    if "please show you&#39;re not a robot" in lowered or "please show you're not a robot" in lowered:
        return "captcha"
    if "gsc_captcha_ccl" in lowered or "recaptcha" in lowered:
        return "captcha"
    if "<title>google scholar</title>" in lowered and "sign in" in lowered and "my profile" in lowered and "gsc_prf_in" not in lowered:
        return "unexpected_gate"
    return None


def preflight_scholar_access(scholar_user_id: str) -> None:
    html = fetch_profile_html(scholar_user_id)
    blocked_reason = detect_blocked_scholar_page(html)
    if blocked_reason == "captcha":
        raise ScholarCaptchaError(
            "Google Scholar returned a CAPTCHA page for the author profile. "
            "The scraper did not modify the database. Try again later, use a proxy-supported "
            "scholarly configuration, or use the browser-based investigation flow."
        )
    if blocked_reason:
        raise ScholarFetchError(
            "Google Scholar returned an unexpected gate page for the author profile. "
            "The scraper did not modify the database."
        )


def hash_title(title: str) -> str:
    return hashlib.md5(title.encode("utf-8")).hexdigest()


def hash_version(cluster_id: str, pub_url: str) -> str:
    return hashlib.md5(f"{cluster_id}:{pub_url}".encode("utf-8")).hexdigest()


def title_similarity(title1: str, title2: str) -> float:
    return SequenceMatcher(None, title1.lower().strip(), title2.lower().strip()).ratio()


def find_similar_title(removed_title: str, current_titles: list[str], threshold: float = 0.7):
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


def insert_paper(conn: sqlite3.Connection, paper: dict, today: str) -> None:
    title = paper.get("bib", {}).get("title", "")
    if not title:
        return
    conn.execute(
        """
        INSERT OR IGNORE INTO publications (id, title, date_added, full_json, validated)
        VALUES (?, ?, ?, ?, ?)
        """,
        (hash_title(title), title, today, json.dumps(paper), 0),
    )
    conn.commit()


def is_paper_exists(conn: sqlite3.Connection, paper_id: str) -> bool:
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM publications WHERE id = ?", (paper_id,))
    return cur.fetchone() is not None


def clean_rows(conn: sqlite3.Connection, visited_paper_ids: set[str], current_titles: list[str]) -> list[dict]:
    cur = conn.cursor()
    removed = []
    if visited_paper_ids:
        placeholders = ",".join("?" for _ in visited_paper_ids)
        cur.execute(
            f"SELECT id, title FROM publications WHERE id NOT IN ({placeholders})",
            tuple(visited_paper_ids),
        )
        removed_rows = cur.fetchall()
        conn.execute(
            f"DELETE FROM publications WHERE id NOT IN ({placeholders})",
            tuple(visited_paper_ids),
        )
    else:
        cur.execute("SELECT id, title FROM publications")
        removed_rows = cur.fetchall()
        conn.execute("DELETE FROM publications")
    conn.commit()

    for paper_id, removed_title in removed_rows:
        similar_title, score = find_similar_title(removed_title, current_titles)
        removed.append(
            {
                "id": paper_id,
                "title": removed_title,
                "similar_title": similar_title,
                "similarity": score,
            }
        )
    return removed


def is_cluster_scraped(conn: sqlite3.Connection, cluster_id: str) -> bool:
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM versions WHERE cluster_id = ? LIMIT 1", (cluster_id,))
    return cur.fetchone() is not None


def scrape_versions(conn: sqlite3.Connection, sleep_range: tuple[float, float] = (10, 15), today: str | None = None) -> int:
    scholarly = _scholarly()
    today = today or today_string()
    cur = conn.cursor()
    cur.execute("SELECT id, title, full_json FROM publications")
    rows = cur.fetchall()

    to_scrape = []
    for pub_id, title, full_json in rows:
        data = json.loads(full_json)
        for cluster_id in data.get("cites_id", []):
            if not is_cluster_scraped(conn, cluster_id):
                to_scrape.append((pub_id, title, cluster_id))

    for pub_id, title, cluster_id in tqdm(to_scrape, desc="Cluster versions"):
        if is_cluster_scraped(conn, cluster_id):
            continue
        try:
            results = scholarly.search_pubs_custom_url(f"/scholar?cluster={cluster_id}")
            found = 0
            for result in results:
                pub_url = result.get("pub_url", "")
                conn.execute(
                    """
                    INSERT OR IGNORE INTO versions
                    (id, publication_id, cluster_id, pub_url, source_json, date_scraped)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        hash_version(cluster_id, pub_url),
                        pub_id,
                        cluster_id,
                        pub_url,
                        json.dumps(result),
                        today,
                    ),
                )
                found += 1
            if found == 0:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO versions
                    (id, publication_id, cluster_id, pub_url, source_json, date_scraped)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        hash_version(cluster_id, "__empty__"),
                        pub_id,
                        cluster_id,
                        "__empty__",
                        "{}",
                        today,
                    ),
                )
            conn.commit()
        except Exception as exc:
            conn.execute(
                """
                INSERT OR IGNORE INTO versions
                (id, publication_id, cluster_id, pub_url, source_json, date_scraped)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    hash_version(cluster_id, "__error__"),
                    pub_id,
                    cluster_id,
                    "__error__",
                    json.dumps({"error": str(exc)}),
                    today,
                ),
            )
            conn.commit()
        time.sleep(random.uniform(*sleep_range))
    return len(to_scrape)


def refresh_profile(
    conn: sqlite3.Connection,
    scholar_user_id: str | None = None,
    profile_sleep_seconds: float = 1.0,
    version_sleep_range: tuple[float, float] = (10, 15),
) -> dict:
    scholarly = _scholarly()
    scholar_user_id = scholar_user_id or get_scholar_user_id()
    today = today_string()
    ensure_base_tables(conn)
    preflight_scholar_access(scholar_user_id)

    try:
        author = scholarly.search_author_id(scholar_user_id)
        author = scholarly.fill(author)
    except Exception as exc:
        message = str(exc)
        if "NoneType" in message or "canonical" in message:
            raise ScholarFetchError(
                "scholarly failed to parse the Google Scholar profile page. "
                "This usually means Scholar returned a blocked or changed page."
            ) from exc
        raise

    scraped_ids = set()
    current_titles = []
    inserted = 0
    for paper in tqdm(author.get("publications", []), desc="Profile publications"):
        title = paper.get("bib", {}).get("title", "")
        if not title:
            continue
        paper_id = hash_title(title)
        scraped_ids.add(paper_id)
        current_titles.append(title)
        if is_paper_exists(conn, paper_id):
            continue
        time.sleep(profile_sleep_seconds)
        insert_paper(conn, scholarly.fill(paper), today)
        inserted += 1

    removed = clean_rows(conn, scraped_ids, current_titles)
    scraped_versions = scrape_versions(conn, sleep_range=version_sleep_range, today=today)
    return {
        "author_name": author.get("name", ""),
        "profile_paper_count": len(author.get("publications", [])),
        "inserted_publications": inserted,
        "removed_publications": removed,
        "scraped_cluster_count": scraped_versions,
    }


def refresh_profile_to_path(db_file: Path = DB_FILE, scholar_user_id: str | None = None) -> dict:
    db_file.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_file))
    try:
        return refresh_profile(conn, scholar_user_id=scholar_user_id)
    finally:
        conn.close()
