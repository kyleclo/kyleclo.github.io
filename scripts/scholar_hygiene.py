# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "scholarly",
#     "tqdm",
# ]
# ///
"""CLI entrypoint for the Google Scholar hygiene workflow."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.scholar_hygiene.workflow import collect_issues, review_issues, run_refresh, verify_issues
from scripts.scholar_hygiene.ui_artifacts import (
    format_add_articles_candidates,
    load_add_articles_candidates,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    refresh = subparsers.add_parser("refresh", help="Refresh Scholar profile and cached evidence")
    refresh.add_argument("--skip-profile", action="store_true", help="Do not refresh your own Scholar profile")
    refresh.add_argument("--coauthors", action="store_true", help="Refresh cached coauthor profiles")

    subparsers.add_parser("detect", help="Detect Scholar hygiene issues and write JSON/CSV artifacts")

    review = subparsers.add_parser("review", help="Print a ranked review queue")
    review.add_argument("--type", choices=[
        "missing_profile_article",
        "under_clustered_profile_article",
        "metadata_anomaly",
    ])
    review.add_argument("--limit", type=int, default=20)

    evidence = subparsers.add_parser("evidence", help="Inspect structured Scholar UI evidence")
    evidence_subparsers = evidence.add_subparsers(dest="evidence_command", required=True)
    add_articles = evidence_subparsers.add_parser(
        "add-articles",
        help="List newest known Add Articles candidate evidence",
    )
    add_articles.add_argument(
        "--status",
        choices=["all", "in-profile", "not-in-profile"],
        default="all",
    )
    add_articles.add_argument("--limit", type=int, default=20)

    subparsers.add_parser("verify", help="Re-run detection and compare with the previous issue snapshot")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "refresh":
        summary = run_refresh(
            refresh_profile_data=not args.skip_profile,
            refresh_coauthors_data=args.coauthors,
        )
        print(json.dumps(summary, indent=2, sort_keys=True))
        return

    if args.command == "detect":
        issues = collect_issues()
        print(json.dumps({"issue_count": len(issues)}, indent=2, sort_keys=True))
        return

    if args.command == "review":
        print(review_issues(issue_type=args.type, limit=args.limit))
        return

    if args.command == "evidence":
        if args.evidence_command == "add-articles":
            status = None
            if args.status == "in-profile":
                status = True
            elif args.status == "not-in-profile":
                status = False
            print(
                format_add_articles_candidates(
                    load_add_articles_candidates(),
                    in_profile=status,
                    limit=args.limit,
                )
            )
            return

    if args.command == "verify":
        print(json.dumps(verify_issues(), indent=2, sort_keys=True))
        return


if __name__ == "__main__":
    main()
