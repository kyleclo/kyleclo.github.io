from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.scholar_merge_queue import (
    build_discovered_queue_items,
    classify_family_type,
    classify_queue_confidence,
    discover_merge_families,
    family_similarity,
    format_merge_queue,
    format_merge_queue_item,
    format_merge_queue_triage,
    get_queue_item,
    load_merge_queue,
    merge_discovered_items,
    queue_item_matches_filters,
    save_merge_queue,
    select_approved_items,
    select_queue_items,
    select_next_approved_item,
    titles_pass_family_heuristics,
    summarize_verification_output,
    update_queue_item_result,
    update_queue_item_status,
    update_queue_item_verification,
)


class TestScholarMergeQueue(unittest.TestCase):
    def test_family_similarity_groups_dolma_variants(self) -> None:
        self.assertGreaterEqual(
            family_similarity(
                "Dolma: An open corpus of three trillion tokens for language model pretraining research",
                "Dolma: An open corpus of 3 trillion tokens for language model pretraining research",
            ),
            0.95,
        )

    def test_discover_merge_families_finds_olmo_family(self) -> None:
        rows = [
            {
                "row_id": "anchor",
                "title": "2 OLMo 2 Furious",
                "citations": "343",
                "year": "2024",
            },
            {
                "row_id": "variant",
                "title": "Faeze Brahman, Christopher Clark, and 21 others. 2025. 2 olmo 2 furious",
                "citations": "56",
                "year": "",
            },
            {
                "row_id": "other",
                "title": "SciBERT: A pretrained language model for scientific text",
                "citations": "5669",
                "year": "2019",
            },
        ]
        families = discover_merge_families(rows)
        self.assertEqual(len(families), 1)
        self.assertEqual({row["row_id"] for row in families[0]}, {"anchor", "variant"})

    def test_titles_pass_family_heuristics_rejects_ordinal_series_mismatch(self) -> None:
        self.assertFalse(
            titles_pass_family_heuristics(
                "Overview of the third workshop on scholarly document processing",
                "Overview of the second workshop on scholarly document processing",
            )
        )

    def test_titles_pass_family_heuristics_rejects_colon_suffix_mismatch(self) -> None:
        self.assertFalse(
            titles_pass_family_heuristics(
                "Scim: Intelligent skimming support for scientific papers",
                "Scim: Intelligent faceted highlights for interactive, multi-pass skimming of scientific papers",
            )
        )

    def test_discover_merge_families_rejects_ordinal_series_mismatch(self) -> None:
        rows = [
            {
                "row_id": "third",
                "title": "Overview of the third workshop on scholarly document processing",
                "citations": "9",
                "year": "2022",
            },
            {
                "row_id": "second",
                "title": "Overview of the second workshop on scholarly document processing",
                "citations": "8",
                "year": "2021",
            },
        ]
        self.assertEqual(discover_merge_families(rows), [])

    def test_discover_merge_families_rejects_scim_false_positive(self) -> None:
        rows = [
            {
                "row_id": "scim-a",
                "title": "Scim: Intelligent skimming support for scientific papers",
                "citations": "73",
                "year": "2023",
            },
            {
                "row_id": "scim-b",
                "title": "Scim: Intelligent faceted highlights for interactive, multi-pass skimming of scientific papers",
                "citations": "10",
                "year": "2022",
            },
        ]
        self.assertEqual(discover_merge_families(rows), [])

    def test_build_discovered_queue_items(self) -> None:
        items = build_discovered_queue_items(
            [
                {
                    "row_id": "a",
                    "title": "Dolma: An open corpus of three trillion tokens for language model pretraining research",
                    "citations": "377",
                    "year": "2024",
                },
                {
                    "row_id": "b",
                    "title": "Dolma: An open corpus of 3 trillion tokens for language model pretraining research",
                    "citations": "12",
                    "year": "2023",
                },
            ],
            source={"captured_url": "https://scholar.google.com/example"},
        )
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["status"], "discovered")
        self.assertEqual(len(items[0]["targets"]), 2)
        self.assertEqual(items[0]["discovery_source"]["captured_url"], "https://scholar.google.com/example")

    def test_merge_discovered_items_preserves_existing_status(self) -> None:
        existing = {
            "generated_at": "2026-04-13T00:00:00Z",
            "items": [
                {
                    "id": "merge:dolma:123",
                    "status": "approved",
                    "family_label": "Old Label",
                    "targets": [{"row_id": "a", "title": "Old", "citations": "1", "year": "2024"}],
                    "review_notes": "keep me",
                    "approved_by_operator": True,
                }
            ],
        }
        discovered = [
            {
                "id": "merge:dolma:123",
                "status": "discovered",
                "family_label": "Dolma",
                "targets": [{"row_id": "a", "title": "New", "citations": "2", "year": "2024"}],
                "discovery_source": {},
                "review_notes": "",
                "approved_by_operator": False,
                "execution_attempts": 0,
                "result": None,
                "discovered_at": "2026-04-13T00:00:01Z",
            }
        ]
        payload = merge_discovered_items(existing, discovered)
        self.assertEqual(payload["items"][0]["status"], "approved")
        self.assertEqual(payload["items"][0]["review_notes"], "keep me")
        self.assertEqual(payload["items"][0]["family_label"], "Dolma")
        self.assertEqual(payload["items"][0]["targets"][0]["title"], "New")

    def test_merge_discovered_items_preserves_status_when_family_id_changes(self) -> None:
        existing = {
            "generated_at": "2026-04-13T00:00:00Z",
            "items": [
                {
                    "id": "merge:olmo:old",
                    "status": "reviewed",
                    "family_label": "2 OLMo 2 Furious",
                    "targets": [
                        {"row_id": "anchor", "title": "2 OLMo 2 Furious", "citations": "396", "year": "2024"},
                        {"row_id": "old-variant", "title": "olmo 2 furious", "citations": "16", "year": ""},
                    ],
                    "review_notes": "keep reviewed state",
                    "approved_by_operator": False,
                }
            ],
        }
        discovered = [
            {
                "id": "merge:olmo:new",
                "status": "discovered",
                "family_label": "2 OLMo 2 Furious",
                "targets": [
                    {"row_id": "anchor", "title": "2 OLMo 2 Furious", "citations": "396", "year": "2024"},
                    {"row_id": "new-variant", "title": "olmo 2 furious, 2025", "citations": "32", "year": "2025"},
                ],
                "discovery_source": {},
                "review_notes": "",
                "approved_by_operator": False,
                "execution_attempts": 0,
                "result": None,
                "discovered_at": "2026-04-13T00:00:01Z",
            }
        ]
        payload = merge_discovered_items(existing, discovered)
        self.assertEqual(len(payload["items"]), 1)
        self.assertEqual(payload["items"][0]["id"], "merge:olmo:new")
        self.assertEqual(payload["items"][0]["status"], "reviewed")
        self.assertEqual(payload["items"][0]["review_notes"], "keep reviewed state")

    def test_load_and_save_merge_queue(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "merge_queue.json"
            save_merge_queue(path, {"generated_at": None, "items": [{"id": "x", "status": "discovered"}]})
            payload = load_merge_queue(path)
            self.assertEqual(payload["items"][0]["id"], "x")

    def test_format_merge_queue(self) -> None:
        text = format_merge_queue(
            [
                {
                    "id": "merge:dolma:123",
                    "family_label": "Dolma",
                    "status": "discovered",
                    "targets": [
                        {
                            "row_id": "a",
                            "title": "Dolma: An open corpus of three trillion tokens for language model pretraining research",
                            "citations": "377",
                            "year": "2024",
                        }
                    ],
                }
            ]
        )
        self.assertIn("Dolma (status=discovered, targets=1)", text)

    def test_format_merge_queue_triage(self) -> None:
        text = format_merge_queue_triage(
            [
                {
                    "id": "merge:dolma:123",
                    "family_label": "Dolma",
                    "status": "discovered",
                    "targets": [
                        {"title": "Dolma: An open corpus of three trillion tokens for language model pretraining research"},
                        {"title": "Dolma: An open corpus of 3 trillion tokens for language model pretraining research"},
                    ],
                }
            ]
        )
        self.assertIn("type=pair", text)
        self.assertIn("confidence=high", text)

    def test_classify_family_type_and_confidence(self) -> None:
        item = {
            "targets": [
                {"title": "Dolma: An open corpus of three trillion tokens for language model pretraining research"},
                {"title": "Dolma: An open corpus of 3 trillion tokens for language model pretraining research"},
            ]
        }
        self.assertEqual(classify_family_type(item), "pair")
        self.assertEqual(classify_queue_confidence(item), "high")

    def test_update_queue_item_status(self) -> None:
        payload = {
            "generated_at": None,
            "items": [
                {
                    "id": "merge:dolma:123",
                    "status": "discovered",
                    "family_label": "Dolma",
                    "targets": [],
                    "review_notes": "",
                    "approved_by_operator": False,
                }
            ],
        }
        updated = update_queue_item_status(
            payload,
            item_id="merge:dolma:123",
            status="approved",
            note="clear duplicate",
        )
        item = get_queue_item(updated, "merge:dolma:123")
        self.assertEqual(item["status"], "approved")
        self.assertTrue(item["approved_by_operator"])
        self.assertEqual(item["review_notes"], "clear duplicate")
        self.assertIn("approved_at", item)

    def test_update_queue_item_status_needs_manual_repair_clears_approval(self) -> None:
        payload = {
            "generated_at": None,
            "items": [
                {
                    "id": "merge:scim:123",
                    "status": "merged",
                    "family_label": "Scim",
                    "targets": [],
                    "review_notes": "",
                    "approved_by_operator": True,
                    "approved_at": "2026-04-13T00:00:01Z",
                }
            ],
        }
        updated = update_queue_item_status(
            payload,
            item_id="merge:scim:123",
            status="needs_manual_repair",
            note="Incorrect merge; requires manual Scholar repair.",
        )
        item = get_queue_item(updated, "merge:scim:123")
        self.assertEqual(item["status"], "needs_manual_repair")
        self.assertFalse(item["approved_by_operator"])
        self.assertNotIn("approved_at", item)

    def test_format_merge_queue_item(self) -> None:
        text = format_merge_queue_item(
            {
                "id": "merge:dolma:123",
                "status": "approved",
                "family_label": "Dolma",
                "targets": [
                    {
                        "row_id": "a",
                        "title": "Dolma: An open corpus of three trillion tokens for language model pretraining research",
                        "citations": "377",
                        "year": "2024",
                    }
                ],
                "review_notes": "clear duplicate",
                "discovery_source": {"captured_url": "https://example.com", "row_count": 100, "expanded_show_more_steps": 1},
            }
        )
        self.assertIn("ID: merge:dolma:123", text)
        self.assertIn("Review Notes: clear duplicate", text)

    def test_select_next_approved_item(self) -> None:
        item = select_next_approved_item(
            {
                "items": [
                    {
                        "id": "b",
                        "status": "approved",
                        "approved_by_operator": True,
                        "approved_at": "2026-04-13T00:00:02Z",
                        "family_label": "B",
                    },
                    {
                        "id": "a",
                        "status": "approved",
                        "approved_by_operator": True,
                        "approved_at": "2026-04-13T00:00:01Z",
                        "family_label": "A",
                    },
                ]
            }
        )
        self.assertEqual(item["id"], "a")

    def test_select_approved_items_respects_order_and_limit(self) -> None:
        items = select_approved_items(
            {
                "items": [
                    {
                        "id": "b",
                        "status": "approved",
                        "approved_by_operator": True,
                        "approved_at": "2026-04-13T00:00:02Z",
                        "family_label": "B",
                    },
                    {
                        "id": "a",
                        "status": "approved",
                        "approved_by_operator": True,
                        "approved_at": "2026-04-13T00:00:01Z",
                        "family_label": "A",
                    },
                ]
            },
            limit=1,
        )
        self.assertEqual([item["id"] for item in items], ["a"])

    def test_queue_item_matches_filters(self) -> None:
        item = {
            "status": "discovered",
            "family_label": "Dolma",
            "targets": [
                {"title": "Dolma: An open corpus of three trillion tokens for language model pretraining research"},
                {"title": "Dolma: An open corpus of 3 trillion tokens for language model pretraining research"},
            ],
        }
        self.assertTrue(queue_item_matches_filters(item, status="discovered", family_type="pair", confidence="high"))
        self.assertTrue(queue_item_matches_filters(item, contains="3 trillion"))
        self.assertFalse(queue_item_matches_filters(item, exclude_contains="3 trillion"))

    def test_select_queue_items_filters(self) -> None:
        payload = {
            "items": [
                {
                    "id": "pair-high",
                    "status": "discovered",
                    "family_label": "Dolma",
                    "targets": [
                        {"title": "Dolma: An open corpus of three trillion tokens for language model pretraining research"},
                        {"title": "Dolma: An open corpus of 3 trillion tokens for language model pretraining research"},
                    ],
                },
                {
                    "id": "multi-low",
                    "status": "discovered",
                    "family_label": "OpenScholar",
                    "targets": [
                        {"title": "Openscholar: Synthesizing scientific literature with retrieval-augmented lms"},
                        {"title": "Synthesizing scientific literature with retrieval-augmented language models"},
                        {"title": "OpenScholar: synthesizing scientific literature with retrieval-augmented language models"},
                    ],
                },
            ]
        }
        items = select_queue_items(payload, status="discovered", family_type="pair", confidence="high")
        self.assertEqual([item["id"] for item in items], ["pair-high"])

    def test_update_queue_item_result(self) -> None:
        payload = {
            "generated_at": None,
            "items": [
                {
                    "id": "merge:dolma:123",
                    "status": "approved",
                    "family_label": "Dolma",
                    "targets": [],
                    "execution_attempts": 0,
                    "approved_by_operator": True,
                }
            ],
        }
        updated = update_queue_item_result(
            payload,
            item_id="merge:dolma:123",
            result={"runner_mode": "dry_run"},
            status="reviewed",
            increment_execution_attempts=False,
        )
        item = get_queue_item(updated, "merge:dolma:123")
        self.assertEqual(item["status"], "reviewed")
        self.assertEqual(item["result"]["runner_mode"], "dry_run")

    def test_update_queue_item_result_can_preserve_approved_status(self) -> None:
        payload = {
            "generated_at": None,
            "items": [
                {
                    "id": "merge:olmo:123",
                    "status": "approved",
                    "family_label": "OLMo",
                    "targets": [],
                    "execution_attempts": 0,
                    "approved_by_operator": True,
                }
            ],
        }
        updated = update_queue_item_result(
            payload,
            item_id="merge:olmo:123",
            result={"runner_mode": "dry_run"},
            status="approved",
            increment_execution_attempts=False,
        )
        item = get_queue_item(updated, "merge:olmo:123")
        self.assertEqual(item["status"], "approved")
        self.assertEqual(item["result"]["runner_mode"], "dry_run")

    def test_summarize_verification_output(self) -> None:
        summary = summarize_verification_output(
            "1. OLMo: Accelerating the science of language models (row_id=x, citations=508, year=2024)"
        )
        self.assertEqual(summary["status"], "verified_visible_rows")
        self.assertEqual(summary["visible_line_count"], 1)

    def test_update_queue_item_verification(self) -> None:
        payload = {
            "generated_at": None,
            "items": [
                {
                    "id": "merge:olmo:123",
                    "status": "merged",
                    "family_label": "OLMo",
                    "targets": [],
                    "result": {"runner_mode": "execute"},
                }
            ],
        }
        updated = update_queue_item_verification(
            payload,
            item_id="merge:olmo:123",
            verification={"status": "verified_visible_rows", "visible_line_count": 1},
        )
        item = get_queue_item(updated, "merge:olmo:123")
        self.assertEqual(item["result"]["verification"]["status"], "verified_visible_rows")


if __name__ == "__main__":
    unittest.main()
