from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCHOLAR_USER_ID = "jY919eMAAAAJ"

DB_FILE = REPO_ROOT / "_bibliography" / "gscholar_export.db"
PAPERS_BIB_FILE = REPO_ROOT / "_bibliography" / "papers.bib"
ISSUES_JSON_FILE = REPO_ROOT / "_bibliography" / "scholar_issues.json"
ISSUES_CSV_FILE = REPO_ROOT / "_bibliography" / "scholar_issues.csv"
STATE_JSON_FILE = REPO_ROOT / "_bibliography" / "scholar_state.json"
DISMISSALS_JSON_FILE = REPO_ROOT / "_bibliography" / "scholar_dismissals.json"
SCHOLAR_UI_ARTIFACT_DIR = REPO_ROOT / "plans" / "artifacts" / "scholar_ui"


def get_scholar_user_id() -> str:
    return os.environ.get("SCHOLAR_USER_ID", DEFAULT_SCHOLAR_USER_ID)
