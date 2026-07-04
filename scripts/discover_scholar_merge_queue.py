# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "playwright",
# ]
# ///
"""
Read-only Google Scholar merge-family discovery helper.

This script:
- attaches to an already-open logged-in Scholar session over CDP
- optionally expands the visible profile rows with bounded Show more clicks
- proposes likely duplicate families from the visible profile rows
- writes the discovered families into a local merge queue artifact
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.scholar_merge_queue import (
    build_discovered_queue_items,
    default_merge_queue_path,
    format_merge_queue,
    load_merge_queue,
    merge_discovered_items,
    save_merge_queue,
)


async def run(
    *,
    cdp_url: str,
    queue_file: Path,
    expand_show_more: int,
    title_filter: str | None,
    min_similarity: float,
) -> None:
    from playwright.async_api import async_playwright

    async def wait_for_profile_page(page, timeout_seconds: int = 20) -> None:
        deadline = asyncio.get_running_loop().time() + timeout_seconds
        while asyncio.get_running_loop().time() < deadline:
            has_profile_table = await page.locator(".gsc_a_tr").count() > 0
            has_add_button = await page.locator("#gsc_dd_add-b").count() > 0
            if has_profile_table and has_add_button:
                return
            await page.wait_for_timeout(500)
        raise RuntimeError("Timed out waiting for the Scholar profile page action bar.")

    async def select_existing_page(context):
        for candidate in reversed(context.pages):
            has_profile_table = await candidate.locator(".gsc_a_tr").count() > 0
            if has_profile_table:
                return candidate
        return context.pages[-1] if context.pages else await context.new_page()

    async def profile_rows(page) -> list[dict]:
        return await page.locator(".gsc_a_tr").evaluate_all(
            """(rows) => rows.map((row) => {
                const checkbox = row.querySelector("input[type='checkbox']");
                const titleLink = row.querySelector(".gsc_a_at");
                const citationCell = row.querySelector(".gsc_a_c");
                const yearCell = row.querySelector(".gsc_a_y");
                return {
                    row_id: checkbox ? (checkbox.value || checkbox.id || "") : "",
                    title: titleLink ? (titleLink.textContent || "").trim() : "",
                    citations: citationCell ? (citationCell.textContent || "").trim() : "",
                    year: yearCell ? (yearCell.textContent || "").trim() : "",
                };
            })"""
        )

    async def click_show_more(page, steps: int) -> int:
        expanded = 0
        for _ in range(steps):
            button = page.locator("#gsc_bpf_more")
            if await button.count() == 0 or await button.first.is_disabled():
                return expanded
            before = await page.locator(".gsc_a_tr").count()
            await button.first.evaluate("(node) => node.click()")
            deadline = asyncio.get_running_loop().time() + 10
            while asyncio.get_running_loop().time() < deadline:
                after = await page.locator(".gsc_a_tr").count()
                if after > before:
                    expanded += 1
                    break
                await page.wait_for_timeout(250)
            else:
                raise RuntimeError("Timed out waiting for more profile rows after clicking Show more.")
        return expanded

    async with async_playwright() as playwright:
        browser = await playwright.chromium.connect_over_cdp(cdp_url)
        if browser.contexts:
            context = browser.contexts[0]
        else:
            context = await browser.new_context()
        page = await select_existing_page(context)
        await wait_for_profile_page(page)
        expanded_steps = await click_show_more(page, expand_show_more)
        rows = await profile_rows(page)
        if title_filter:
            needle = " ".join(title_filter.split()).casefold()
            rows = [row for row in rows if needle in row.get("title", "").casefold()]

        discovered_items = build_discovered_queue_items(
            rows,
            source={
                "captured_url": page.url,
                "expanded_show_more_steps": expanded_steps,
                "row_count": len(rows),
                "title_filter": title_filter or "",
            },
            min_similarity=min_similarity,
        )
        payload = merge_discovered_items(load_merge_queue(queue_file), discovered_items)
        save_merge_queue(queue_file, payload)
        print(
            json.dumps(
                {
                    "queue_file": str(queue_file),
                    "discovered_item_count": len(discovered_items),
                    "expanded_show_more_steps": expanded_steps,
                    "visible_row_count": len(rows),
                },
                indent=2,
                sort_keys=True,
            )
        )
        print("")
        print(format_merge_queue(discovered_items))
        await browser.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cdp-url", required=True, help="Chrome DevTools URL for an already-open logged-in browser.")
    parser.add_argument(
        "--queue-file",
        type=Path,
        default=default_merge_queue_path(),
        help="Where the read-only discovered merge queue should be written.",
    )
    parser.add_argument(
        "--expand-show-more",
        type=int,
        default=0,
        help="How many bounded Show more clicks to perform before collecting visible rows.",
    )
    parser.add_argument(
        "--title-filter",
        help="Optional case-insensitive title substring filter for discovery.",
    )
    parser.add_argument(
        "--min-similarity",
        type=float,
        default=0.74,
        help="Minimum title-family overlap score needed to propose a duplicate family.",
    )
    args = parser.parse_args()
    asyncio.run(
        run(
            cdp_url=args.cdp_url,
            queue_file=args.queue_file,
            expand_show_more=args.expand_show_more,
            title_filter=args.title_filter,
            min_similarity=args.min_similarity,
        )
    )


if __name__ == "__main__":
    main()
