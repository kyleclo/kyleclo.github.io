from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from scripts.investigate_scholar_ui import default_artifact_dir
from scripts.parse_scholar_add_articles_snapshot import normalize_space

MERGE_QUEUE_STATUSES = {
    "discovered",
    "reviewed",
    "approved",
    "skipped",
    "merged",
    "failed",
    "needs_manual_choice",
    "needs_manual_repair",
    "stale",
}

STOPWORDS = {
    "a",
    "an",
    "and",
    "for",
    "in",
    "of",
    "on",
    "the",
    "to",
}

DIGIT_WORDS = {
    "0": "zero",
    "1": "one",
    "2": "two",
    "3": "three",
    "4": "four",
    "5": "five",
    "6": "six",
    "7": "seven",
    "8": "eight",
    "9": "nine",
}

ORDINAL_TOKENS = {
    "first",
    "second",
    "third",
    "fourth",
    "fifth",
    "sixth",
    "seventh",
    "eighth",
    "ninth",
    "tenth",
}


def default_merge_queue_path() -> Path:
    return default_artifact_dir() / "merge_queue.json"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_citations(text: str) -> int:
    match = re.search(r"\d+", text or "")
    return int(match.group(0)) if match else 0


def normalize_family_text(text: str) -> str:
    text = normalize_space(text).casefold()
    for digit, word in DIGIT_WORDS.items():
        text = re.sub(rf"\b{re.escape(digit)}\b", word, text)
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def family_tokens(title: str) -> set[str]:
    tokens = []
    for token in normalize_family_text(title).split():
        if len(token) <= 1:
            continue
        if token in STOPWORDS:
            continue
        if re.fullmatch(r"(19|20)\d{2}", token):
            continue
        tokens.append(token)
    return set(tokens)


def ordered_family_tokens(title: str) -> list[str]:
    tokens = []
    for token in normalize_family_text(title).split():
        if len(token) <= 1:
            continue
        if token in STOPWORDS:
            continue
        if re.fullmatch(r"(19|20)\d{2}", token):
            continue
        tokens.append(token)
    return tokens


def ordinal_tokens(title: str) -> set[str]:
    return {token for token in ordered_family_tokens(title) if token in ORDINAL_TOKENS}


def titles_pass_family_heuristics(left_title: str, right_title: str) -> bool:
    left_ordinals = ordinal_tokens(left_title)
    right_ordinals = ordinal_tokens(right_title)
    if left_ordinals and right_ordinals and left_ordinals != right_ordinals:
        return False
    left_normalized = normalize_family_text(left_title)
    right_normalized = normalize_family_text(right_title)
    if ":" in left_title and ":" in right_title:
        left_prefix, left_suffix = [normalize_family_text(part) for part in left_title.split(":", 1)]
        right_prefix, right_suffix = [normalize_family_text(part) for part in right_title.split(":", 1)]
        if left_prefix == right_prefix and left_suffix and right_suffix:
            suffix_similarity = family_similarity(left_suffix, right_suffix)
            suffix_jaccard = family_jaccard_similarity(left_suffix, right_suffix)
            if suffix_similarity < 0.74 or suffix_jaccard < 0.74:
                return False
    if left_normalized.startswith(right_normalized) or right_normalized.startswith(left_normalized):
        shorter, longer = sorted([left_normalized, right_normalized], key=len)
        extra_tokens = [token for token in longer.split() if token not in shorter.split()]
        if len(extra_tokens) >= 4:
            return False
    return True


def family_similarity(left_title: str, right_title: str) -> float:
    left_tokens = family_tokens(left_title)
    right_tokens = family_tokens(right_title)
    if not left_tokens or not right_tokens:
        return 0.0
    overlap = len(left_tokens & right_tokens)
    return overlap / min(len(left_tokens), len(right_tokens))


def family_jaccard_similarity(left_title: str, right_title: str) -> float:
    left_tokens = family_tokens(left_title)
    right_tokens = family_tokens(right_title)
    if not left_tokens or not right_tokens:
        return 0.0
    overlap = len(left_tokens & right_tokens)
    union = len(left_tokens | right_tokens)
    return overlap / union if union else 0.0


def discover_merge_families(rows: list[dict], *, min_similarity: float = 0.74) -> list[list[dict]]:
    rows = [row for row in rows if row.get("row_id") and row.get("title")]
    neighbors: dict[str, set[str]] = {row["row_id"]: set() for row in rows}
    rows_by_id = {row["row_id"]: row for row in rows}

    for index, left in enumerate(rows):
        for right in rows[index + 1 :]:
            if not titles_pass_family_heuristics(left.get("title", ""), right.get("title", "")):
                continue
            score = family_similarity(left.get("title", ""), right.get("title", ""))
            if score < min_similarity:
                continue
            neighbors[left["row_id"]].add(right["row_id"])
            neighbors[right["row_id"]].add(left["row_id"])

    families = []
    visited = set()
    for row in rows:
        row_id = row["row_id"]
        if row_id in visited or not neighbors[row_id]:
            continue
        stack = [row_id]
        component = []
        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            component.append(rows_by_id[current])
            stack.extend(sorted(neighbors[current] - visited))
        families.append(sorted(component, key=lambda item: (-parse_citations(item.get("citations", "")), item.get("title", "").lower())))

    families.sort(key=lambda family: (-parse_citations(family[0].get("citations", "")), family[0].get("title", "").lower()))
    return families


def family_slug(title: str) -> str:
    slug = normalize_family_text(title).replace(" ", "-")
    return slug[:48] or "family"


def queue_item_id(targets: list[dict]) -> str:
    sorted_ids = sorted(target["row_id"] for target in targets)
    digest = hashlib.md5("|".join(sorted_ids).encode("utf-8")).hexdigest()[:10]
    return f"merge:{family_slug(targets[0]['title'])}:{digest}"


def build_discovered_queue_items(
    rows: list[dict],
    *,
    source: dict | None = None,
    min_similarity: float = 0.74,
) -> list[dict]:
    items = []
    for family in discover_merge_families(rows, min_similarity=min_similarity):
        items.append(
            {
                "id": queue_item_id(family),
                "status": "discovered",
                "family_label": family[0]["title"],
                "targets": [
                    {
                        "row_id": row["row_id"],
                        "title": row.get("title", ""),
                        "citations": row.get("citations", ""),
                        "year": row.get("year", ""),
                    }
                    for row in family
                ],
                "discovery_source": source or {},
                "review_notes": "",
                "approved_by_operator": False,
                "execution_attempts": 0,
                "result": None,
                "discovered_at": utc_now_iso(),
            }
        )
    return items


def load_merge_queue(path: Path) -> dict:
    if not path.exists():
        return {"generated_at": None, "items": []}
    return json.loads(path.read_text())


def target_row_ids(item: dict) -> set[str]:
    return {target.get("row_id", "") for target in item.get("targets", []) if target.get("row_id")}


def queue_items_refer_to_same_family(existing: dict, discovered: dict) -> bool:
    existing_label = normalize_family_text(existing.get("family_label", ""))
    discovered_label = normalize_family_text(discovered.get("family_label", ""))
    if existing_label != discovered_label:
        return False
    overlap = target_row_ids(existing) & target_row_ids(discovered)
    return bool(overlap)


def find_matching_existing_item(existing_items: list[dict], discovered_item: dict) -> dict | None:
    exact = next((item for item in existing_items if item.get("id") == discovered_item.get("id")), None)
    if exact is not None:
        return exact
    for item in existing_items:
        if queue_items_refer_to_same_family(item, discovered_item):
            return item
    return None


def merge_discovered_items(existing_payload: dict, discovered_items: list[dict]) -> dict:
    existing_items = [dict(item) for item in existing_payload.get("items", [])]
    items_by_id = {item["id"]: item for item in existing_items}
    for item in discovered_items:
        existing = find_matching_existing_item(existing_items, item)
        if existing is None:
            items_by_id[item["id"]] = item
            existing_items.append(items_by_id[item["id"]])
            continue
        updated = dict(existing)
        old_id = updated["id"]
        updated["id"] = item["id"]
        updated["family_label"] = item["family_label"]
        updated["targets"] = item["targets"]
        updated["discovery_source"] = item["discovery_source"]
        updated["discovered_at"] = item["discovered_at"]
        if old_id != item["id"]:
            items_by_id.pop(old_id, None)
        items_by_id[item["id"]] = updated
        for index, existing_item in enumerate(existing_items):
            if existing_item.get("id") == old_id:
                existing_items[index] = updated
                break
    items = sorted(items_by_id.values(), key=lambda item: item.get("family_label", "").lower())
    return {"generated_at": utc_now_iso(), "items": items}


def save_merge_queue(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True))


def get_queue_item(payload: dict, item_id: str) -> dict:
    for item in payload.get("items", []):
        if item.get("id") == item_id:
            return item
    raise KeyError(f"Unknown merge queue item id: {item_id}")


def update_queue_item_status(
    payload: dict,
    *,
    item_id: str,
    status: str,
    note: str | None = None,
    approved_by_operator: bool | None = None,
) -> dict:
    if status not in MERGE_QUEUE_STATUSES:
        raise ValueError(f"Unsupported merge queue status: {status}")

    updated_payload = {"generated_at": utc_now_iso(), "items": [dict(item) for item in payload.get("items", [])]}
    item = get_queue_item(updated_payload, item_id)
    item["status"] = status
    if note is not None:
        item["review_notes"] = note
    if approved_by_operator is not None:
        item["approved_by_operator"] = approved_by_operator
    if status == "approved":
        item["approved_by_operator"] = True
        item["approved_at"] = utc_now_iso()
    elif status in {"skipped", "reviewed", "needs_manual_choice", "needs_manual_repair", "stale"}:
        item["approved_by_operator"] = bool(item.get("approved_by_operator", False) and status == "reviewed")
        if status != "reviewed":
            item.pop("approved_at", None)
    return updated_payload


def select_next_approved_item(payload: dict) -> dict:
    approved_items = [
        item
        for item in payload.get("items", [])
        if item.get("status") == "approved" and item.get("approved_by_operator")
    ]
    if not approved_items:
        raise RuntimeError("No approved merge queue items found.")
    approved_items.sort(key=lambda item: (item.get("approved_at", ""), item.get("family_label", "").lower()))
    return approved_items[0]


def select_approved_items(payload: dict, *, limit: int | None = None) -> list[dict]:
    approved_items = [
        item
        for item in payload.get("items", [])
        if item.get("status") == "approved" and item.get("approved_by_operator")
    ]
    approved_items.sort(key=lambda item: (item.get("approved_at", ""), item.get("family_label", "").lower()))
    if limit is not None:
        return approved_items[:limit]
    return approved_items


def update_queue_item_result(
    payload: dict,
    *,
    item_id: str,
    result: dict,
    status: str,
    increment_execution_attempts: bool,
) -> dict:
    if status not in MERGE_QUEUE_STATUSES:
        raise ValueError(f"Unsupported merge queue status: {status}")
    updated_payload = {"generated_at": utc_now_iso(), "items": [dict(item) for item in payload.get("items", [])]}
    item = get_queue_item(updated_payload, item_id)
    item["status"] = status
    item["result"] = result
    if increment_execution_attempts:
        item["execution_attempts"] = int(item.get("execution_attempts", 0)) + 1
    return updated_payload


def summarize_verification_output(output: str) -> dict:
    lines = [line.strip() for line in (output or "").splitlines() if line.strip()]
    return {
        "status": "verified_visible_rows" if lines else "verification_empty",
        "visible_line_count": len(lines),
        "visible_rows_text": output or "",
    }


def update_queue_item_verification(
    payload: dict,
    *,
    item_id: str,
    verification: dict,
) -> dict:
    updated_payload = {"generated_at": utc_now_iso(), "items": [dict(item) for item in payload.get("items", [])]}
    item = get_queue_item(updated_payload, item_id)
    existing_result = dict(item.get("result") or {})
    existing_result["verification"] = verification
    item["result"] = existing_result
    return updated_payload


def format_merge_queue_item(item: dict) -> str:
    lines = [
        f"ID: {item.get('id', '')}",
        f"Status: {item.get('status', '')}",
        f"Family: {item.get('family_label', '')}",
        f"Targets: {len(item.get('targets', []))}",
    ]
    if item.get("review_notes"):
        lines.append(f"Review Notes: {item.get('review_notes', '')}")
    if item.get("approved_at"):
        lines.append(f"Approved At: {item.get('approved_at', '')}")
    source = item.get("discovery_source", {})
    if source:
        lines.append(
            "Discovery: "
            f"url={source.get('captured_url', '')}, "
            f"rows={source.get('row_count', '')}, "
            f"show_more={source.get('expanded_show_more_steps', '')}"
        )
    if item.get("result") is not None:
        lines.append(f"Result: {json.dumps(item.get('result', {}), sort_keys=True)}")
    for index, target in enumerate(item.get("targets", []), start=1):
        lines.append(
            f"{index}. {target.get('title', '')} "
            f"(row_id={target.get('row_id', '')}, citations={target.get('citations', '')}, year={target.get('year', '')})"
        )
    return "\n".join(lines)


def format_merge_queue(items: list[dict], *, status: str | None = None, limit: int = 20) -> str:
    if status:
        items = [item for item in items if item.get("status") == status]
    if not items:
        return "No merge queue items found."

    lines = []
    for index, item in enumerate(items[:limit], start=1):
        lines.append(
            f"{index}. {item.get('family_label', '')} "
            f"(status={item.get('status', '')}, targets={len(item.get('targets', []))})"
        )
        for target in item.get("targets", []):
            lines.append(
                f"   - {target.get('title', '')} "
                f"(row_id={target.get('row_id', '')}, citations={target.get('citations', '')}, year={target.get('year', '')})"
            )
    return "\n".join(lines)


def classify_family_type(item: dict) -> str:
    target_count = len(item.get("targets", []))
    return "pair" if target_count == 2 else "multi"


def classify_queue_confidence(item: dict) -> str:
    targets = item.get("targets", [])
    if len(targets) < 2:
        return "low"
    left = targets[0].get("title", "")
    right = targets[1].get("title", "")
    similarity = family_similarity(left, right)
    if similarity >= 0.95:
        return "high"
    if similarity >= 0.82:
        return "medium"
    return "low"


def queue_item_matches_filters(
    item: dict,
    *,
    status: str | None = None,
    family_type: str | None = None,
    confidence: str | None = None,
    contains: str | None = None,
    exclude_contains: str | None = None,
) -> bool:
    if status and item.get("status") != status:
        return False
    if family_type and classify_family_type(item) != family_type:
        return False
    if confidence and classify_queue_confidence(item) != confidence:
        return False
    haystack = " ".join(
        [item.get("family_label", "")]
        + [target.get("title", "") for target in item.get("targets", [])]
    ).casefold()
    if contains and contains.casefold() not in haystack:
        return False
    if exclude_contains and exclude_contains.casefold() in haystack:
        return False
    return True


def select_queue_items(
    payload: dict,
    *,
    status: str | None = None,
    family_type: str | None = None,
    confidence: str | None = None,
    contains: str | None = None,
    exclude_contains: str | None = None,
    limit: int | None = None,
) -> list[dict]:
    items = [
        item
        for item in payload.get("items", [])
        if queue_item_matches_filters(
            item,
            status=status,
            family_type=family_type,
            confidence=confidence,
            contains=contains,
            exclude_contains=exclude_contains,
        )
    ]
    items.sort(key=lambda item: item.get("family_label", "").lower())
    if limit is not None:
        return items[:limit]
    return items


def format_merge_queue_triage(items: list[dict], *, status: str | None = None, limit: int = 20) -> str:
    if status:
        items = [item for item in items if item.get("status") == status]
    if not items:
        return "No merge queue items found."

    lines = []
    for index, item in enumerate(items[:limit], start=1):
        targets = item.get("targets", [])
        top_titles = " | ".join(target.get("title", "") for target in targets[:2])
        lines.append(
            f"{index}. {item.get('family_label', '')} "
            f"[status={item.get('status', '')}, type={classify_family_type(item)}, confidence={classify_queue_confidence(item)}, targets={len(targets)}]"
        )
        if top_titles:
            lines.append(f"   Top: {top_titles}")
    return "\n".join(lines)
