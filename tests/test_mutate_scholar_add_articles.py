from __future__ import annotations

import unittest

from scripts.mutate_scholar_add_articles import (
    build_confirmation_phrase,
    choose_target_row,
    normalize_title_text,
    row_matches_expected_title,
)


class TestMutateScholarAddArticles(unittest.TestCase):
    def test_build_confirmation_phrase(self) -> None:
        self.assertEqual(build_confirmation_phrase("o054MLHYLD4J"), "ADD o054MLHYLD4J")

    def test_row_matches_expected_title_normalizes_case_and_whitespace(self) -> None:
        self.assertTrue(
            row_matches_expected_title("  OLMo 2 Furious ", "olmo   2 furious")
        )
        self.assertFalse(
            row_matches_expected_title("OLMo 2 Furious", "OLMo 2 Furious (COLM's Version)")
        )

    def test_normalize_title_text(self) -> None:
        self.assertEqual(normalize_title_text("  OLMo  2 Furious "), "olmo 2 furious")

    def test_choose_target_row_by_doc_id_and_title(self) -> None:
        rows = [
            {"doc_id": "x", "title": "Different Paper"},
            {"doc_id": "o054MLHYLD4J", "title": "olmo 2 furious, 2025"},
        ]
        row = choose_target_row(rows, "o054MLHYLD4J", "  OLMO 2 FURIOUS, 2025 ")
        self.assertEqual(row["title"], "olmo 2 furious, 2025")

    def test_choose_target_row_rejects_title_mismatch(self) -> None:
        rows = [{"doc_id": "o054MLHYLD4J", "title": "olmo 2 furious, 2025"}]
        with self.assertRaises(RuntimeError):
            choose_target_row(rows, "o054MLHYLD4J", "2 OLMo 2 Furious")


if __name__ == "__main__":
    unittest.main()
