# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "playwright",
# ]
# ///
"""
Read-only Google Scholar UI investigation helper.

This script exists to test whether a browser automation layer can reliably
assist with Google Scholar profile hygiene work without yet mutating anything.

Typical use:
    uv run playwright install chromium
    uv run scripts/investigate_scholar_ui.py --query "\"paper title\""
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, quote, quote_plus, unquote, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.parse_scholar_add_articles_snapshot import parse_snapshot
from scripts.scholar_hygiene.config import get_scholar_user_id


def default_artifact_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "plans" / "artifacts" / "scholar_ui"


def normalize_query_text(text: str) -> str:
    return " ".join((text or "").split())


def extract_query_from_relative_url(url: str) -> str:
    if not url:
        return ""
    parsed = urlsplit(url)
    params = parse_qs(parsed.query)
    return normalize_query_text(unquote(params.get("imq", [""])[0]))


def should_reuse_existing_query_state(
    *,
    requested_query: str,
    current_query: str,
    current_start: str,
    current_doc_ids: tuple[str, ...],
) -> bool:
    return (
        normalize_query_text(current_query) == normalize_query_text(requested_query)
        and bool(current_doc_ids)
        and current_start in {"", "1"}
    )


async def run(
    query: str | None,
    add_articles_queries: list[str],
    capture_profile: bool,
    detail_url: str | None,
    capture_detail: bool,
    capture_current_page: bool,
    wait_for_add_articles: bool,
    trace_navigation: bool,
    wait_for_enter: bool,
    wait_seconds: int,
    artifact_dir: Path,
    cdp_url: str | None,
    use_existing_page: bool,
    parse_add_articles: bool,
    capture_add_articles_pages: int,
    between_pages_seconds: int,
    between_queries_seconds: int,
) -> None:
    from playwright.async_api import async_playwright

    def page_marker_summary(markers: dict[str, bool]) -> str:
        return ",".join(key for key, value in markers.items() if value)

    scholar_id = get_scholar_user_id()
    profile_url = (
        "https://scholar.google.com/citations"
        f"?view_op=list_works&hl=en&user={scholar_id}"
    )
    search_url = (
        "https://scholar.google.com/scholar?q=" + quote_plus(query)
        if query
        else None
    )
    target_url = detail_url or search_url or profile_url

    async def trace_page_state(page) -> dict[str, object]:
        visible_markers = []
        for selector in [
            "#gsc_prf_in",
            "#gsc_md_iad",
            "#gsc_ia_ac",
            "#gsc_ia_res",
            "#gsc_a_t",
            "#gsc_oci_title",
            ".gs_r.gs_or.gs_scl",
        ]:
            if await page.locator(f"{selector}:visible").count() > 0:
                visible_markers.append(selector)
        return {
            "url": page.url,
            "title": await page.title(),
            "visible_markers": visible_markers,
        }

    async def wait_for_add_articles_ui(page, timeout_seconds: int) -> None:
        deadline = asyncio.get_running_loop().time() + timeout_seconds
        add_articles_ready = False
        last_trace: tuple[str, str] | None = None
        while asyncio.get_running_loop().time() < deadline:
            has_input = await page.locator("#gsc_ia_ac:visible").count() > 0
            has_results = await page.locator("#gsc_ia_res:visible").count() > 0
            has_dialog = await page.locator("#gsc_md_iad").count() > 0
            if trace_navigation:
                trace = await trace_page_state(page)
                trace_key = (trace["url"], "|".join(trace["visible_markers"]))
                if trace_key != last_trace:
                    print("Trace:", trace)
                    last_trace = trace_key
            if has_input or has_results or has_dialog:
                add_articles_ready = True
                break
            await page.wait_for_timeout(1000)
        if not add_articles_ready:
            raise RuntimeError(
                "Timed out waiting for visible add-articles UI "
                "(#gsc_ia_ac, #gsc_ia_res, or #gsc_md_iad)."
            )

    async def page_markers(page) -> dict[str, bool]:
        return {
            "has_profile_table": await page.locator(".gsc_a_tr").count() > 0,
            "has_profile_name": await page.locator("#gsc_prf_in").count() > 0,
            "has_detail_title": await page.locator("#gsc_oci_title").count() > 0,
            "has_versions_results": await page.locator(".gs_r.gs_or.gs_scl").count() > 0,
            "has_add_articles_input": await page.locator("#gsc_ia_ac").count() > 0,
            "has_add_articles_results": await page.locator("#gsc_ia_res").count() > 0,
            "has_add_articles_dialog": await page.locator("#gsc_md_iad").count() > 0,
        }

    async def add_articles_dom_query(page) -> str:
        data = page.locator("#gsc_iadb_data")
        if await data.count() > 0:
            for attr in ("data-next", "data-prev"):
                value = await data.first.get_attribute(attr)
                query_text = extract_query_from_relative_url(value or "")
                if query_text:
                    return query_text
        if "#d=gsc_md_iad" in page.url and "&u=" in page.url:
            fragment = page.url.split("#", 1)[1]
            params = parse_qs(fragment)
            nested = unquote(params.get("u", [""])[0])
            return extract_query_from_relative_url(nested)
        return ""

    async def add_articles_doc_ids(page) -> tuple[str, ...]:
        inputs = page.locator(".gsc_iadb_art input[name='d']")
        count = await inputs.count()
        values = []
        for index in range(min(count, 10)):
            value = await inputs.nth(index).get_attribute("value")
            if value:
                values.append(value)
        return tuple(values)

    async def set_add_articles_query(page, query_text: str) -> None:
        input_locator = page.locator("#gsc_iads_tsi")
        if await input_locator.count() == 0:
            raise RuntimeError("Could not find Add Articles query input #gsc_iads_tsi.")
        await input_locator.first.evaluate(
            """(el, value) => {
                el.value = value;
                el.dispatchEvent(new Event("input", { bubbles: true }));
                el.dispatchEvent(new Event("change", { bubbles: true }));
            }""",
            query_text,
        )

    async def submit_add_articles_query(page, query_text: str, timeout_seconds: int) -> None:
        form_locator = page.locator("#gsc_iads_frm")
        if await form_locator.count() == 0:
            raise RuntimeError("Could not find Add Articles search form #gsc_iads_frm.")

        normalized_query = normalize_query_text(query_text)
        current_dom_query = await add_articles_dom_query(page)
        current_start = await add_articles_start(page)
        current_doc_ids = await add_articles_doc_ids(page)
        if should_reuse_existing_query_state(
            requested_query=normalized_query,
            current_query=current_dom_query,
            current_start=current_start,
            current_doc_ids=current_doc_ids,
        ):
            await set_add_articles_query(page, query_text)
            return

        previous_url = page.url
        previous_start = await add_articles_start(page)
        previous_dom_query = await add_articles_dom_query(page)
        previous_doc_ids = await add_articles_doc_ids(page)
        await set_add_articles_query(page, query_text)
        await form_locator.first.evaluate("(form) => form.requestSubmit()")

        deadline = asyncio.get_running_loop().time() + timeout_seconds
        while asyncio.get_running_loop().time() < deadline:
            await wait_for_add_articles_ui(page, 2)
            current_start = await add_articles_start(page)
            current_dom_query = await add_articles_dom_query(page)
            current_doc_ids = await add_articles_doc_ids(page)
            url_changed = page.url != previous_url
            start_changed = current_start != previous_start
            query_matches = current_dom_query == normalized_query
            doc_ids_changed = current_doc_ids != previous_doc_ids
            query_changed = current_dom_query != previous_dom_query
            if query_matches and (query_changed or doc_ids_changed or url_changed or start_changed):
                return
            await page.wait_for_timeout(500)
        raise RuntimeError(f"Timed out waiting for Add Articles results for query: {query_text}")

    async def rewind_add_articles_to_first_page(page, timeout_seconds: int, max_steps: int = 5) -> None:
        prev_button = page.locator("#gsc_iads_pp .gsc_pgn_ppr")
        if await prev_button.count() == 0:
            return

        steps = 0
        while steps < max_steps:
            current_start = await add_articles_start(page)
            if current_start in {"", "1"}:
                return
            if await prev_button.first.is_disabled():
                return
            await prev_button.first.click()
            deadline = asyncio.get_running_loop().time() + timeout_seconds
            while asyncio.get_running_loop().time() < deadline:
                await wait_for_add_articles_ui(page, 2)
                new_start = await add_articles_start(page)
                if new_start and new_start != current_start:
                    break
                await page.wait_for_timeout(500)
            steps += 1

        current_start = await add_articles_start(page)
        if current_start not in {"", "1"}:
            raise RuntimeError(
                "Could not rewind Add Articles results to page 1 within the bounded step limit."
            )

    async def capture_add_articles_sequence(
        page,
        *,
        query_label: str | None,
    ) -> None:
        capture_kind = "current page"
        if query_label:
            capture_kind = f'current page (add articles query "{query_label}" page 1)'
        await capture_page_artifacts(page, stem="current_page", capture_kind=capture_kind)
        if capture_add_articles_pages <= 1:
            return
        if not wait_for_add_articles:
            raise RuntimeError(
                "--capture-add-articles-pages requires --wait-for-add-articles "
                "so the script can verify the modal is present."
            )
        if not (cdp_url and use_existing_page):
            raise RuntimeError(
                "--capture-add-articles-pages requires --cdp-url and "
                "--use-existing-page to preserve the existing logged-in modal state."
            )
        for page_index in range(2, capture_add_articles_pages + 1):
            next_url = await next_add_articles_url(page)
            if not next_url:
                print(
                    "No further Add Articles page is available; "
                    f"stopping after {page_index - 1} page(s)."
                )
                break
            print(
                f"Waiting {between_pages_seconds} seconds before advancing "
                f"to Add Articles page {page_index}."
            )
            await page.wait_for_timeout(between_pages_seconds * 1000)
            advanced = await advance_add_articles_page(page, wait_seconds)
            if not advanced:
                print(
                    "Modal next-page click did not advance results; "
                    f"stopping after {page_index - 1} page(s)."
                )
                break
            print(f"Detected Add Articles page {page_index}; capturing.")
            capture_kind = f"current page (add articles page {page_index})"
            if query_label:
                capture_kind = (
                    f'current page (add articles query "{query_label}" page {page_index})'
                )
            await capture_page_artifacts(
                page,
                stem="current_page",
                capture_kind=capture_kind,
            )

    async def capture_page_artifacts(page, *, stem: str, capture_kind: str) -> dict[str, object]:
        artifact_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = artifact_dir / f"{stem}_{stamp}.png"
        html_path = artifact_dir / f"{stem}_{stamp}.html"
        metadata_path = artifact_dir / f"{stem}_{stamp}_capture.json"
        await page.screenshot(path=str(screenshot_path), full_page=True)
        html = await page.content()
        html_path.write_text(html)
        markers = await page_markers(page)
        metadata_path.write_text(
            json.dumps(
                {
                    "captured_url": page.url,
                    "page_title": await page.title(),
                    "capture_kind": capture_kind,
                    "markers": markers,
                },
                indent=2,
                sort_keys=True,
            )
        )
        print(f"Captured URL: {page.url}")
        print(f"Page title: {await page.title()}")
        print(f"Saved screenshot: {screenshot_path}")
        print(f"Saved HTML: {html_path}")
        print(f"Saved capture metadata: {metadata_path}")

        parsed_path = None
        if parse_add_articles and (
            markers["has_add_articles_input"]
            or markers["has_add_articles_results"]
            or markers["has_add_articles_dialog"]
        ):
            parsed_path = html_path.with_name(f"{html_path.stem}_add_articles.json")
            parsed_payload = parse_snapshot(html_path)
            parsed_path.write_text(json.dumps(parsed_payload, indent=2, sort_keys=True))
            print(f"Saved parsed Add Articles JSON: {parsed_path}")
            print(f"Candidate rows parsed: {parsed_payload['row_count']}")

        return {
            "screenshot_path": screenshot_path,
            "html_path": html_path,
            "metadata_path": metadata_path,
            "parsed_path": parsed_path,
            "markers": markers,
        }

    async def next_add_articles_url(page) -> str:
        data = page.locator("#gsc_iadb_data")
        if await data.count() == 0:
            return ""
        next_url = await data.first.get_attribute("data-next")
        if not next_url:
            return ""
        if "#d=gsc_md_iad" in page.url:
            base_url = page.url.split("#", 1)[0]
            return f"{base_url}#d=gsc_md_iad&u={quote(next_url, safe='')}"
        if next_url.startswith("http://") or next_url.startswith("https://"):
            return next_url
        return "https://scholar.google.com" + next_url

    async def add_articles_start(page) -> str:
        data = page.locator("#gsc_iadb_data")
        if await data.count() == 0:
            return ""
        return await data.first.get_attribute("data-start") or ""

    async def advance_add_articles_page(page, timeout_seconds: int) -> bool:
        next_button = page.locator("#gsc_iads_pp .gsc_pgn_pnx")
        if await next_button.count() == 0:
            return False
        disabled = await next_button.first.is_disabled()
        if disabled:
            return False

        previous_start = await add_articles_start(page)
        await next_button.first.evaluate("(button) => button.click()")
        deadline = asyncio.get_running_loop().time() + timeout_seconds
        while asyncio.get_running_loop().time() < deadline:
            await wait_for_add_articles_ui(page, 2)
            current_start = await add_articles_start(page)
            if current_start and current_start != previous_start:
                return True
            await page.wait_for_timeout(500)
        return False

    async def select_existing_page(context):
        if not use_existing_page or not context.pages:
            return None

        if wait_for_add_articles:
            for candidate in reversed(context.pages):
                markers = await page_markers(candidate)
                if (
                    markers["has_add_articles_input"]
                    or markers["has_add_articles_results"]
                    or markers["has_add_articles_dialog"]
                ):
                    print(
                        "Using an existing page with Add Articles markers:",
                        {
                            "url": candidate.url,
                            "title": await candidate.title(),
                            "markers": page_marker_summary(markers),
                        },
                    )
                    return candidate

        page = context.pages[-1]
        print("Using the most recently open page in the existing browser context.")
        return page

    async with async_playwright() as playwright:
        browser = None
        context = None
        if cdp_url:
            browser = await playwright.chromium.connect_over_cdp(cdp_url)
            if browser.contexts:
                context = browser.contexts[0]
            else:
                context = await browser.new_context()
            existing_page = await select_existing_page(context)
            if existing_page is not None:
                page = existing_page
            else:
                page = await context.new_page()
            print(f"Connected to existing browser over CDP: {cdp_url}")
        else:
            browser = await playwright.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
        if not (cdp_url and use_existing_page):
            await page.goto(target_url)
            if detail_url:
                print("Opened the requested Scholar detail page.")
            else:
                print("Opened your Scholar profile page.")
        else:
            print("Attached to the existing page without navigation.")
        print("Log in manually if Scholar prompts for authentication.")
        if search_url and not detail_url:
            await page.goto(search_url)
            print(f"Opened search results for query: {query}")
        if capture_profile or capture_detail or capture_current_page:
            if capture_detail:
                capture_kind = "detail page"
                stem = "detail_page"
            elif capture_profile:
                capture_kind = "profile page"
                stem = "profile_page"
            else:
                capture_kind = "current page"
                stem = "current_page"
            if wait_for_enter:
                print(
                    "Waiting for manual navigation. Press Enter in the controlling "
                    "terminal when the target Scholar page is visible."
                )
                enter_task = asyncio.create_task(asyncio.to_thread(sys.stdin.readline))
                last_trace: tuple[str, str] | None = None
                while not enter_task.done():
                    if trace_navigation:
                        trace = await trace_page_state(page)
                        trace_key = (trace["url"], "|".join(trace["visible_markers"]))
                        if trace_key != last_trace:
                            print("Trace:", trace)
                            last_trace = trace_key
                    await page.wait_for_timeout(1000)
                print("Received Enter; capturing current page.")
            else:
                print(
                    f"Waiting {wait_seconds} seconds for manual login / page settling "
                    f"before capturing a {capture_kind} screenshot and HTML snapshot."
                )
                if wait_for_add_articles:
                    await wait_for_add_articles_ui(page, wait_seconds)
                    print("Detected visible add-articles UI; capturing immediately.")
                else:
                    await page.wait_for_timeout(wait_seconds * 1000)
            if add_articles_queries:
                if not wait_for_add_articles:
                    raise RuntimeError(
                        "--add-articles-query requires --wait-for-add-articles."
                    )
                if not (cdp_url and use_existing_page):
                    raise RuntimeError(
                        "--add-articles-query requires --cdp-url and --use-existing-page."
                    )
                for query_index, add_articles_query in enumerate(add_articles_queries, start=1):
                    if query_index > 1:
                        print(
                            f"Waiting {between_queries_seconds} seconds before starting "
                            f'query {query_index}: "{add_articles_query}"'
                        )
                        await page.wait_for_timeout(between_queries_seconds * 1000)
                    else:
                        print(f'Starting Add Articles query 1: "{add_articles_query}"')
                    await submit_add_articles_query(page, add_articles_query, wait_seconds)
                    await rewind_add_articles_to_first_page(page, wait_seconds)
                    print(f'Add Articles results loaded for query: "{add_articles_query}"')
                    await capture_add_articles_sequence(page, query_label=add_articles_query)
            else:
                await capture_add_articles_sequence(
                    page,
                    query_label=query if wait_for_add_articles else None,
                )
            await page.wait_for_timeout(5000)
        else:
            print("This script is read-only. Close the browser window when done.")
            await page.wait_for_timeout(30000)
        await browser.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", help="Optional Scholar search query to inspect")
    parser.add_argument(
        "--add-articles-query",
        action="append",
        dest="add_articles_queries",
        default=[],
        help=(
            "Curated Add Articles query to run in the already-open modal. "
            "Repeat this flag for multiple queries."
        ),
    )
    parser.add_argument(
        "--capture-profile",
        action="store_true",
        help="After a manual-login wait, save a profile screenshot and HTML snapshot.",
    )
    parser.add_argument(
        "--detail-url",
        help="Optional Scholar detail page URL to open instead of the profile page.",
    )
    parser.add_argument(
        "--capture-detail",
        action="store_true",
        help="After a manual-login wait, save a detail-page screenshot and HTML snapshot.",
    )
    parser.add_argument(
        "--capture-current-page",
        action="store_true",
        help="After a manual-login wait, capture whatever Scholar page is currently open.",
    )
    parser.add_argument(
        "--wait-for-add-articles",
        action="store_true",
        help=(
            "Require a visible add-articles UI before capturing; fails if "
            "Scholar never shows #gsc_ia_ac or #gsc_ia_res within the wait window."
        ),
    )
    parser.add_argument(
        "--trace-navigation",
        action="store_true",
        help="While waiting, print URL/title/visible Scholar containers when they change.",
    )
    parser.add_argument(
        "--wait-for-enter",
        action="store_true",
        help="Keep the browser open until Enter is sent on stdin, then capture the current page.",
    )
    parser.add_argument(
        "--wait-seconds",
        type=int,
        default=45,
        help="How long to wait for manual login / page settling before capture.",
    )
    parser.add_argument(
        "--artifact-dir",
        type=Path,
        default=default_artifact_dir(),
        help="Directory where screenshots and HTML snapshots should be written.",
    )
    parser.add_argument(
        "--cdp-url",
        help=(
            "Optional Chrome DevTools URL, for example http://127.0.0.1:9222. "
            "Use this to attach to a browser you launched yourself."
        ),
    )
    parser.add_argument(
        "--use-existing-page",
        action="store_true",
        help="When attaching over CDP, use the most recently open existing page instead of opening a new tab.",
    )
    parser.add_argument(
        "--parse-add-articles",
        action="store_true",
        help="When the captured page is an Add Articles modal, also write parsed *_add_articles.json output.",
    )
    parser.add_argument(
        "--capture-add-articles-pages",
        type=int,
        default=1,
        help=(
            "Capture the current Add Articles page plus up to N-1 additional pages via "
            "the modal's data-next URL. Requires --cdp-url, --use-existing-page, and "
            "--wait-for-add-articles."
        ),
    )
    parser.add_argument(
        "--between-pages-seconds",
        type=int,
        default=8,
        help="Delay between bounded Add Articles page loads.",
    )
    parser.add_argument(
        "--between-queries-seconds",
        type=int,
        default=12,
        help="Delay between curated Add Articles queries.",
    )
    args = parser.parse_args()
    if args.capture_add_articles_pages < 1:
        parser.error("--capture-add-articles-pages must be at least 1")
    if args.capture_add_articles_pages > 3:
        parser.error("--capture-add-articles-pages must not exceed 3 during investigation")
    if len(args.add_articles_queries) > 3:
        parser.error("--add-articles-query must not be provided more than 3 times during investigation")
    asyncio.run(
        run(
            args.query,
            args.add_articles_queries,
            capture_profile=args.capture_profile,
            detail_url=args.detail_url,
            capture_detail=args.capture_detail,
            capture_current_page=args.capture_current_page,
            wait_for_add_articles=args.wait_for_add_articles,
            trace_navigation=args.trace_navigation,
            wait_for_enter=args.wait_for_enter,
            wait_seconds=args.wait_seconds,
            artifact_dir=args.artifact_dir,
            cdp_url=args.cdp_url,
            use_existing_page=args.use_existing_page,
            parse_add_articles=args.parse_add_articles,
            capture_add_articles_pages=args.capture_add_articles_pages,
            between_pages_seconds=args.between_pages_seconds,
            between_queries_seconds=args.between_queries_seconds,
        )
    )


if __name__ == "__main__":
    main()
