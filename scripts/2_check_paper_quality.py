# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "scholarly",
#     "tqdm",
# ]
# ///
"""
Deprecated wrapper for the old paper quality report.

Use `uv run scripts/scholar_hygiene.py detect` and
`uv run scripts/scholar_hygiene.py review --type metadata_anomaly` instead.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.scholar_hygiene.workflow import collect_issues, review_issues


def main() -> None:
    collect_issues()
    print(review_issues(issue_type="metadata_anomaly", limit=50))


if __name__ == "__main__":
    main()
