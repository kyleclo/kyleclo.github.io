from __future__ import annotations

import unittest

from scripts.investigate_scholar_ui import (
    extract_query_from_relative_url,
    normalize_query_text,
    should_reuse_existing_query_state,
)


class TestInvestigateScholarUi(unittest.TestCase):
    def test_normalize_query_text_collapses_whitespace(self) -> None:
        self.assertEqual(normalize_query_text('  "OpenScholar"   '), '"OpenScholar"')

    def test_extract_query_from_relative_url(self) -> None:
        self.assertEqual(
            extract_query_from_relative_url(
                "/citations?view_op=import_lookup&hl=en&imq=%22CORD-19%22&json=&btnA=1"
            ),
            '"CORD-19"',
        )
        self.assertEqual(
            extract_query_from_relative_url(
                "?hl=en&imq=Kyle+Lo&btnA=1&view_op=import_lookup&json=&imstart=10"
            ),
            "Kyle Lo",
        )

    def test_should_reuse_existing_query_state_when_query_matches_page_one(self) -> None:
        self.assertTrue(
            should_reuse_existing_query_state(
                requested_query="Kyle Lo",
                current_query="Kyle Lo",
                current_start="1",
                current_doc_ids=("doc-1", "doc-2"),
            )
        )

    def test_should_not_reuse_existing_query_state_when_offset_or_query_differs(self) -> None:
        self.assertFalse(
            should_reuse_existing_query_state(
                requested_query='"CORD-19"',
                current_query='"OpenScholar"',
                current_start="1",
                current_doc_ids=("doc-1",),
            )
        )
        self.assertFalse(
            should_reuse_existing_query_state(
                requested_query="Kyle Lo",
                current_query="Kyle Lo",
                current_start="21",
                current_doc_ids=("doc-1",),
            )
        )
        self.assertFalse(
            should_reuse_existing_query_state(
                requested_query="Kyle Lo",
                current_query="Kyle Lo",
                current_start="1",
                current_doc_ids=(),
            )
        )


if __name__ == "__main__":
    unittest.main()
