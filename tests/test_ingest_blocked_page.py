from __future__ import annotations

import unittest

from scripts.scholar_hygiene.ingest import detect_blocked_scholar_page


class TestIngestBlockedPage(unittest.TestCase):
    def test_detects_captcha_page(self) -> None:
        html = """
        <html>
          <body>
            <div id="gsc_captcha_ccl">
              <h1>Please show you're not a robot</h1>
            </div>
          </body>
        </html>
        """
        self.assertEqual(detect_blocked_scholar_page(html), "captcha")


if __name__ == "__main__":
    unittest.main()
