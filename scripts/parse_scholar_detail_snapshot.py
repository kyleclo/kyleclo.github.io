# /// script
# requires-python = ">=3.11"
# ///
"""Parse a saved Google Scholar detail-page HTML snapshot into structured JSON."""

from __future__ import annotations

import argparse
import json
import re
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin

SCHOLAR_BASE = "https://scholar.google.com"


def normalize_space(text: str) -> str:
    return " ".join(unescape(text or "").replace("\xa0", " ").split())


def attr_map(attrs) -> dict[str, str]:
    return {key: value for key, value in attrs}


def extract_total_citation_summary(html: str) -> str:
    match = re.search(
        r'Total citations</div><div class="gsc_oci_value"><div[^>]*><a[^>]*>(.*?)</a>',
        html,
        re.DOTALL,
    )
    return normalize_space(match.group(1)) if match else ""


def extract_merged_scholar_articles(html: str) -> list[dict]:
    pattern = re.compile(
        r'<div class="gsc_oci_merged_snippet">'
        r'<div><a href="(?P<title_href>[^"]+)">(?P<title>.*?)</a>(?:<span class="gsc_oms_mm">\*</span>)?</div>'
        r'<div>(?P<summary>.*?)</div>'
        r'<div>(?P<links>.*?)</div>'
        r'</div>',
        re.DOTALL,
    )
    link_pattern = re.compile(r'<a class="gsc_oms_link" href="(?P<href>[^"]+)">(?P<label>.*?)</a>', re.DOTALL)

    articles = []
    for match in pattern.finditer(html):
        links = []
        for link_match in link_pattern.finditer(match.group("links")):
            links.append(
                {
                    "label": normalize_space(link_match.group("label")),
                    "url": urljoin(SCHOLAR_BASE, unescape(link_match.group("href"))),
                }
            )
        articles.append(
            {
                "title": normalize_space(match.group("title")),
                "title_url": urljoin(SCHOLAR_BASE, unescape(match.group("title_href"))),
                "summary": normalize_space(match.group("summary")),
                "links": links,
            }
        )
    return articles


class ScholarDetailParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.data: dict = {
            "title": "",
            "title_url": "",
            "pdf_url": "",
            "fields": {},
            "citation_summary": "",
            "merged_scholar_articles": [],
        }
        self._capture_title = False
        self._capture_pdf = False
        self._capture_field = False
        self._capture_value = False
        self._current_field = ""
        self._buffer: list[str] = []
        self._current_value_depth = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        attrs_d = attr_map(attrs)
        class_attr = attrs_d.get("class", "")
        elem_id = attrs_d.get("id", "")

        if elem_id == "gsc_oci_title" and tag == "div":
            self._capture_title = False
        if tag == "a" and class_attr == "gsc_oci_title_link":
            self._capture_title = True
            self.data["title_url"] = attrs_d.get("href", "")
            self._buffer = []
        elif tag == "a" and "gsc_vcd_title_ggt" not in class_attr and self._capture_pdf is False and attrs_d.get("href", "").endswith(".pdf"):
            # best-effort PDF link capture from title wrapper
            self.data["pdf_url"] = attrs_d.get("href", "")
        elif tag == "div" and class_attr == "gsc_oci_field":
            self._capture_field = True
            self._buffer = []
        elif tag == "div" and class_attr == "gsc_oci_value":
            self._capture_value = True
            self._buffer = []
            self._current_value_depth = 1
        elif self._capture_value and tag == "div":
            self._current_value_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if self._capture_title and tag == "a":
            self.data["title"] = normalize_space("".join(self._buffer))
            self._capture_title = False
        elif self._capture_field and tag == "div":
            self._current_field = normalize_space("".join(self._buffer))
            self._capture_field = False
        elif self._capture_value and tag == "div":
            self._current_value_depth -= 1
            if self._current_value_depth == 0:
                value = normalize_space("".join(self._buffer))
                if self._current_field and value:
                    self.data["fields"][self._current_field] = value
                self._capture_value = False

    def handle_data(self, data: str) -> None:
        if any(
            [
                self._capture_title,
                self._capture_field,
                self._capture_value,
            ]
        ):
            self._buffer.append(data)


def parse_snapshot(html_path: Path) -> dict:
    html = html_path.read_text()
    parser = ScholarDetailParser()
    parser.feed(html)
    payload = {
        "snapshot_file": str(html_path),
        **parser.data,
    }
    payload["citation_summary"] = extract_total_citation_summary(html)
    payload["merged_scholar_articles"] = extract_merged_scholar_articles(html)
    return payload


def default_output_path(html_path: Path) -> Path:
    return html_path.with_name(f"{html_path.stem}_parsed.json")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("html_path", type=Path, help="Path to a saved Scholar detail HTML snapshot")
    parser.add_argument("--output", type=Path, help="Optional output JSON path")
    args = parser.parse_args()

    payload = parse_snapshot(args.html_path)
    output_path = args.output or default_output_path(args.html_path)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True))
    print(f"Saved parsed detail JSON: {output_path}")
    print(f"Merged Scholar articles parsed: {len(payload['merged_scholar_articles'])}")


if __name__ == "__main__":
    main()
