# /// script
# requires-python = ">=3.11"
# ///
"""Parse a saved Google Scholar Add Articles HTML snapshot into structured JSON."""

from __future__ import annotations

import argparse
import json
import re
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, unquote, urljoin

SCHOLAR_BASE = "https://scholar.google.com"


def normalize_space(text: str) -> str:
    return " ".join(unescape(text or "").replace("\xa0", " ").split())


def attr_map(attrs) -> dict[str, str]:
    return {key: value for key, value in attrs}


def extract_capture_url(html_path: Path) -> str:
    metadata_path = html_path.with_name(f"{html_path.stem}_capture.json")
    if not metadata_path.exists():
        return ""
    try:
        payload = json.loads(metadata_path.read_text())
    except json.JSONDecodeError:
        return ""
    return payload.get("captured_url", "")


def extract_search_query(html: str, captured_url: str) -> str:
    match = re.search(r'<input type="text"[^>]*id="gsc_iads_tsi"[^>]*value="([^"]*)"', html)
    if match:
        return normalize_space(match.group(1))
    if "#d=gsc_md_iad" not in captured_url:
        return ""
    fragment = captured_url.split("#", 1)[1]
    params = parse_qs(fragment)
    nested = unquote(params.get("u", [""])[0])
    nested_params = parse_qs(nested.split("?", 1)[1] if "?" in nested else "")
    return normalize_space(nested_params.get("imq", [""])[0])


def extract_result_stats(html: str) -> dict[str, str]:
    match = re.search(
        r'<div id="gsc_iadb_data"[^>]*data-prev="([^"]*)"[^>]*data-next="([^"]*)"[^>]*data-start="([^"]*)"[^>]*data-end="([^"]*)"[^>]*data-max="([^"]*)"[^>]*data-num="([^"]*)"',
        html,
        re.DOTALL,
    )
    if not match:
        return {}
    prev_url, next_url, start, end, max_results, page_result_count = match.groups()
    return {
        "start": start,
        "end": end,
        "max_results": max_results,
        "page_result_count": page_result_count,
        "has_prev": str(bool(prev_url)).lower(),
        "has_next": str(bool(next_url)).lower(),
        "next_url": urljoin(SCHOLAR_BASE, unescape(next_url)) if next_url else "",
        "prev_url": urljoin(SCHOLAR_BASE, unescape(prev_url)) if prev_url else "",
    }


class AddArticlesParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.dialog_title = ""
        self.rows: list[dict] = []

        self._in_dialog_title = False
        self._capture: list[str] = []

        self._current_row: dict | None = None
        self._row_depth = 0
        self._row_rank = 0

        self._capture_title = False
        self._capture_meta = False
        self._capture_status = False

    def handle_starttag(self, tag: str, attrs) -> None:
        attrs_d = attr_map(attrs)
        class_attr = attrs_d.get("class", "")
        elem_id = attrs_d.get("id", "")

        if tag == "span" and elem_id == "gsc_iad_tart":
            self._in_dialog_title = True
            self._capture = []
            return

        if self._current_row is None and tag == "div" and "gsc_iadb_art" in class_attr.split():
            self._row_rank += 1
            self._current_row = {
                "result_rank": self._row_rank,
                "title": "",
                "title_url": "",
                "authors_venue": "",
                "status_label": "",
                "doc_id": "",
                "checkbox_id": "",
                "disabled": False,
                "in_profile": False,
                "raw_classes": normalize_space(class_attr),
            }
            self._row_depth = 1
            return

        if self._current_row is not None:
            if tag == "div":
                self._row_depth += 1
            if tag == "a" and self._current_row["title"] == "" and attrs_d.get("href", ""):
                href = attrs_d.get("href", "")
                if href.startswith("/scholar?oi=bibs"):
                    self._current_row["title_url"] = urljoin(SCHOLAR_BASE, href)
                    self._capture_title = True
                    self._capture = []
            elif tag == "div" and class_attr == "gs_gray" and self._current_row["authors_venue"] == "":
                self._capture_meta = True
                self._capture = []
            elif tag == "div" and class_attr == "gsc_iadb_art_added":
                self._capture_status = True
                self._capture = []
            elif tag == "input" and attrs_d.get("name") == "d":
                self._current_row["doc_id"] = attrs_d.get("value", "")
                self._current_row["checkbox_id"] = attrs_d.get("id", "")
                self._current_row["disabled"] = "disabled" in attrs_d

    def handle_endtag(self, tag: str) -> None:
        if self._in_dialog_title and tag == "span":
            self.dialog_title = normalize_space("".join(self._capture))
            self._in_dialog_title = False
            return

        if self._current_row is not None:
            if self._capture_title and tag == "a":
                self._current_row["title"] = normalize_space("".join(self._capture))
                self._capture_title = False
            elif self._capture_meta and tag == "div":
                self._current_row["authors_venue"] = normalize_space("".join(self._capture))
                self._capture_meta = False
            elif self._capture_status and tag == "div":
                status = normalize_space("".join(self._capture))
                self._current_row["status_label"] = status
                self._current_row["in_profile"] = status.lower() == "in profile"
                self._capture_status = False

            if tag == "div":
                self._row_depth -= 1
                if self._row_depth == 0:
                    self.rows.append(self._current_row)
                    self._current_row = None

    def handle_data(self, data: str) -> None:
        if self._in_dialog_title or self._capture_title or self._capture_meta or self._capture_status:
            self._capture.append(data)


def parse_snapshot(html_path: Path) -> dict:
    html = html_path.read_text()
    captured_url = extract_capture_url(html_path)
    parser = AddArticlesParser()
    parser.feed(html)
    return {
        "snapshot_file": str(html_path),
        "captured_url": captured_url,
        "dialog_title": parser.dialog_title,
        "search_query": extract_search_query(html, captured_url),
        "result_stats": extract_result_stats(html),
        "rows": parser.rows,
        "row_count": len(parser.rows),
    }


def default_output_path(html_path: Path) -> Path:
    return html_path.with_name(f"{html_path.stem}_add_articles.json")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("html_path", type=Path, help="Path to a saved Scholar Add Articles HTML snapshot")
    parser.add_argument("--output", type=Path, help="Optional output JSON path")
    args = parser.parse_args()

    payload = parse_snapshot(args.html_path)
    output_path = args.output or default_output_path(args.html_path)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True))
    print(f"Saved parsed Add Articles JSON: {output_path}")
    print(f"Candidate rows parsed: {payload['row_count']}")


if __name__ == "__main__":
    main()
