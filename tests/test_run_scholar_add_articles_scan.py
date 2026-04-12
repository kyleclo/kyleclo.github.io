from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.run_scholar_add_articles_scan import load_queries


class TestRunScholarAddArticlesScan(unittest.TestCase):
    def test_load_queries_ignores_blank_lines_and_comments(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "queries.txt"
            path.write_text(
                "\n".join(
                    [
                        "# comment",
                        "",
                        "Kyle Lo",
                        '  "OpenScholar"  ',
                        "# another comment",
                        '"CORD-19"',
                    ]
                )
            )
            self.assertEqual(load_queries(path), ["Kyle Lo", '"OpenScholar"', '"CORD-19"'])


if __name__ == "__main__":
    unittest.main()
