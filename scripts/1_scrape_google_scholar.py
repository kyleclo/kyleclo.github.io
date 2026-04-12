# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "scholarly",
#     "tqdm",
# ]
# ///
"""
Scrape Google Scholar for the configured author and save to the local SQLite DB.

This is the stable raw-ingestion entrypoint. It preserves compatibility with the
existing `_bibliography/gscholar_export.db` schema while delegating the actual
scrape logic to `scripts.scholar_hygiene.ingest`.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.scholar_hygiene.ingest import refresh_profile_to_path


def main() -> None:
    summary = refresh_profile_to_path()
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
