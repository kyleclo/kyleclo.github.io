from __future__ import annotations

import unittest

from scripts.mutate_scholar_merge_family import (
    build_confirmation_phrase,
    choose_confirmation_merge_action,
    choose_merge_action,
    choose_target_rows,
    filter_rows_by_title,
    format_visible_actions,
    format_visible_rows,
    normalize_title_text,
    parse_target_spec,
    row_matches_expected_title,
    selector_for_id,
)


class TestMutateScholarMergeFamily(unittest.TestCase):
    def test_parse_target_spec(self) -> None:
        self.assertEqual(
            parse_target_spec(" YMXJ3gTQoygJ :: 2 OLMo 2 Furious "),
            {"row_id": "YMXJ3gTQoygJ", "expected_title": "2 OLMo 2 Furious"},
        )

    def test_parse_target_spec_requires_separator_and_title(self) -> None:
        with self.assertRaises(ValueError):
            parse_target_spec("YMXJ3gTQoygJ")
        with self.assertRaises(ValueError):
            parse_target_spec("YMXJ3gTQoygJ::")

    def test_build_confirmation_phrase_sorts_row_ids(self) -> None:
        self.assertEqual(
            build_confirmation_phrase(["u0s43F4mZm0J", "YMXJ3gTQoygJ"]),
            "MERGE YMXJ3gTQoygJ u0s43F4mZm0J",
        )

    def test_row_matches_expected_title_normalizes_case_and_whitespace(self) -> None:
        self.assertTrue(
            row_matches_expected_title("  2 OLMo 2 Furious ", "2   olmo 2 furious")
        )
        self.assertFalse(
            row_matches_expected_title("2 OLMo 2 Furious", "2 OLMo 2 Furious (COLM's Version)")
        )

    def test_normalize_title_text(self) -> None:
        self.assertEqual(normalize_title_text("  2 OLMo  2 Furious "), "2 olmo 2 furious")

    def test_choose_target_rows(self) -> None:
        rows = [
            {"row_id": "YMXJ3gTQoygJ", "title": "2 OLMo 2 Furious"},
            {"row_id": "u0s43F4mZm0J", "title": "2 olmo 2 furious"},
            {"row_id": "other", "title": "Different Paper"},
        ]
        selected = choose_target_rows(
            rows,
            [
                {"row_id": "YMXJ3gTQoygJ", "expected_title": "2 OLMo 2 Furious"},
                {"row_id": "u0s43F4mZm0J", "expected_title": "2 olmo 2 furious"},
            ],
        )
        self.assertEqual([row["row_id"] for row in selected], ["YMXJ3gTQoygJ", "u0s43F4mZm0J"])

    def test_choose_target_rows_rejects_title_mismatch(self) -> None:
        rows = [
            {"row_id": "YMXJ3gTQoygJ", "title": "2 OLMo 2 Furious"},
            {"row_id": "u0s43F4mZm0J", "title": "2 olmo 2 furious"},
        ]
        with self.assertRaises(RuntimeError):
            choose_target_rows(
                rows,
                [
                    {"row_id": "YMXJ3gTQoygJ", "expected_title": "2 OLMo 2 Furious"},
                    {"row_id": "u0s43F4mZm0J", "expected_title": "Wrong Title"},
                ],
            )

    def test_choose_merge_action_requires_single_enabled_merge(self) -> None:
        action = choose_merge_action(
            [
                {"id": "gsc_btn_del", "text": "Delete", "disabled": False, "hidden": False},
                {"id": "gsc_btn_mer", "text": " Merge ", "disabled": False, "hidden": False},
            ]
        )
        self.assertEqual(action["id"], "gsc_btn_mer")

        with self.assertRaises(RuntimeError):
            choose_merge_action([{"id": "gsc_btn_mer", "text": "Merge", "disabled": True, "hidden": False}])

        with self.assertRaises(RuntimeError):
            choose_merge_action([])

        with self.assertRaises(RuntimeError):
            choose_merge_action([{"id": "gsc_btn_mer", "text": "Merge", "disabled": False, "hidden": True}])

    def test_choose_confirmation_merge_action(self) -> None:
        self.assertEqual(
            choose_confirmation_merge_action(
                [
                    {"id": "gsc_md_mopt_merge", "text": "Merge", "disabled": False, "hidden": False},
                    {"id": "gsc_md_mopt_cancel", "text": "Cancel", "disabled": False, "hidden": False},
                ]
            )["id"],
            "gsc_md_mopt_merge",
        )
        self.assertIsNone(
            choose_confirmation_merge_action(
                [{"id": "gsc_md_mopt_merge", "text": "Merge", "disabled": False, "hidden": True}]
            )
        )

    def test_format_visible_rows(self) -> None:
        text = format_visible_rows(
            [
                {
                    "row_id": "YMXJ3gTQoygJ",
                    "title": "2 OLMo 2 Furious",
                    "citations": "12",
                    "year": "2025",
                },
                {
                    "row_id": "u0s43F4mZm0J",
                    "title": "2 olmo 2 furious",
                    "citations": "3",
                    "year": "2024",
                },
            ],
            limit=1,
        )
        self.assertEqual(
            text,
            "1. 2 OLMo 2 Furious (row_id=YMXJ3gTQoygJ, citations=12, year=2025)",
        )

    def test_filter_rows_by_title(self) -> None:
        rows = [
            {"row_id": "a", "title": "2 OLMo 2 Furious"},
            {"row_id": "b", "title": "Dolma: An open corpus"},
        ]
        self.assertEqual(
            [row["row_id"] for row in filter_rows_by_title(rows, "olmo")],
            ["a"],
        )
        self.assertEqual(
            [row["row_id"] for row in filter_rows_by_title(rows, None)],
            ["a", "b"],
        )

    def test_selector_for_id_uses_attribute_selector(self) -> None:
        self.assertEqual(
            selector_for_id("input", "gsc_x:jY919eMAAAAJ:roLk4NBRz8UC"),
            'input[id="gsc_x:jY919eMAAAAJ:roLk4NBRz8UC"]',
        )

    def test_format_visible_actions(self) -> None:
        text = format_visible_actions(
            [
                {"text": "Merge", "tag": "button", "id": "merge", "disabled": False, "hidden": False},
                {"text": "Delete", "tag": "button", "id": "delete", "disabled": True, "hidden": True},
            ]
        )
        self.assertEqual(
            text,
            "1. Merge (tag=button, id=merge, visible, enabled)\n2. Delete (tag=button, id=delete, hidden, disabled)",
        )


if __name__ == "__main__":
    unittest.main()
