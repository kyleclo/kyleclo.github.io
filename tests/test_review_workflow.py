from __future__ import annotations

import unittest

from scripts.scholar_hygiene.workflow import related_add_articles_candidates


class TestReviewWorkflow(unittest.TestCase):
    def test_related_add_articles_candidates_groups_same_query_family(self) -> None:
        issue = {
            "title": "2 OLMo 2 Furious",
            "evidence": {
                "add_articles_candidate": {
                    "title": "olmo 2 furious, 2025",
                    "doc_id": "candidate-1",
                    "search_query": "olmo 2 furious",
                }
            },
        }
        candidates = [
            {
                "title": "2 OLMo 2 Furious",
                "doc_id": "in-profile-1",
                "search_query": "olmo 2 furious",
                "in_profile": True,
            },
            {
                "title": "OLMo 2 Furious. arXiv 2024",
                "doc_id": "candidate-2",
                "search_query": "olmo 2 furious",
                "in_profile": False,
            },
            {
                "title": "Completely Different Paper",
                "doc_id": "different",
                "search_query": "olmo 2 furious",
                "in_profile": False,
            },
            {
                "title": "2 OLMo 2 Furious",
                "doc_id": "wrong-query",
                "search_query": "Kyle Lo",
                "in_profile": True,
            },
        ]

        related_in_profile, related_not_in_profile = related_add_articles_candidates(issue, candidates)
        self.assertEqual([row["doc_id"] for row in related_in_profile], ["in-profile-1"])
        self.assertEqual([row["doc_id"] for row in related_not_in_profile], ["candidate-2"])


if __name__ == "__main__":
    unittest.main()
