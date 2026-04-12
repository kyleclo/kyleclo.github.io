from __future__ import annotations

import unittest

from scripts.scholar_hygiene.detector import detect_metadata_anomalies


class TestMetadataAnomalyDetection(unittest.TestCase):
    def test_detects_conflicting_years_and_venues(self) -> None:
        publications = [
            {
                "id": "pub-1",
                "title": "A Great Paper",
                "author": "Alice Smith and Kyle Lo",
                "year": "2024",
                "num_citations": 10,
                "full_json": {"bib": {"title": "A Great Paper"}},
            }
        ]
        versions_by_publication = {
            "pub-1": [
                {
                    "cluster_id": "cluster-1",
                    "pub_url": "https://example.com/1",
                    "source_json": {"bib": {"title": "A Great Paper", "pub_year": "2024", "journal": "ACL"}},
                },
                {
                    "cluster_id": "cluster-1",
                    "pub_url": "https://example.com/2",
                    "source_json": {"bib": {"title": "A Great Paper", "pub_year": "2023", "journal": "EMNLP"}},
                },
            ]
        }
        expected = [
            {
                "id": "paper-1",
                "title": "A Great Paper",
                "author": "Alice Smith and Kyle Lo",
                "year": "2024",
                "venue": "ACL",
                "doi": "",
                "arxiv": "",
                "url": "",
            }
        ]

        issues = detect_metadata_anomalies(publications, versions_by_publication, expected)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]["type"], "metadata_anomaly")
        self.assertIn("2023", issues[0]["evidence"]["observed_years"])
        self.assertIn("2024", issues[0]["evidence"]["observed_years"])


if __name__ == "__main__":
    unittest.main()
