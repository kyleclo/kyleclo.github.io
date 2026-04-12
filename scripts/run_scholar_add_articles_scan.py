# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "playwright",
# ]
# ///
"""Run a bounded Add Articles scan from a small curated query file."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.investigate_scholar_ui import default_artifact_dir, run


def load_queries(path: Path) -> list[str]:
    queries = []
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        queries.append(line)
    return queries


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query_file", type=Path, help="Text file with one curated Add Articles query per line")
    parser.add_argument("--cdp-url", default="http://127.0.0.1:9222")
    parser.add_argument("--artifact-dir", type=Path, default=default_artifact_dir())
    parser.add_argument("--capture-add-articles-pages", type=int, default=3)
    parser.add_argument("--between-pages-seconds", type=int, default=8)
    parser.add_argument("--between-queries-seconds", type=int, default=12)
    parser.add_argument("--wait-seconds", type=int, default=45)
    parser.add_argument("--trace-navigation", action="store_true")
    args = parser.parse_args()

    queries = load_queries(args.query_file)
    if not queries:
        parser.error("query file did not contain any usable queries")
    if len(queries) > 3:
        parser.error("query file must contain at most 3 queries during investigation")
    if args.capture_add_articles_pages < 1:
        parser.error("--capture-add-articles-pages must be at least 1")
    if args.capture_add_articles_pages > 3:
        parser.error("--capture-add-articles-pages must not exceed 3 during investigation")

    asyncio.run(
        run(
            query=None,
            add_articles_queries=queries,
            capture_profile=False,
            detail_url=None,
            capture_detail=False,
            capture_current_page=True,
            wait_for_add_articles=True,
            trace_navigation=args.trace_navigation,
            wait_for_enter=False,
            wait_seconds=args.wait_seconds,
            artifact_dir=args.artifact_dir,
            cdp_url=args.cdp_url,
            use_existing_page=True,
            parse_add_articles=True,
            capture_add_articles_pages=args.capture_add_articles_pages,
            between_pages_seconds=args.between_pages_seconds,
            between_queries_seconds=args.between_queries_seconds,
        )
    )


if __name__ == "__main__":
    main()
