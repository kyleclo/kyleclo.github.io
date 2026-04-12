from __future__ import annotations

import json
from datetime import datetime

from .coauthors import refresh_coauthor_cache
from .config import ISSUES_JSON_FILE, STATE_JSON_FILE
from .db import connect, ensure_base_tables, load_cached_coauthors, load_publications, load_versions_for_publication_ids
from .detector import (
    detect_metadata_anomalies,
    detect_missing_profile_articles,
    detect_under_clustered_articles,
    write_issue_artifacts,
)
from .expected import load_expected_papers
from .ui_artifacts import load_add_articles_candidates
from .utils import title_similarity


def run_refresh(refresh_profile_data: bool = True, refresh_coauthors_data: bool = False) -> dict:
    from .ingest import refresh_profile, today_string

    conn = connect()
    ensure_base_tables(conn)
    summary = {"refreshed_profile": None, "refreshed_coauthors": None}
    try:
        if refresh_profile_data:
            summary["refreshed_profile"] = refresh_profile(conn)
        if refresh_coauthors_data:
            summary["refreshed_coauthors"] = refresh_coauthor_cache(conn, today_string())
        return summary
    finally:
        conn.close()


def collect_issues() -> list[dict]:
    conn = connect()
    try:
        publications = load_publications(conn)
        versions_by_publication = load_versions_for_publication_ids(
            conn, {publication["id"] for publication in publications}
        )
        cached_coauthors = load_cached_coauthors(conn)
    finally:
        conn.close()

    expected_papers = load_expected_papers()
    add_articles_candidates = load_add_articles_candidates()

    missing = detect_missing_profile_articles(
        expected_papers,
        publications,
        cached_coauthors,
        add_articles_candidates=add_articles_candidates,
    )
    clusters = detect_under_clustered_articles(
        publications,
        cached_coauthors,
        add_articles_candidates=add_articles_candidates,
    )
    metadata = detect_metadata_anomalies(publications, versions_by_publication, expected_papers)

    issues = sorted(
        missing + clusters + metadata,
        key=lambda issue: (-issue["score"], issue["type"], issue["title"].lower()),
    )
    write_issue_artifacts(issues, generated_at=datetime.now().isoformat())
    return issues


def related_add_articles_candidates(issue: dict, candidates: list[dict]) -> tuple[list[dict], list[dict]]:
    evidence = issue.get("evidence", {})
    candidate = evidence.get("add_articles_candidate", {})
    if not candidate:
        return [], []

    search_query = candidate.get("search_query", "")
    issue_title = issue.get("title", "")
    candidate_title = candidate.get("title", "")
    candidate_doc_id = candidate.get("doc_id", "")

    def is_related(row: dict) -> bool:
        if search_query and row.get("search_query", "") != search_query:
            return False
        row_title = row.get("title", "")
        return (
            title_similarity(issue_title, row_title) >= 0.72
            or title_similarity(candidate_title, row_title) >= 0.72
        )

    related = [row for row in candidates if is_related(row)]
    in_profile = []
    not_in_profile = []
    for row in related:
        if row.get("doc_id", "") == candidate_doc_id:
            continue
        if row.get("in_profile"):
            in_profile.append(row)
        else:
            not_in_profile.append(row)

    key_fn = lambda row: row.get("title", "").lower()
    return sorted(in_profile, key=key_fn), sorted(not_in_profile, key=key_fn)


def review_issues(issue_type: str | None = None, limit: int = 20) -> str:
    if not ISSUES_JSON_FILE.exists():
        issues = collect_issues()
    else:
        issues = json.loads(ISSUES_JSON_FILE.read_text())
    if issue_type:
        issues = [issue for issue in issues if issue["type"] == issue_type]
    add_articles_candidates = load_add_articles_candidates()

    lines = []
    for index, issue in enumerate(issues[:limit], start=1):
        lines.append(
            f"{index}. [{issue['type']}] {issue['title']} "
            f"(confidence={issue['confidence']}, score={issue['score']}, status={issue['status']})"
        )
        lines.append(f"   Action: {issue['recommended_action']}")
        evidence = issue.get("evidence", {})
        reasons = evidence.get("reasons", [])
        if reasons:
            lines.append(f"   Evidence: {'; '.join(reasons)}")
        add_articles_candidate = evidence.get("add_articles_candidate", {})
        if add_articles_candidate:
            profile_entry = evidence.get("left", {})
            if profile_entry:
                lines.append(
                    "   Profile Entry: "
                    f"{profile_entry.get('title', '')} "
                    f"(id={profile_entry.get('id', '')}, year={profile_entry.get('year', '')}, "
                    f"citations={profile_entry.get('citations', '')})"
                )
            title = add_articles_candidate.get("title", "")
            doc_id = add_articles_candidate.get("doc_id", "")
            if title:
                lines.append(f"   Candidate: {title}")
            if doc_id:
                lines.append(f"   Candidate Doc ID: {doc_id}")
            authors_venue = add_articles_candidate.get("authors_venue", "")
            if authors_venue:
                lines.append(f"   Candidate Meta: {authors_venue}")
            if add_articles_candidate.get("title_url"):
                lines.append(f"   Candidate URL: {add_articles_candidate['title_url']}")
            if add_articles_candidate.get("artifact_file"):
                lines.append(f"   Artifact: {add_articles_candidate['artifact_file']}")
            related_in_profile, related_not_in_profile = related_add_articles_candidates(
                issue,
                add_articles_candidates,
            )
            if related_in_profile:
                lines.append(
                    "   Related In-Profile: "
                    + " | ".join(
                        f"{row.get('doc_id', '')}: {row.get('title', '')}"
                        for row in related_in_profile[:4]
                    )
                )
            if related_not_in_profile:
                lines.append(
                    "   Related Not-In-Profile: "
                    + " | ".join(
                        f"{row.get('doc_id', '')}: {row.get('title', '')}"
                        for row in related_not_in_profile[:4]
                    )
                )
        queries = issue.get("manual_queries", [])
        if queries:
            lines.append(f"   Search: {queries[0]}")
    if not lines:
        return "No issues found."
    return "\n".join(lines)


def verify_issues() -> dict:
    previous_state = json.loads(STATE_JSON_FILE.read_text()) if STATE_JSON_FILE.exists() else {}
    previous_ids = set(previous_state.get("issue_ids", []))
    issues = collect_issues()
    current_ids = {issue["id"] for issue in issues}
    return {
        "previous_issue_count": len(previous_ids),
        "current_issue_count": len(current_ids),
        "resolved_issue_ids": sorted(previous_ids - current_ids),
        "new_issue_ids": sorted(current_ids - previous_ids),
        "still_open_issue_ids": sorted(previous_ids & current_ids),
    }
