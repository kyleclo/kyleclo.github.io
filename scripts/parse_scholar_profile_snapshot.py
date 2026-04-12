# /// script
# requires-python = ">=3.11"
# ///
"""Parse a saved Google Scholar profile HTML snapshot into structured JSON."""

from __future__ import annotations

import argparse
import json
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin

SCHOLAR_BASE = "https://scholar.google.com"


def normalize_space(text: str) -> str:
    return " ".join(unescape(text or "").replace("\xa0", " ").split())


def attr_map(attrs) -> dict[str, str]:
    return {key: value for key, value in attrs}


class ScholarProfileParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.profile: dict = {}
        self.rows: list[dict] = []

        self._in_name = False
        self._in_affiliation = False
        self._in_stats = False
        self._in_stat_label = False
        self._in_stat_value = False
        self._current_stat_label = ""
        self._current_stat_value = ""
        self._current_row: dict | None = None
        self._row_stack = 0
        self._current_link_field: str | None = None
        self._current_div_role: str | None = None
        self._capture_text: list[str] = []
        self._capture_authors = False
        self._capture_venue = False
        self._capture_citations = False
        self._capture_year = False
        self._profile_articles_label = ""

    def handle_starttag(self, tag: str, attrs) -> None:
        attrs_d = attr_map(attrs)
        class_attr = attrs_d.get("class", "")
        elem_id = attrs_d.get("id", "")

        if tag == "div" and elem_id == "gsc_prf_in":
            self._in_name = True
            self._capture_text = []
        elif tag == "div" and elem_id == "gsc_prf_i":
            self._in_affiliation = True
            self._capture_text = []
        elif tag == "table" and elem_id == "gsc_rsb_st":
            self._in_stats = True
        elif self._in_stats and tag == "td" and class_attr == "gsc_rsb_sth":
            self._in_stat_label = True
            self._capture_text = []
        elif self._in_stats and tag == "td" and class_attr == "gsc_rsb_std":
            self._in_stat_value = True
            self._capture_text = []
        elif tag == "span" and elem_id == "gsc_a_nn":
            self._capture_text = []
            self._current_link_field = "__articles_label__"
        elif tag == "tr" and "gsc_a_tr" in class_attr.split():
            self._current_row = {
                "title": "",
                "detail_url": "",
                "authors": "",
                "venue": "",
                "citations": "",
                "citations_url": "",
                "year": "",
            }
            self._row_stack = 1
        elif self._current_row is not None:
            if tag == "tr":
                self._row_stack += 1
            if tag == "a" and "gsc_a_at" in class_attr.split():
                self._current_link_field = "title"
                self._current_row["detail_url"] = urljoin(
                    SCHOLAR_BASE, attrs_d.get("href", "")
                )
                self._capture_text = []
            elif tag == "div" and class_attr == "gs_gray":
                if not self._current_row["authors"]:
                    self._capture_authors = True
                    self._capture_text = []
                elif not self._current_row["venue"]:
                    self._capture_venue = True
                    self._capture_text = []
            elif tag == "a" and "gsc_a_ac" in class_attr.split():
                self._capture_citations = True
                self._current_row["citations_url"] = attrs_d.get("href", "")
                self._capture_text = []
            elif tag == "span" and "gsc_a_h" in class_attr.split():
                self._capture_year = True
                self._capture_text = []

    def handle_endtag(self, tag: str) -> None:
        if self._in_name and tag == "div":
            self.profile["name"] = normalize_space("".join(self._capture_text))
            self._in_name = False
        elif self._in_affiliation and tag == "div":
            text = normalize_space("".join(self._capture_text))
            if text:
                self.profile["affiliation"] = text
            self._in_affiliation = False
        elif self._in_stat_label and tag == "td":
            self._current_stat_label = normalize_space("".join(self._capture_text))
            self._in_stat_label = False
        elif self._in_stat_value and tag == "td":
            self._current_stat_value = normalize_space("".join(self._capture_text))
            if self._current_stat_label:
                self.profile.setdefault("stats", {})[self._current_stat_label] = self._current_stat_value
            self._current_stat_label = ""
            self._current_stat_value = ""
            self._in_stat_value = False
        elif self._current_link_field == "__articles_label__" and tag == "span":
            self._profile_articles_label = normalize_space("".join(self._capture_text))
            self._current_link_field = None
        elif self._current_row is not None:
            if self._current_link_field == "title" and tag == "a":
                self._current_row["title"] = normalize_space("".join(self._capture_text))
                self._current_link_field = None
            elif self._capture_authors and tag == "div":
                self._current_row["authors"] = normalize_space("".join(self._capture_text))
                self._capture_authors = False
            elif self._capture_venue and tag == "div":
                self._current_row["venue"] = normalize_space("".join(self._capture_text))
                self._capture_venue = False
            elif self._capture_citations and tag == "a":
                self._current_row["citations"] = normalize_space("".join(self._capture_text))
                self._capture_citations = False
            elif self._capture_year and tag == "span":
                self._current_row["year"] = normalize_space("".join(self._capture_text))
                self._capture_year = False
            elif tag == "tr":
                self._row_stack -= 1
                if self._row_stack == 0:
                    self.rows.append(self._current_row)
                    self._current_row = None

    def handle_data(self, data: str) -> None:
        if any(
            [
                self._in_name,
                self._in_affiliation,
                self._in_stat_label,
                self._in_stat_value,
                self._current_link_field is not None,
                self._capture_authors,
                self._capture_venue,
                self._capture_citations,
                self._capture_year,
            ]
        ):
            self._capture_text.append(data)


def parse_snapshot(html_path: Path) -> dict:
    parser = ScholarProfileParser()
    parser.feed(html_path.read_text())
    return {
        "snapshot_file": str(html_path),
        "profile": {
            **parser.profile,
            "visible_articles_label": parser._profile_articles_label,
        },
        "visible_rows": parser.rows,
        "visible_row_count": len(parser.rows),
    }


def default_output_path(html_path: Path) -> Path:
    return html_path.with_name(f"{html_path.stem}_rows.json")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("html_path", type=Path, help="Path to a saved Scholar profile HTML snapshot")
    parser.add_argument("--output", type=Path, help="Optional output JSON path")
    args = parser.parse_args()

    payload = parse_snapshot(args.html_path)
    output_path = args.output or default_output_path(args.html_path)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True))
    print(f"Saved parsed snapshot JSON: {output_path}")
    print(f"Visible rows parsed: {payload['visible_row_count']}")


if __name__ == "__main__":
    main()
