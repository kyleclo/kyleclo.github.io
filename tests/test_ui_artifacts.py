from __future__ import annotations

import json
import tempfile
import time
import unittest
from pathlib import Path

from scripts.scholar_hygiene.ui_artifacts import load_add_articles_candidates


class TestUiArtifacts(unittest.TestCase):
    def test_prefers_newest_candidate_by_doc_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            artifact_dir = Path(tmpdir)

            older = {
                "search_query": "kyle lo",
                "captured_url": "https://example.com/old",
                "result_stats": {},
                "rows": [
                    {
                        "title": "Cord-19: The COVID-19 open research dataset. arXiv 2020",
                        "authors_venue": "LL Wang, K Lo - arXiv, 2020",
                        "doc_id": "lY3Lk2jqby8J",
                        "in_profile": False,
                    }
                ],
            }
            newer = {
                "search_query": "Kyle Lo",
                "captured_url": "https://example.com/new",
                "result_stats": {},
                "rows": [
                    {
                        "title": "Cord-19: The COVID-19 open research dataset. arXiv 2020",
                        "authors_venue": "LL Wang, K Lo - arXiv, 2020",
                        "doc_id": "lY3Lk2jqby8J",
                        "in_profile": True,
                    }
                ],
            }

            old_path = artifact_dir / "old_add_articles.json"
            new_path = artifact_dir / "new_add_articles.json"
            old_path.write_text(json.dumps(older))
            time.sleep(0.01)
            new_path.write_text(json.dumps(newer))

            candidates = load_add_articles_candidates(artifact_dir)
            self.assertEqual(len(candidates), 1)
            self.assertTrue(candidates[0]["in_profile"])
            self.assertEqual(candidates[0]["captured_url"], "https://example.com/new")

    def test_ignores_newer_empty_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            artifact_dir = Path(tmpdir)

            older = {
                "search_query": "Kyle Lo",
                "captured_url": "https://example.com/old",
                "result_stats": {"start": "1", "end": "10"},
                "rows": [
                    {
                        "title": "olmo 2 furious, 2025",
                        "authors_venue": "T OLMo, P Walsh, L Soldaini, D Groeneveld, K Lo - arXiv, 2024",
                        "doc_id": "o054MLHYLD4J",
                        "in_profile": False,
                    }
                ],
            }
            newer_empty = {
                "search_query": "Kyle Lo",
                "captured_url": "https://example.com/new-empty",
                "result_stats": {},
                "rows": [],
            }

            old_path = artifact_dir / "old_add_articles.json"
            new_path = artifact_dir / "new_add_articles.json"
            old_path.write_text(json.dumps(older))
            time.sleep(0.01)
            new_path.write_text(json.dumps(newer_empty))

            candidates = load_add_articles_candidates(artifact_dir)
            self.assertEqual(len(candidates), 1)
            self.assertEqual(candidates[0]["doc_id"], "o054MLHYLD4J")
            self.assertEqual(candidates[0]["captured_url"], "https://example.com/old")


if __name__ == "__main__":
    unittest.main()
