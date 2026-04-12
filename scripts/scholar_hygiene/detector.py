from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .config import DISMISSALS_JSON_FILE, ISSUES_CSV_FILE, ISSUES_JSON_FILE, STATE_JSON_FILE
from .utils import author_overlap_score, normalize_text, safe_int, title_similarity, token_jaccard


@dataclass
class MatchResult:
    score: float
    reasons: list[str]
    matched_by_identifier: bool = False


def publication_identifier_set(record: dict) -> set[str]:
    identifiers = set()
    full_json = record.get("full_json", {})
    bib = full_json.get("bib", {})
    for key in ("doi", "eprint", "arxiv"):
        value = bib.get(key) or record.get(key)
        if value:
            identifiers.add(str(value).lower())
    for key in ("pub_url", "url"):
        value = full_json.get(key) or bib.get(key) or record.get(key)
        if value:
            lowered = str(value).lower()
            identifiers.add(lowered)
            if "arxiv.org/abs/" in lowered:
                identifiers.add(lowered.rsplit("/", 1)[-1])
    return identifiers


def expected_identifier_set(record: dict) -> set[str]:
    identifiers = set()
    for key in ("doi", "arxiv", "url"):
        value = record.get(key)
        if value:
            identifiers.add(str(value).lower())
    return identifiers


def score_expected_to_publication(expected: dict, publication: dict) -> MatchResult:
    reasons = []
    score = 0.0
    id_overlap = expected_identifier_set(expected) & publication_identifier_set(publication)
    if id_overlap:
        reasons.append(f"identifier overlap: {sorted(id_overlap)[0]}")
        score += 1.0

    title_score = title_similarity(expected["title"], publication["title"])
    if title_score >= 0.9:
        reasons.append(f"title similarity {title_score:.2f}")
        score += 0.75
    elif title_score >= 0.8:
        reasons.append(f"title similarity {title_score:.2f}")
        score += 0.45

    token_score = token_jaccard(expected["title"], publication["title"])
    if token_score >= 0.75:
        reasons.append(f"title token overlap {token_score:.2f}")
        score += 0.25

    author_score = author_overlap_score(expected.get("author", ""), publication.get("author", ""))
    if author_score >= 0.6:
        reasons.append(f"author overlap {author_score:.2f}")
        score += 0.25

    expected_year = safe_int(expected.get("year"))
    pub_year = safe_int(publication.get("year"))
    if expected_year and pub_year and abs(expected_year - pub_year) <= 1:
        reasons.append(f"year proximity {expected_year}/{pub_year}")
        score += 0.15

    return MatchResult(score=score, reasons=reasons, matched_by_identifier=bool(id_overlap))


def score_expected_to_coauthor_publication(expected: dict, coauthor_name: str, publication: dict) -> MatchResult:
    result = score_expected_to_publication(expected, publication)
    if result.score > 0:
        result.reasons.append(f"found on coauthor profile: {coauthor_name}")
        result.score += 0.1
    return result


def score_expected_to_add_articles_candidate(expected: dict, candidate: dict) -> MatchResult:
    publication_like = {
        "title": candidate.get("title", ""),
        "author": candidate.get("author", ""),
        "year": candidate.get("year", ""),
        "full_json": {
            "pub_url": candidate.get("title_url", ""),
        },
    }
    result = score_expected_to_publication(expected, publication_like)
    if candidate.get("in_profile"):
        return MatchResult(
            score=0.0,
            reasons=["candidate row already marked in profile"],
        )
    if result.score > 0:
        query = candidate.get("search_query") or "unknown query"
        result.reasons.append(f"found in Add articles results: {query}")
        result.score += 0.2
        bonus, bonus_reason = query_specificity_bonus(expected["title"], query)
        if bonus > 0:
            result.score += bonus
            result.reasons.append(bonus_reason)
        result.reasons.append("candidate row not marked in profile")
    return result


def score_publication_to_add_articles_candidate(publication: dict, candidate: dict) -> MatchResult:
    publication_like = {
        "title": candidate.get("title", ""),
        "author": candidate.get("author", ""),
        "year": candidate.get("year", ""),
        "full_json": {
            "pub_url": candidate.get("title_url", ""),
        },
    }
    result = score_expected_to_publication(publication, publication_like)
    if result.score > 0:
        query = candidate.get("search_query") or "unknown query"
        result.reasons.append(f"found in Add articles results: {query}")
        bonus, bonus_reason = query_specificity_bonus(publication["title"], query)
        if bonus > 0:
            result.score += bonus
            result.reasons.append(bonus_reason)
        if candidate.get("in_profile"):
            result.reasons.append("candidate row already marked in profile")
        else:
            result.score += 0.25
            result.reasons.append("candidate row not marked in profile")
    return result


def query_specificity_bonus(title: str, query: str) -> tuple[float, str]:
    normalized_query = normalize_text(query)
    if not normalized_query:
        return 0.0, ""

    title_ratio = title_similarity(title, query)
    token_ratio = token_jaccard(title, query)
    if title_ratio >= 0.85 or token_ratio >= 0.95:
        return 0.35, f"query closely matches title ({max(title_ratio, token_ratio):.2f})"
    if title_ratio >= 0.65 or token_ratio >= 0.6:
        return 0.2, f"query strongly overlaps title ({max(title_ratio, token_ratio):.2f})"
    if title_ratio >= 0.45 or token_ratio >= 0.35:
        return 0.1, f"query overlaps title ({max(title_ratio, token_ratio):.2f})"
    return 0.0, ""


def classify_confidence(score: float) -> str:
    if score >= 1.2:
        return "high"
    if score >= 0.85:
        return "medium"
    return "low"


def build_manual_queries(expected: dict) -> list[str]:
    title = expected["title"]
    queries = [f"\"{title}\""]
    if expected.get("author"):
        queries.append(f"\"{title}\" \"{expected['author'].split(' and ')[0]}\"")
    if expected.get("doi"):
        queries.append(expected["doi"])
    if expected.get("arxiv"):
        queries.append(expected["arxiv"])
    return queries


def detect_missing_profile_articles(
    expected_papers: list[dict],
    publications: list[dict],
    coauthors: list[dict],
    add_articles_candidates: list[dict] | None = None,
) -> list[dict]:
    issues = []
    add_articles_candidates = add_articles_candidates or []
    for expected in expected_papers:
        best_profile_match = max(
            (score_expected_to_publication(expected, publication) for publication in publications),
            key=lambda item: item.score,
            default=MatchResult(score=0.0, reasons=[]),
        )
        if best_profile_match.score >= 1.0:
            continue

        best_coauthor = None
        for profile in coauthors:
            coauthor_name = profile.get("name", "Unknown")
            for publication in profile.get("publications", []):
                candidate = {
                    "title": publication.get("bib", {}).get("title", ""),
                    "author": publication.get("bib", {}).get("author", ""),
                    "year": publication.get("bib", {}).get("pub_year", ""),
                    "full_json": publication,
                }
                result = score_expected_to_coauthor_publication(expected, coauthor_name, candidate)
                if best_coauthor is None or result.score > best_coauthor["result"].score:
                    best_coauthor = {
                        "result": result,
                        "coauthor_name": coauthor_name,
                        "publication": publication,
                    }

        if not best_coauthor or best_coauthor["result"].score < 0.85:
            best_coauthor = None

        best_add_articles = None
        for candidate in add_articles_candidates:
            result = score_expected_to_add_articles_candidate(expected, candidate)
            if best_add_articles is None or result.score > best_add_articles["result"].score:
                best_add_articles = {
                    "result": result,
                    "candidate": candidate,
                }

        evidence_source = None
        evidence_score = 0.0
        if best_coauthor and best_coauthor["result"].score >= 0.85:
            evidence_source = ("coauthor", best_coauthor)
            evidence_score = best_coauthor["result"].score
        if best_add_articles and best_add_articles["result"].score >= 0.85 and best_add_articles["result"].score > evidence_score:
            evidence_source = ("add_articles", best_add_articles)
            evidence_score = best_add_articles["result"].score
        if evidence_source is None:
            continue

        issue_id = f"missing:{expected['id']}"
        source_kind, source_payload = evidence_source
        evidence = {
            "expected_paper": expected,
            "best_profile_match": {
                "score": best_profile_match.score,
                "reasons": best_profile_match.reasons,
            },
        }
        score = evidence_score
        if source_kind == "coauthor":
            evidence.update(
                {
                    "coauthor_name": source_payload["coauthor_name"],
                    "coauthor_title": source_payload["publication"].get("bib", {}).get("title", ""),
                    "coauthor_citations": source_payload["publication"].get("num_citations", 0),
                    "reasons": source_payload["result"].reasons,
                }
            )
        else:
            candidate = source_payload["candidate"]
            evidence.update(
                {
                    "add_articles_candidate": {
                        "title": candidate.get("title", ""),
                        "title_url": candidate.get("title_url", ""),
                        "authors_venue": candidate.get("authors_venue", ""),
                        "doc_id": candidate.get("doc_id", ""),
                        "search_query": candidate.get("search_query", ""),
                        "captured_url": candidate.get("captured_url", ""),
                        "artifact_file": candidate.get("artifact_file", ""),
                        "in_profile": candidate.get("in_profile", False),
                    },
                    "reasons": source_payload["result"].reasons,
                }
            )
        issues.append(
            {
                "id": issue_id,
                "type": "missing_profile_article",
                "title": expected["title"],
                "confidence": classify_confidence(score),
                "score": round(score, 3),
                "recommended_action": "Search Google Scholar Add Articles with the suggested queries and attach the matching paper to your profile.",
                "manual_queries": build_manual_queries(expected),
                "evidence": evidence,
            }
        )
    return issues


def detect_under_clustered_articles(
    publications: list[dict],
    coauthors: list[dict],
    add_articles_candidates: list[dict] | None = None,
) -> list[dict]:
    issues = []
    seen_pairs = set()
    add_articles_candidates = add_articles_candidates or []

    for index, left in enumerate(publications):
        left_clusters = set(left.get("cites_id", []))
        for right in publications[index + 1 :]:
            right_clusters = set(right.get("cites_id", []))
            shared_clusters = sorted(left_clusters & right_clusters)
            title_score = title_similarity(left["title"], right["title"])
            author_score = author_overlap_score(left.get("author", ""), right.get("author", ""))
            year_left = safe_int(left.get("year"))
            year_right = safe_int(right.get("year"))
            year_close = year_left and year_right and abs(year_left - year_right) <= 1

            score = 0.0
            reasons = []
            if shared_clusters:
                reasons.append(f"shared cluster ids: {', '.join(shared_clusters[:3])}")
                score += 1.1
            if title_score >= 0.85:
                reasons.append(f"title similarity {title_score:.2f}")
                score += 0.35
            if author_score >= 0.6:
                reasons.append(f"author overlap {author_score:.2f}")
                score += 0.25
            if year_close:
                reasons.append(f"year proximity {year_left}/{year_right}")
                score += 0.1

            coauthor_support = []
            for profile in coauthors:
                for publication in profile.get("publications", []):
                    coauthor_title = publication.get("bib", {}).get("title", "")
                    if (
                        title_similarity(left["title"], coauthor_title) >= 0.84
                        and title_similarity(right["title"], coauthor_title) >= 0.84
                    ):
                        coauthor_support.append(profile.get("name", "Unknown"))
                        break
            if coauthor_support:
                reasons.append(f"coauthor sees a single likely merged paper: {', '.join(sorted(set(coauthor_support))[:2])}")
                score += 0.2

            if score < 0.9:
                continue

            pair_key = tuple(sorted((left["id"], right["id"])))
            if pair_key in seen_pairs:
                continue
            seen_pairs.add(pair_key)
            issues.append(
                {
                    "id": f"cluster:{pair_key[0]}:{pair_key[1]}",
                    "type": "under_clustered_profile_article",
                    "title": left["title"],
                    "confidence": classify_confidence(score),
                    "score": round(score, 3),
                    "recommended_action": "Open both profile entries in Scholar and merge them if they represent the same paper.",
                    "manual_queries": [f"\"{left['title']}\"", f"\"{right['title']}\""],
                    "evidence": {
                        "left": {
                            "id": left["id"],
                            "title": left["title"],
                            "citations": left["num_citations"],
                            "year": left["year"],
                        },
                        "right": {
                            "id": right["id"],
                            "title": right["title"],
                            "citations": right["num_citations"],
                            "year": right["year"],
                        },
                        "shared_clusters": shared_clusters,
                        "reasons": reasons,
                    },
                }
            )

    for publication in publications:
        best_candidate = None
        for candidate in add_articles_candidates:
            if candidate.get("in_profile"):
                continue
            result = score_publication_to_add_articles_candidate(publication, candidate)
            if best_candidate is None or result.score > best_candidate["result"].score:
                best_candidate = {
                    "result": result,
                    "candidate": candidate,
                }

        if not best_candidate or best_candidate["result"].score < 0.9:
            continue

        candidate = best_candidate["candidate"]
        issue_id = f"cluster:add:{publication['id']}:{candidate.get('doc_id', 'unknown')}"
        issues.append(
            {
                "id": issue_id,
                "type": "under_clustered_profile_article",
                "title": publication["title"],
                "confidence": classify_confidence(best_candidate["result"].score),
                "score": round(best_candidate["result"].score, 3),
                "recommended_action": (
                    "Open the matching Add Articles candidate and your existing profile paper, "
                    "attach the candidate if needed, then merge the resulting Scholar entries."
                ),
                "manual_queries": [candidate.get("search_query", ""), f"\"{publication['title']}\""],
                "evidence": {
                    "left": {
                        "id": publication["id"],
                        "title": publication["title"],
                        "citations": publication["num_citations"],
                        "year": publication["year"],
                    },
                    "add_articles_candidate": {
                        "title": candidate.get("title", ""),
                        "title_url": candidate.get("title_url", ""),
                        "authors_venue": candidate.get("authors_venue", ""),
                        "doc_id": candidate.get("doc_id", ""),
                        "search_query": candidate.get("search_query", ""),
                        "captured_url": candidate.get("captured_url", ""),
                        "artifact_file": candidate.get("artifact_file", ""),
                    },
                    "shared_clusters": [],
                    "reasons": best_candidate["result"].reasons,
                },
            }
        )
    return issues


def detect_metadata_anomalies(publications: list[dict], versions_by_publication: dict[str, list[dict]], expected_papers: list[dict]) -> list[dict]:
    issues = []
    expected_lookup = expected_papers
    for publication in publications:
        versions = versions_by_publication.get(publication["id"], [])
        if not versions:
            continue

        observed_years = set()
        observed_venues = set()
        divergent_titles = []
        for version in versions:
            if version["pub_url"] in {"__empty__", "__error__"}:
                continue
            source = version["source_json"]
            bib = source.get("bib", {})
            version_title = bib.get("title", "")
            version_year = bib.get("pub_year", "")
            version_venue = bib.get("conference") or bib.get("journal") or bib.get("citation") or bib.get("venue", "")
            if version_year:
                observed_years.add(str(version_year))
            if version_venue:
                observed_venues.add(version_venue)
            if version_title and title_similarity(publication["title"], version_title) < 0.5:
                divergent_titles.append(version_title)

        matched_expected = None
        for expected in expected_lookup:
            match_result = score_expected_to_publication(expected, publication)
            if matched_expected is None or match_result.score > matched_expected[0].score:
                matched_expected = (match_result, expected)

        reasons = []
        score = 0.0
        if len(observed_years) >= 2:
            reasons.append(f"conflicting years in versions: {sorted(observed_years)}")
            score += 0.5
        if len(observed_venues) >= 2:
            reasons.append("conflicting venues across versions")
            score += 0.35
        if divergent_titles:
            reasons.append(f"{len(divergent_titles)} divergent version titles")
            score += 0.35
        if matched_expected:
            match_result, expected = matched_expected
            if match_result.score >= 0.85:
                expected_year = str(expected.get("year", "")).strip()
                if expected_year and observed_years and expected_year not in observed_years:
                    reasons.append(f"local bibliography year differs: {expected_year}")
                    score += 0.25
                expected_venue = expected.get("venue", "").strip()
                if expected_venue and observed_venues and expected_venue not in observed_venues:
                    reasons.append("local bibliography venue differs")
                    score += 0.2

        if score < 0.45:
            continue

        issues.append(
            {
                "id": f"metadata:{publication['id']}",
                "type": "metadata_anomaly",
                "title": publication["title"],
                "confidence": classify_confidence(score),
                "score": round(score, 3),
                "recommended_action": "Inspect the Scholar cluster and choose the canonical entry with the correct year/venue metadata.",
                "manual_queries": [f"\"{publication['title']}\""],
                "evidence": {
                    "publication_id": publication["id"],
                    "publication_title": publication["title"],
                    "observed_years": sorted(observed_years),
                    "observed_venues": sorted(observed_venues),
                    "divergent_titles": divergent_titles[:10],
                    "reasons": reasons,
                },
            }
        )
    return issues


def issue_type_counts(issues: list[dict]) -> dict[str, int]:
    issue_types = sorted({issue["type"] for issue in issues})
    return {
        issue_type: sum(1 for issue in issues if issue["type"] == issue_type)
        for issue_type in issue_types
    }


def load_dismissals(path: Path = DISMISSALS_JSON_FILE) -> set[str]:
    if not path.exists():
        return set()
    payload = json.loads(path.read_text())
    if isinstance(payload, dict):
        values = payload.get("dismissed_issue_ids", [])
    else:
        values = payload
    return {str(value) for value in values}


def write_issue_artifacts(issues: list[dict], generated_at: str | None = None) -> dict:
    generated_at = generated_at or datetime.now().isoformat()
    dismissals = load_dismissals()
    for issue in issues:
        issue["status"] = "dismissed" if issue["id"] in dismissals else "open"

    ISSUES_JSON_FILE.write_text(json.dumps(issues, indent=2, sort_keys=True))

    with ISSUES_CSV_FILE.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "id",
                "type",
                "title",
                "confidence",
                "score",
                "status",
                "recommended_action",
                "manual_queries",
            ],
        )
        writer.writeheader()
        for issue in issues:
            writer.writerow(
                {
                    "id": issue["id"],
                    "type": issue["type"],
                    "title": issue["title"],
                    "confidence": issue["confidence"],
                    "score": issue["score"],
                    "status": issue["status"],
                    "recommended_action": issue["recommended_action"],
                    "manual_queries": " | ".join(issue.get("manual_queries", [])),
                }
            )

    state = {
        "generated_at": generated_at,
        "issue_count": len(issues),
        "issue_ids": [issue["id"] for issue in issues],
        "type_counts": issue_type_counts(issues),
    }
    STATE_JSON_FILE.write_text(json.dumps(state, indent=2, sort_keys=True))
    return state
