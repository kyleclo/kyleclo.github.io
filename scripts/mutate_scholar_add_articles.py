# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "playwright",
# ]
# ///
"""
Bounded Google Scholar Add Articles mutation helper.

This script is intentionally narrow:
- it attaches to an already-open logged-in Scholar session over CDP
- it only acts on one reviewed Add Articles candidate at a time
- it requires an explicit confirmation phrase before clicking Add
- it captures pre/post evidence so the mutation outcome can be reviewed
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.investigate_scholar_ui import default_artifact_dir
from scripts.parse_scholar_add_articles_snapshot import parse_snapshot
from scripts.parse_scholar_add_articles_snapshot import normalize_space


def normalize_title_text(text: str) -> str:
    return normalize_space(text).casefold()


def build_confirmation_phrase(doc_id: str) -> str:
    return f"ADD {doc_id}"


def row_matches_expected_title(row_title: str, expected_title: str | None) -> bool:
    if not expected_title:
        return True
    return normalize_title_text(row_title) == normalize_title_text(expected_title)


def choose_target_row(rows: list[dict], doc_id: str, expected_title: str | None) -> dict:
    matches = [row for row in rows if row.get("doc_id") == doc_id]
    if not matches:
        raise RuntimeError(f"Could not find a visible Add Articles row with doc_id={doc_id}.")
    if expected_title:
        matches = [
            row for row in matches if row_matches_expected_title(row.get("title", ""), expected_title)
        ]
        if not matches:
            raise RuntimeError(
                "The visible Add Articles row matched the requested doc_id but not the expected title."
            )
    if len(matches) != 1:
        raise RuntimeError(
            f"Expected exactly one visible Add Articles row for doc_id={doc_id}; found {len(matches)}."
        )
    return matches[0]


async def run(
    *,
    cdp_url: str,
    doc_id: str,
    title: str | None,
    query: str | None,
    target_start: str | None,
    confirm: str | None,
    execute: bool,
    artifact_dir: Path,
    wait_seconds: int,
) -> None:
    from playwright.async_api import async_playwright

    async def page_markers(page) -> dict[str, bool]:
        return {
            "has_add_articles_input": await page.locator("#gsc_ia_ac").count() > 0,
            "has_add_articles_results": await page.locator("#gsc_ia_res").count() > 0,
            "has_add_articles_dialog": await page.locator("#gsc_md_iad").count() > 0,
        }

    async def wait_for_add_articles_ui(page, timeout_seconds: int) -> None:
        deadline = asyncio.get_running_loop().time() + timeout_seconds
        while asyncio.get_running_loop().time() < deadline:
            markers = await page_markers(page)
            if any(markers.values()):
                return
            await page.wait_for_timeout(500)
        raise RuntimeError(
            "Timed out waiting for visible Add Articles UI (#gsc_ia_ac, #gsc_ia_res, or #gsc_md_iad)."
        )

    async def wait_for_profile_page(page, timeout_seconds: int) -> None:
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
            markers = await page_markers(candidate)
            if any(markers.values()):
                return candidate
        return context.pages[-1] if context.pages else await context.new_page()

    async def add_articles_rows(page) -> list[dict]:
        return await page.locator(".gsc_iadb_art").evaluate_all(
            """(rows) => rows.map((row) => {
                const checkbox = row.querySelector("input[name='d']");
                const titleLink = row.querySelector("a[href*='view_op=view_citation'], a[href*='oi=bibs']");
                const meta = row.querySelector(".gs_gray");
                const status = row.querySelector(".gsc_iadb_art_added");
                return {
                    doc_id: checkbox ? checkbox.value || "" : "",
                    checkbox_id: checkbox ? checkbox.id || "" : "",
                    disabled: checkbox ? checkbox.disabled : true,
                    checked: checkbox ? checkbox.checked : false,
                    title: titleLink ? (titleLink.textContent || "").trim() : "",
                    authors_venue: meta ? (meta.textContent || "").trim() : "",
                    status_label: status ? (status.textContent || "").trim() : "",
                    in_profile: status ? ((status.textContent || "").trim().toLowerCase() === "in profile") : false,
                };
            })"""
        )

    async def add_articles_search_query(page) -> str:
        input_locator = page.locator("#gsc_iads_tsi")
        if await input_locator.count() == 0:
            return ""
        value = await input_locator.first.input_value()
        return normalize_space(value)

    async def add_articles_start(page) -> str:
        data = page.locator("#gsc_iadb_data")
        if await data.count() == 0:
            return ""
        return await data.first.get_attribute("data-start") or ""

    async def capture_page_artifacts(page, *, stem: str, capture_kind: str) -> dict[str, Path]:
        artifact_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = artifact_dir / f"{stem}_{stamp}.png"
        html_path = artifact_dir / f"{stem}_{stamp}.html"
        metadata_path = artifact_dir / f"{stem}_{stamp}_capture.json"
        await page.screenshot(path=str(screenshot_path), full_page=True)
        html_path.write_text(await page.content())
        metadata_path.write_text(
            json.dumps(
                {
                    "captured_url": page.url,
                    "page_title": await page.title(),
                    "capture_kind": capture_kind,
                },
                indent=2,
                sort_keys=True,
            )
        )
        if any((await page_markers(page)).values()):
            parsed_path = html_path.with_name(f"{html_path.stem}_add_articles.json")
            parsed_path.write_text(json.dumps(parse_snapshot(html_path), indent=2, sort_keys=True))
        return {
            "screenshot_path": screenshot_path,
            "html_path": html_path,
            "metadata_path": metadata_path,
        }

    async def ensure_candidate_selected(page, checkbox_id: str) -> None:
        checkbox = page.locator(f"#{checkbox_id}")
        if await checkbox.count() == 0:
            raise RuntimeError(f"Could not find checkbox #{checkbox_id} for the reviewed candidate.")
        if await checkbox.first.is_disabled():
            raise RuntimeError(f"Checkbox #{checkbox_id} is disabled; refusing to mutate.")
        if not await checkbox.first.is_checked():
            await checkbox.first.evaluate("(node) => node.click()")

    async def open_add_articles_modal_from_profile(page, query_text: str) -> None:
        await wait_for_profile_page(page, wait_seconds)
        close_button = page.locator("#gsc_md_iad-x")
        if await close_button.count() > 0:
            modal_root = page.locator("#gsc_md_iad")
            modal_classes = await modal_root.first.get_attribute("class") if await modal_root.count() > 0 else ""
            if modal_classes and "gs_vis" in modal_classes.split():
                await close_button.first.evaluate("(button) => button.click()")
                deadline = asyncio.get_running_loop().time() + wait_seconds
                while asyncio.get_running_loop().time() < deadline:
                    modal_classes = await modal_root.first.get_attribute("class") if await modal_root.count() > 0 else ""
                    if not modal_classes or "gs_vis" not in modal_classes.split():
                        break
                    await page.wait_for_timeout(250)
        add_dropdown = page.locator("#gsc_dd_add-b")
        if await add_dropdown.count() == 0:
            raise RuntimeError("Could not find the profile-page Add control #gsc_dd_add-b.")
        await add_dropdown.first.evaluate("(button) => button.click()")
        menu_item = page.locator("#gsc_dd_add-d a.gs_md_li").filter(has_text="Add articles")
        if await menu_item.count() == 0:
            raise RuntimeError("Could not find the Add articles menu item in the profile menu.")
        await menu_item.first.click()
        await wait_for_add_articles_ui(page, wait_seconds)
        input_locator = page.locator("#gsc_iads_tsi")
        if await input_locator.count() == 0:
            raise RuntimeError("Could not find Add Articles query input after opening the modal.")
        await input_locator.first.evaluate(
            """(el, value) => {
                el.value = value;
                el.dispatchEvent(new Event("input", { bubbles: true }));
                el.dispatchEvent(new Event("change", { bubbles: true }));
            }""",
            query_text,
        )
        form_locator = page.locator("#gsc_iads_frm")
        if await form_locator.count() == 0:
            raise RuntimeError("Could not find Add Articles form after opening the modal.")
        previous_doc_ids = tuple(row.get("doc_id", "") for row in await add_articles_rows(page))
        await form_locator.first.evaluate("(form) => form.requestSubmit()")
        deadline = asyncio.get_running_loop().time() + wait_seconds
        normalized_query = normalize_space(query_text)
        while asyncio.get_running_loop().time() < deadline:
            await wait_for_add_articles_ui(page, 2)
            current_query = await add_articles_search_query(page)
            rows = await add_articles_rows(page)
            current_doc_ids = tuple(row.get("doc_id", "") for row in rows)
            if current_query == normalized_query and current_doc_ids != previous_doc_ids:
                return
            await page.wait_for_timeout(500)
        raise RuntimeError(f'Timed out waiting for Add Articles results for query "{query_text}".')

    async def click_add_button(page) -> None:
        add_button = page.locator("#gsc_iad_add")
        if await add_button.count() == 0:
            raise RuntimeError("Could not find the Add button #gsc_iad_add.")
        deadline = asyncio.get_running_loop().time() + wait_seconds
        while asyncio.get_running_loop().time() < deadline:
            if not await add_button.first.is_disabled():
                await add_button.first.evaluate("(button) => button.click()")
                return
            await page.wait_for_timeout(250)
        raise RuntimeError("The Add button stayed disabled after selecting the candidate.")

    async def advance_add_articles_page(page) -> bool:
        next_button = page.locator("#gsc_iads_pp .gsc_pgn_pnx")
        if await next_button.count() == 0:
            return False
        if await next_button.first.is_disabled():
            return False
        previous_start = await add_articles_start(page)
        await next_button.first.evaluate("(button) => button.click()")
        deadline = asyncio.get_running_loop().time() + wait_seconds
        while asyncio.get_running_loop().time() < deadline:
            await wait_for_add_articles_ui(page, 2)
            current_start = await add_articles_start(page)
            if current_start and current_start != previous_start:
                return True
            await page.wait_for_timeout(250)
        return False

    async def page_to_add_articles_start(page, desired_start: str) -> None:
        current_start = await add_articles_start(page)
        if current_start == desired_start:
            return
        max_steps = 20
        for _ in range(max_steps):
            advanced = await advance_add_articles_page(page)
            if not advanced:
                break
            current_start = await add_articles_start(page)
            if current_start == desired_start:
                return
        raise RuntimeError(
            f"Could not reach Add Articles start={desired_start} within the bounded page limit."
        )

    async def wait_for_post_add_change(page, original_rows: list[dict]) -> tuple[dict | None, list[dict]]:
        original_doc_ids = tuple(row.get("doc_id", "") for row in original_rows)
        deadline = asyncio.get_running_loop().time() + wait_seconds
        while asyncio.get_running_loop().time() < deadline:
            await wait_for_add_articles_ui(page, 2)
            rows = await add_articles_rows(page)
            current_doc_ids = tuple(row.get("doc_id", "") for row in rows)
            target_row = next((row for row in rows if row.get("doc_id") == doc_id), None)
            if current_doc_ids != original_doc_ids:
                return target_row, rows
            if target_row is None:
                return None, rows
            if target_row.get("in_profile"):
                return target_row, rows
            await page.wait_for_timeout(500)
        raise RuntimeError(
            "Timed out waiting for an observable Add Articles queue change after clicking Add."
        )

    expected_confirmation = build_confirmation_phrase(doc_id)
    if execute and confirm != expected_confirmation:
        raise RuntimeError(
            f'Explicit confirmation mismatch. Re-run with --confirm "{expected_confirmation}".'
        )

    async with async_playwright() as playwright:
        browser = await playwright.chromium.connect_over_cdp(cdp_url)
        if browser.contexts:
            context = browser.contexts[0]
        else:
            context = await browser.new_context()
        page = await select_existing_page(context)
        if query:
            await open_add_articles_modal_from_profile(page, query)
        else:
            await wait_for_add_articles_ui(page, wait_seconds)
        if target_start:
            await page_to_add_articles_start(page, target_start)

        pre_artifacts = await capture_page_artifacts(
            page,
            stem="mutation_pre",
            capture_kind=f"pre-mutation add articles review for {doc_id}",
        )
        rows = await add_articles_rows(page)
        target_row = choose_target_row(rows, doc_id, title)
        summary = {
            "doc_id": target_row.get("doc_id", ""),
            "title": target_row.get("title", ""),
            "authors_venue": target_row.get("authors_venue", ""),
            "status_label": target_row.get("status_label", ""),
            "checkbox_id": target_row.get("checkbox_id", ""),
            "pre_artifacts": {key: str(value) for key, value in pre_artifacts.items()},
        }
        print(json.dumps(summary, indent=2, sort_keys=True))

        if target_row.get("in_profile"):
            raise RuntimeError(f"doc_id={doc_id} is already marked in profile; refusing to mutate.")
        if target_row.get("disabled"):
            raise RuntimeError(f"doc_id={doc_id} is disabled in the current modal; refusing to mutate.")
        if not target_row.get("checkbox_id"):
            raise RuntimeError(f"doc_id={doc_id} does not expose a checkbox id; refusing to mutate.")

        if not execute:
            print("")
            print("Dry run only. No mutation was performed.")
            print(f'If this reviewed row is correct, rerun with: --execute --confirm "{expected_confirmation}"')
            await browser.close()
            return

        await ensure_candidate_selected(page, target_row["checkbox_id"])
        await click_add_button(page)
        post_row, post_rows = await wait_for_post_add_change(page, rows)
        post_artifacts = await capture_page_artifacts(
            page,
            stem="mutation_post",
            capture_kind=f"post-mutation add articles review for {doc_id}",
        )
        outcome = {
            "doc_id": doc_id,
            "post_target_present": post_row is not None,
            "post_target_in_profile": bool(post_row and post_row.get("in_profile")),
            "visible_row_count_after": len(post_rows),
            "post_artifacts": {key: str(value) for key, value in post_artifacts.items()},
        }
        print("")
        print(json.dumps(outcome, indent=2, sort_keys=True))
        await browser.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cdp-url", required=True, help="Chrome DevTools URL for an already-open logged-in browser.")
    parser.add_argument("--doc-id", required=True, help="Reviewed Scholar Add Articles doc_id to act on.")
    parser.add_argument("--title", help="Optional exact title check for the reviewed row.")
    parser.add_argument(
        "--query",
        help="Optional Add Articles query to open from the profile page before verifying or mutating.",
    )
    parser.add_argument(
        "--target-start",
        help="Optional Add Articles result-page start offset to reach via bounded DOM pagination.",
    )
    parser.add_argument(
        "--confirm",
        help='Explicit confirmation phrase. Must exactly match "ADD <doc_id>" when --execute is used.',
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually click the Add button after candidate verification.",
    )
    parser.add_argument(
        "--artifact-dir",
        type=Path,
        default=default_artifact_dir(),
        help="Directory where pre/post mutation evidence snapshots should be written.",
    )
    parser.add_argument(
        "--wait-seconds",
        type=int,
        default=20,
        help="How long to wait for the modal and post-click queue change.",
    )
    args = parser.parse_args()
    asyncio.run(
        run(
            cdp_url=args.cdp_url,
            doc_id=args.doc_id,
            title=args.title,
            query=args.query,
            target_start=args.target_start,
            confirm=args.confirm,
            execute=args.execute,
            artifact_dir=args.artifact_dir,
            wait_seconds=args.wait_seconds,
        )
    )


if __name__ == "__main__":
    main()
