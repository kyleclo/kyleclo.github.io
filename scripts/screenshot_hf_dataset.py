# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "playwright",
# ]
# ///
"""
Screenshot a Hugging Face dataset card using Playwright.

Call:
    uv run scripts/screenshot_hf_dataset.py

Prerequisites:
    uv run playwright install chromium
"""

import os
from playwright.sync_api import sync_playwright

URL = "https://huggingface.co/datasets/allenai/peS2o"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "../assets/img/publication_preview")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "pes2o-pretraining-efficiently-on-s2orc-dataset.png")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 960})
        page.goto(URL, wait_until="networkidle")

        # Dismiss any cookie banners
        try:
            page.click("button:has-text('Accept')", timeout=3000)
        except Exception:
            pass

        # Wait for content to render
        page.wait_for_timeout(2000)

        # Screenshot the visible viewport
        page.screenshot(path=OUTPUT_FILE)
        print(f"Screenshot saved to {OUTPUT_FILE}")

        browser.close()


if __name__ == "__main__":
    main()
