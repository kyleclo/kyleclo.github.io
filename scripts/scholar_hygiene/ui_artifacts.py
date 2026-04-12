from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable

from .config import SCHOLAR_UI_ARTIFACT_DIR


def extract_year(text: str) -> str:
    match = re.search(r"(19|20)\d{2}", text or "")
    return match.group(0) if match else ""


def load_add_articles_candidates(artifact_dir: Path | None = None) -> list[dict]:
    base_dir = artifact_dir or SCHOLAR_UI_ARTIFACT_DIR
    if not base_dir.exists():
        return []

    candidates_by_key: dict[str, dict] = {}
    for path in sorted(base_dir.glob("*_add_articles.json")):
        try:
            payload = json.loads(path.read_text())
        except json.JSONDecodeError:
            continue
        if not payload.get("rows"):
            # An empty Add Articles capture is not strong enough evidence to
            # supersede previously captured positive rows for the same query.
            continue
        for row in payload.get("rows", []):
            candidate = dict(row)
            candidate["artifact_file"] = str(path)
            candidate["search_query"] = payload.get("search_query", "")
            candidate["captured_url"] = payload.get("captured_url", "")
            candidate["result_stats"] = payload.get("result_stats", {})
            candidate["year"] = extract_year(row.get("authors_venue", ""))
            candidate["author"] = row.get("authors_venue", "")
            candidate["artifact_mtime"] = path.stat().st_mtime
            key = candidate.get("doc_id") or f"{candidate.get('title','')}|{candidate.get('search_query','')}"
            existing = candidates_by_key.get(key)
            if existing is None or candidate["artifact_mtime"] >= existing.get("artifact_mtime", 0):
                candidates_by_key[key] = candidate
    return sorted(
        candidates_by_key.values(),
        key=lambda candidate: (
            candidate.get("search_query", "").lower(),
            candidate.get("title", "").lower(),
        ),
    )


def format_add_articles_candidates(
    candidates: Iterable[dict],
    *,
    in_profile: bool | None = None,
    limit: int = 20,
) -> str:
    rows = list(candidates)
    if in_profile is not None:
        rows = [row for row in rows if bool(row.get("in_profile")) is in_profile]

    lines = []
    for index, row in enumerate(rows[:limit], start=1):
        status = "in profile" if row.get("in_profile") else "not in profile"
        lines.append(
            f"{index}. {row.get('title', '')} "
            f"({status}, doc_id={row.get('doc_id', '')}, query={row.get('search_query', '')})"
        )
        authors_venue = row.get("authors_venue", "")
        if authors_venue:
            lines.append(f"   Meta: {authors_venue}")
        title_url = row.get("title_url", "")
        if title_url:
            lines.append(f"   URL: {title_url}")
        artifact = row.get("artifact_file", "")
        if artifact:
            lines.append(f"   Artifact: {artifact}")
    if not lines:
        return "No add-articles evidence found."
    return "\n".join(lines)
