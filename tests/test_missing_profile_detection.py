from __future__ import annotations

import unittest

from scripts.scholar_hygiene.detector import detect_missing_profile_articles


class TestMissingProfileDetection(unittest.TestCase):
    def test_detects_missing_paper_from_coauthor_evidence(self) -> None:
        expected = [
            {
                "id": "paper-1",
                "title": "A Great Paper",
                "author": "Alice Smith and Kyle Lo",
                "year": "2024",
                "doi": "10.1000/test",
                "arxiv": "",
                "url": "",
            }
        ]
        my_publications = [
            {
                "id": "pub-1",
                "title": "A Different Paper",
                "author": "Kyle Lo",
                "year": "2024",
                "full_json": {"bib": {"title": "A Different Paper"}},
            }
        ]
        coauthors = [
            {
                "name": "Alice Smith",
                "publications": [
                    {
                        "bib": {
                            "title": "A Great Paper",
                            "author": "Alice Smith and Kyle Lo",
                            "pub_year": "2024",
                            "doi": "10.1000/test",
                        },
                        "num_citations": 42,
                    }
                ],
            }
        ]

        issues = detect_missing_profile_articles(expected, my_publications, coauthors)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]["type"], "missing_profile_article")
        self.assertEqual(issues[0]["confidence"], "high")

    def test_detects_missing_paper_from_add_articles_evidence(self) -> None:
        expected = [
            {
                "id": "paper-cord19",
                "title": "Cord-19: The COVID-19 open research dataset",
                "author": "LL Wang and Kyle Lo and Y Chandrasekhar",
                "year": "2020",
                "doi": "",
                "arxiv": "",
                "url": "",
            }
        ]
        my_publications = [
            {
                "id": "pub-1",
                "title": "A Different Paper",
                "author": "Kyle Lo",
                "year": "2020",
                "full_json": {"bib": {"title": "A Different Paper"}},
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

        issues = detect_missing_profile_articles(
            expected,
            my_publications,
            [],
            add_articles_candidates=add_articles_candidates,
        )
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]["type"], "missing_profile_article")
        self.assertEqual(
            issues[0]["evidence"]["add_articles_candidate"]["doc_id"],
            "lY3Lk2jqby8J",
        )
        self.assertIn(
            "candidate row not marked in profile",
            issues[0]["evidence"]["reasons"],
        )


if __name__ == "__main__":
    unittest.main()
