from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher

_STOPWORDS = {"a", "an", "and", "for", "of", "on", "the", "to", "with"}


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def normalize_title(title: str) -> str:
    return normalize_text(title)


def tokenize_title(title: str) -> set[str]:
    return {tok for tok in normalize_title(title).split() if tok and tok not in _STOPWORDS}


def title_similarity(left: str, right: str) -> float:
    return SequenceMatcher(None, normalize_title(left), normalize_title(right)).ratio()


def token_jaccard(left: str, right: str) -> float:
    left_tokens = tokenize_title(left)
    right_tokens = tokenize_title(right)
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def normalize_author_list(author_text: str) -> list[str]:
    if not author_text:
        return []
    parts = re.split(r"\s+and\s+|,\s*", author_text)
    authors = []
    for part in parts:
        norm = normalize_text(part)
        if norm:
            authors.append(norm)
    return authors


def author_last_names(author_text: str) -> set[str]:
    last_names = set()
    for author in normalize_author_list(author_text):
        pieces = author.split()
        if pieces:
            last_names.add(pieces[-1])
    return last_names


def author_overlap_score(left: str, right: str) -> float:
    left_names = author_last_names(left)
    right_names = author_last_names(right)
    if not left_names or not right_names:
        return 0.0
    return len(left_names & right_names) / len(left_names | right_names)


def safe_int(value) -> int | None:
    if value in (None, "", []):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def compact_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()

