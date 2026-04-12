from __future__ import annotations

import unittest

from scripts.scholar_hygiene.detector import detect_under_clustered_articles


class TestUnderClusteredDetection(unittest.TestCase):
    def test_detects_profile_entries_with_shared_clusters(self) -> None:
        publications = [
            {
                "id": "left",
                "title": "A Great Paper",
                "author": "Alice Smith and Kyle Lo",
                "year": "2024",
                "num_citations": 10,
                "cites_id": ["cluster-1"],
            },
            {
                "id": "right",
                "title": "A Great Paper Extended",
                "author": "Alice Smith and Kyle Lo",
                "year": "2024",
                "num_citations": 12,
                "cites_id": ["cluster-1"],
            },
        ]

        issues = detect_under_clustered_articles(publications, [])
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]["type"], "under_clustered_profile_article")
        self.assertIn("cluster-1", issues[0]["evidence"]["shared_clusters"])

    def test_detects_add_articles_variant_for_existing_profile_paper(self) -> None:
        publications = [
            {
                "id": "cord19-profile",
                "title": "CORD-19}: The {COVID-19} Open Research Dataset",
                "author": "Wang, Lucy Lu and Lo, Kyle and Chandrasekhar, Yoganand",
                "year": "2020",
                "num_citations": 1169,
                "cites_id": ["14379169419409422584"],
                "full_json": {"bib": {"title": "CORD-19}: The {COVID-19} Open Research Dataset"}},
            }
        ]
        add_articles_candidates = [
            {
                "title": "Cord-19: The COVID-19 open research dataset. arXiv 2020",
                "title_url": "https://scholar.google.com/scholar?oi=bibs&cluster=3418208377074584981&btnI=1&hl=en",
                "authors_venue": "LL Wang, K Lo, Y Chandrasekhar, R Reas - arXiv preprint arXiv:2004.10706, 2020",
                "author": "LL Wang, K Lo, Y Chandrasekhar, R Reas",
                "year": "2020",
                "doc_id": "lY3Lk2jqby8J",
                "search_query": "kyle lo",
                "captured_url": "https://scholar.google.com/citations?...imstart=130",
                "artifact_file": "plans/artifacts/scholar_ui/current_page_20260411_112522_add_articles.json",
                "in_profile": False,
            }
        ]

        issues = detect_under_clustered_articles(
            publications,
            [],
            add_articles_candidates=add_articles_candidates,
        )
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]["type"], "under_clustered_profile_article")
        self.assertEqual(
            issues[0]["evidence"]["add_articles_candidate"]["doc_id"],
            "lY3Lk2jqby8J",
        )
        self.assertIn(
            "candidate row not marked in profile",
            issues[0]["evidence"]["reasons"],
        )

    def test_prefers_targeted_query_bundle_over_broad_query_candidate(self) -> None:
        publications = [
            {
                "id": "olmo-profile",
                "title": "2 OLMo 2 Furious",
                "author": "T OLMo and P Walsh and L Soldaini and D Groeneveld and Kyle Lo",
                "year": "2024",
                "num_citations": 24,
                "cites_id": ["2928412902057166176"],
                "full_json": {"bib": {"title": "2 OLMo 2 Furious"}},
            }
        ]
        add_articles_candidates = [
            {
                "title": "olmo 2 furious, 2025",
                "title_url": "https://scholar.google.com/scholar?oi=bibs&cluster=4480193984860802723&btnI=1&hl=en",
                "authors_venue": "T OLMo, P Walsh, L Soldaini, D Groeneveld, K Lo - arXiv preprint arXiv:2501.00656, 2024",
                "author": "T OLMo, P Walsh, L Soldaini, D Groeneveld, K Lo",
                "year": "2024",
                "doc_id": "broad-candidate",
                "search_query": "Kyle Lo",
                "captured_url": "https://scholar.google.com/citations?...imstart=0",
                "artifact_file": "broad.json",
                "in_profile": False,
            },
            {
                "title": "olmo 2 furious",
                "title_url": "https://scholar.google.com/scholar?oi=bibs&cluster=15195229993886287284&btnI=1&hl=en",
                "authors_venue": "P Walsh, L Soldaini, D Groeneveld, K Lo, S Arora - arXiv preprint arXiv:2501.00656, 2025",
                "author": "P Walsh, L Soldaini, D Groeneveld, K Lo, S Arora",
                "year": "2025",
                "doc_id": "targeted-candidate",
                "search_query": "olmo 2 furious",
                "captured_url": "https://scholar.google.com/citations?...imstart=10",
                "artifact_file": "targeted.json",
                "in_profile": False,
            },
        ]

        issues = detect_under_clustered_articles(
            publications,
            [],
            add_articles_candidates=add_articles_candidates,
        )
        self.assertEqual(len(issues), 1)
        self.assertEqual(
            issues[0]["evidence"]["add_articles_candidate"]["doc_id"],
            "targeted-candidate",
        )
        self.assertIn(
            "query",
            "; ".join(issues[0]["evidence"]["reasons"]),
        )


if __name__ == "__main__":
    unittest.main()
