from __future__ import annotations

from pathlib import Path

from .config import PAPERS_BIB_FILE
from .utils import compact_whitespace


def _parse_bibtex_entries(text: str) -> list[tuple[str, dict]]:
    entries = []
    i = 0
    while True:
        at = text.find("@", i)
        if at == -1:
            break
        brace = text.find("{", at)
        if brace == -1:
            break
        comma = text.find(",", brace)
        if comma == -1:
            break
        entry_type = text[at + 1 : brace].strip().lower()
        key = text[brace + 1 : comma].strip()
        depth = 1
        j = comma + 1
        while j < len(text) and depth > 0:
            char = text[j]
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
            j += 1
        body = text[comma + 1 : j - 1]
        fields: dict[str, str] = {"ENTRYTYPE": entry_type, "ID": key}
        lines = body.splitlines()
        current_key = None
        current_value = []
        for raw_line in lines:
            line = raw_line.strip()
            if not line:
                continue
            if current_key is None and "=" in line:
                field, value = line.split("=", 1)
                current_key = field.strip().lower()
                current_value = [value.strip()]
            elif current_key is not None:
                current_value.append(line)
            if current_key is not None and line.endswith(","):
                value = " ".join(current_value).rstrip(",").strip()
                value = value.strip("{}").strip('"')
                fields[current_key] = compact_whitespace(value)
                current_key = None
                current_value = []
        if current_key is not None:
            value = " ".join(current_value).strip().strip("{}").strip('"')
            fields[current_key] = compact_whitespace(value)
        entries.append((key, fields))
        i = j
    return entries


def load_expected_papers(bib_file: Path = PAPERS_BIB_FILE) -> list[dict]:
    if not bib_file.exists():
        return []
    text = bib_file.read_text()
    expected = []
    for key, fields in _parse_bibtex_entries(text):
        title = fields.get("title", "")
        if not title:
            continue
        expected.append(
            {
                "id": key,
                "title": title,
                "author": fields.get("author", ""),
                "year": fields.get("year", ""),
                "venue": fields.get("journal") or fields.get("booktitle", ""),
                "doi": fields.get("doi", ""),
                "arxiv": fields.get("arxiv", ""),
                "url": fields.get("url", ""),
                "source": "papers.bib",
            }
        )
    return expected

