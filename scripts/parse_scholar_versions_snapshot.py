# /// script
# requires-python = ">=3.11"
# ///
"""Parse a saved Google Scholar versions/results HTML snapshot into structured JSON."""

from __future__ import annotations

import argparse
import json
import re
from html import unescape
from pathlib import Path
from urllib.parse import urljoin

SCHOLAR_BASE = "https://scholar.google.com"


def normalize_space(text: str) -> str:
    return " ".join(unescape(text or "").replace("\xa0", " ").split())


def default_output_path(html_path: Path) -> Path:
    return html_path.with_name(f"{html_path.stem}_versions.json")


def extract_cluster_id(html: str) -> str:
    match = re.search(r"cluster=(\d+)", html)
    return match.group(1) if match else ""


def parse_versions_snapshot(html_path: Path) -> dict:
    html = html_path.read_text()
    cluster_id = extract_cluster_id(html)

    row_pattern = re.compile(
        r'<div class="gs_r gs_or gs_scl"(?P<attrs>[^>]*)>'
        r'.*?<h3 class="gs_rt"[^>]*>(?P<title_block>.*?)</h3>'
        r'<div class="gs_a">(?P<meta>.*?)</div>'
        r'(?:<div class="gs_rs">(?P<snippet>.*?)</div>)?'
        r'.*?<div class="gs_fl gs_flb">(?P<footer>.*?)</div>'
        r'.*?</div></div>',
        re.DOTALL,
    )
    link_pattern = re.compile(r'<a[^>]+href="(?P<href>[^"]+)"[^>]*>(?P<label>.*?)</a>', re.DOTALL)
    title_link_pattern = re.compile(r'<a[^>]+id="(?P<id>[^"]+)"[^>]+href="(?P<href>[^"]+)"[^>]*>(?P<title>.*?)</a>', re.DOTALL)
    data_rp_pattern = re.compile(r'data-rp="(?P<rp>\d+)"')
    data_did_pattern = re.compile(r'data-did="(?P<did>[^"]*)"')

    rows = []
    for row_match in row_pattern.finditer(html):
        attrs = row_match.group("attrs")
        title_block = row_match.group("title_block")
        meta = row_match.group("meta")
        snippet = row_match.group("snippet") or ""
        footer = row_match.group("footer")

        title_match = title_link_pattern.search(title_block)
        if not title_match:
            continue

        footer_links = []
        for link_match in link_pattern.finditer(footer):
            label = normalize_space(re.sub(r"<[^>]+>", " ", link_match.group("label")))
            if not label:
                continue
            footer_links.append(
                {
                    "label": label,
                    "url": urljoin(SCHOLAR_BASE, unescape(link_match.group("href"))),
                }
            )

        rows.append(
            {
                "result_id": title_match.group("id"),
                "result_rank": int(data_rp_pattern.search(attrs).group("rp")) if data_rp_pattern.search(attrs) else None,
                "data_did": data_did_pattern.search(attrs).group("did") if data_did_pattern.search(attrs) else "",
                "title": normalize_space(re.sub(r"<[^>]+>", " ", title_match.group("title"))),
                "title_url": urljoin(SCHOLAR_BASE, unescape(title_match.group("href"))),
                "meta": normalize_space(re.sub(r"<[^>]+>", " ", meta)),
                "snippet": normalize_space(re.sub(r"<[^>]+>", " ", snippet)),
                "footer_links": footer_links,
            }
        )

    return {
        "snapshot_file": str(html_path),
        "cluster_id": cluster_id,
        "result_count": len(rows),
        "results": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("html_path", type=Path, help="Path to a saved Scholar versions/results HTML snapshot")
    parser.add_argument("--output", type=Path, help="Optional output JSON path")
    args = parser.parse_args()

    payload = parse_versions_snapshot(args.html_path)
    output_path = args.output or default_output_path(args.html_path)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True))
    print(f"Saved parsed versions JSON: {output_path}")
    print(f"Results parsed: {payload['result_count']}")
    print(f"Cluster id: {payload['cluster_id'] or 'N/A'}")


if __name__ == "__main__":
    main()
