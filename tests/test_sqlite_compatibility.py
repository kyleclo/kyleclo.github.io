from __future__ import annotations

import sqlite3
import unittest

from scripts.scholar_hygiene.config import DB_FILE
from scripts.scholar_hygiene.db import ensure_base_tables, load_cached_coauthors, load_publications, load_versions_for_publication_ids


class TestSqliteCompatibility(unittest.TestCase):
    def test_existing_db_is_readable_and_compatible(self) -> None:
        self.assertTrue(DB_FILE.exists(), f"Expected DB to exist at {DB_FILE}")
        conn = sqlite3.connect(str(DB_FILE))
        try:
            ensure_base_tables(conn)
            publications = load_publications(conn)
            versions = load_versions_for_publication_ids(conn)
            coauthors = load_cached_coauthors(conn)
        finally:
            conn.close()

        self.assertGreater(len(publications), 0)
        self.assertIsInstance(versions, dict)
        self.assertIsInstance(coauthors, list)
        first = publications[0]
        self.assertIn("id", first)
        self.assertIn("title", first)
        self.assertIn("full_json", first)


if __name__ == "__main__":
    unittest.main()
