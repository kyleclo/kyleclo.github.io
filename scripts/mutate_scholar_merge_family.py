# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "playwright",
# ]
# ///
"""
Bounded Google Scholar profile merge helper.

This script intentionally mirrors the add-phase safety posture:
- it attaches to an already-open logged-in Scholar session over CDP
- it only acts on one reviewed profile family at a time
- it requires an explicit confirmation phrase before clicking Merge
- it captures pre/post evidence so the merge attempt can be reviewed
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
from scripts.parse_scholar_add_articles_snapshot import normalize_space


def normalize_title_text(text: str) -> str:
    return normalize_space(text).casefold()


def parse_target_spec(spec: str) -> dict[str, str]:
    row_id, separator, expected_title = spec.partition("::")
    row_id = normalize_space(row_id)
    expected_title = normalize_space(expected_title)
    if not separator:
        raise ValueError(
            'Target must use the form "<row-id>::<expected title>".'
        )
    if not row_id:
        raise ValueError("Target row id cannot be empty.")
    if not expected_title:
        raise ValueError("Target expected title cannot be empty.")
    return {"row_id": row_id, "expected_title": expected_title}


def build_confirmation_phrase(row_ids: list[str]) -> str:
    normalized_ids = [normalize_space(row_id) for row_id in row_ids if normalize_space(row_id)]
    if len(normalized_ids) < 2:
        raise ValueError("Merge confirmation requires at least two reviewed row ids.")
    return "MERGE " + " ".join(sorted(normalized_ids))


def row_matches_expected_title(row_title: str, expected_title: str) -> bool:
    return normalize_title_text(row_title) == normalize_title_text(expected_title)


def choose_target_rows(rows: list[dict], reviewed_targets: list[dict]) -> list[dict]:
    if len(reviewed_targets) < 2:
        raise RuntimeError("At least two reviewed targets are required for a bounded merge family.")

    chosen_rows = []
    seen_row_ids = set()
    for target in reviewed_targets:
        row_id = target["row_id"]
        expected_title = target["expected_title"]
        matches = [row for row in rows if row.get("row_id") == row_id]
        if not matches:
            raise RuntimeError(f"Could not find a visible Scholar profile row with row_id={row_id}.")
        if len(matches) != 1:
            raise RuntimeError(
                f"Expected exactly one visible Scholar profile row for row_id={row_id}; found {len(matches)}."
            )
        match = matches[0]
        if not row_matches_expected_title(match.get("title", ""), expected_title):
            raise RuntimeError(
                "The visible Scholar profile row matched the requested row id but not the expected title."
            )
        if row_id in seen_row_ids:
            raise RuntimeError(f"Duplicate reviewed row id requested: {row_id}.")
        seen_row_ids.add(row_id)
        chosen_rows.append(match)
    return chosen_rows


def choose_merge_action(actions: list[dict]) -> dict:
    primary_matches = [
        action
        for action in actions
        if action.get("id") == "gsc_btn_mer" and not action.get("hidden") and not action.get("disabled")
    ]
    if len(primary_matches) == 1:
        return primary_matches[0]
    if len(primary_matches) > 1:
        raise RuntimeError(
            f"Expected exactly one visible enabled primary Merge action; found {len(primary_matches)}."
        )
    raise RuntimeError("The expected visible primary Merge action is not present.")


def choose_confirmation_merge_action(actions: list[dict]) -> dict | None:
    matches = []
    for action in actions:
        if action.get("id") != "gsc_md_mopt_merge":
            continue
        if action.get("hidden") or action.get("disabled"):
            continue
        matches.append(action)
    if not matches:
        return None
    if len(matches) != 1:
        raise RuntimeError(
            f"Expected exactly one visible enabled confirmation Merge action; found {len(matches)}."
        )
    return matches[0]


def format_visible_rows(rows: list[dict], *, limit: int | None = None) -> str:
    visible_rows = rows[:limit] if limit is not None else rows
    if not visible_rows:
        return "No visible Scholar profile rows found."

    lines = []
    for index, row in enumerate(visible_rows, start=1):
        lines.append(
            f"{index}. {row.get('title', '')} "
            f"(row_id={row.get('row_id', '')}, citations={row.get('citations', '')}, year={row.get('year', '')})"
        )
    return "\n".join(lines)


def filter_rows_by_title(rows: list[dict], title_filter: str | None) -> list[dict]:
    if not title_filter:
        return rows
    needle = normalize_title_text(title_filter)
    return [row for row in rows if needle in normalize_title_text(row.get("title", ""))]


def selector_for_id(tag: str, value: str) -> str:
    return f'{tag}[id="{value}"]'


def format_visible_actions(actions: list[dict]) -> str:
    if not actions:
        return "No visible profile actions found."
    lines = []
    for index, action in enumerate(actions, start=1):
        disabled = "disabled" if action.get("disabled") else "enabled"
        hidden = "hidden" if action.get("hidden") else "visible"
        lines.append(
            f"{index}. {action.get('text', '')} "
            f"(tag={action.get('tag', '')}, id={action.get('id', '')}, {hidden}, {disabled})"
        )
    return "\n".join(lines)


async def run(
    *,
    cdp_url: str,
    targets: list[str],
    confirm: str | None,
    execute: bool,
    list_visible_rows: bool,
    visible_row_limit: int,
    visible_row_title_filter: str | None,
    list_visible_actions: bool,
    artifact_dir: Path,
    wait_seconds: int,
) -> dict:
    from playwright.async_api import async_playwright

    reviewed_targets = [parse_target_spec(spec) for spec in targets]

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
                    checkbox_id: checkbox ? (checkbox.id || "") : "",
                    disabled: checkbox ? checkbox.disabled : true,
                    checked: checkbox ? checkbox.checked : false,
                    title: titleLink ? (titleLink.textContent || "").trim() : "",
                    citations: citationCell ? (citationCell.textContent || "").trim() : "",
                    year: yearCell ? (yearCell.textContent || "").trim() : "",
                };
            })"""
        )

    async def visible_actions(page) -> list[dict]:
        return await page.evaluate(
            """() => {
                const ids = [
                    "gsc_btn_mer",
                    "gsc_btn_del",
                    "gsc_dd_exp-b",
                    "gsc_dd_mor-b",
                    "gsc_dd_add-b",
                    "gsc_bpf_more",
                    "gsc_md_mopt_merge",
                    "gsc_md_mopt_cancel",
                    "gsc_md_cbyd_merge",
                ];
                return ids
                    .map((id) => document.getElementById(id))
                    .filter((node) => node)
                    .map((node) => {
                        const style = window.getComputedStyle(node);
                        const rect = node.getBoundingClientRect();
                        const text = (node.textContent || "").trim();
                        const disabled = node.disabled === true || node.getAttribute("aria-disabled") === "true";
                        const hidden =
                            style.display === "none" ||
                            style.visibility === "hidden" ||
                            rect.width === 0 ||
                            rect.height === 0;
                        return {
                            id: node.id || "",
                            text,
                            disabled,
                            hidden,
                            tag: node.tagName.toLowerCase(),
                        };
                    })
                    .filter((node) => node.text || node.id);
            }"""
        )

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
        return {
            "screenshot_path": screenshot_path,
            "html_path": html_path,
            "metadata_path": metadata_path,
        }

    async def ensure_rows_selected(page, selected_rows: list[dict]) -> None:
        for row in selected_rows:
            checkbox_id = row.get("checkbox_id", "")
            if not checkbox_id:
                raise RuntimeError(
                    f"Reviewed row_id={row.get('row_id', '')} does not expose a checkbox id; refusing to mutate."
                )
            checkbox = page.locator(selector_for_id("input", checkbox_id))
            if await checkbox.count() == 0:
                raise RuntimeError(f"Could not find checkbox #{checkbox_id} for the reviewed row.")
            if await checkbox.first.is_disabled():
                raise RuntimeError(f"Checkbox #{checkbox_id} is disabled; refusing to mutate.")
            if not await checkbox.first.is_checked():
                await checkbox.first.evaluate("(node) => node.click()")

    async def click_merge_action(page, action: dict) -> None:
        action_id = action.get("id", "")
        if action_id:
            locator = page.locator(selector_for_id(action.get("tag", "button"), action_id))
            if await locator.count() > 0:
                await locator.first.evaluate("(node) => node.click()")
                return
        fallback = page.get_by_role("button", name="Merge")
        if await fallback.count() > 0:
            await fallback.first.evaluate("(node) => node.click()")
            return
        fallback_link = page.get_by_role("link", name="Merge")
        if await fallback_link.count() > 0:
            await fallback_link.first.evaluate("(node) => node.click()")
            return
        raise RuntimeError("Could not click the previously discovered Merge action.")

    async def maybe_confirm_merge_modal(page) -> bool:
        actions = await visible_actions(page)
        confirmation_action = choose_confirmation_merge_action(actions)
        if confirmation_action is None:
            return False
        await click_merge_action(page, confirmation_action)
        return True

    async def dismiss_stale_merge_modal(page) -> bool:
        actions = await visible_actions(page)
        cancel_actions = [
            action
            for action in actions
            if action.get("id") == "gsc_md_mopt_cancel" and not action.get("hidden") and not action.get("disabled")
        ]
        if not cancel_actions:
            return False
        if len(cancel_actions) != 1:
            raise RuntimeError(
                f"Expected exactly one visible enabled merge-cancel action; found {len(cancel_actions)}."
            )
        await click_merge_action(page, cancel_actions[0])
        deadline = asyncio.get_running_loop().time() + wait_seconds
        while asyncio.get_running_loop().time() < deadline:
            actions = await visible_actions(page)
            if choose_confirmation_merge_action(actions) is None:
                return True
            await page.wait_for_timeout(250)
        raise RuntimeError("Timed out waiting for the stale merge confirmation modal to close.")

    async def wait_for_post_merge_change(page, original_rows: list[dict]) -> list[dict]:
        original_checked = tuple(row.get("checked") for row in original_rows)
        original_ids = tuple(row.get("row_id", "") for row in original_rows)
        deadline = asyncio.get_running_loop().time() + wait_seconds
        confirmation_clicked = False
        while asyncio.get_running_loop().time() < deadline:
            await wait_for_profile_page(page, 2)
            rows = await profile_rows(page)
            current_ids = tuple(row.get("row_id", "") for row in rows)
            if current_ids != original_ids:
                return rows
            current_checked = tuple(row.get("checked") for row in rows[: len(original_checked)])
            if current_checked != original_checked:
                return rows
            if not confirmation_clicked and await maybe_confirm_merge_modal(page):
                confirmation_clicked = True
            await page.wait_for_timeout(500)
        raise RuntimeError("Timed out waiting for an observable profile-table change after clicking Merge.")

    async with async_playwright() as playwright:
        browser = await playwright.chromium.connect_over_cdp(cdp_url)
        if browser.contexts:
            context = browser.contexts[0]
        else:
            context = await browser.new_context()
        page = await select_existing_page(context)
        await wait_for_profile_page(page, wait_seconds)
        await dismiss_stale_merge_modal(page)

        rows = await profile_rows(page)
        if list_visible_rows:
            output = format_visible_rows(
                filter_rows_by_title(rows, visible_row_title_filter),
                limit=visible_row_limit,
            )
            print(output)
            await browser.close()
            return {"mode": "list_visible_rows", "output": output}

        expected_confirmation = build_confirmation_phrase([target["row_id"] for target in reviewed_targets])
        if execute and confirm != expected_confirmation:
            raise RuntimeError(
                f'Explicit confirmation mismatch. Re-run with --confirm "{expected_confirmation}".'
            )

        pre_artifacts = await capture_page_artifacts(
            page,
            stem="merge_pre",
            capture_kind="pre-mutation merge family review",
        )
        target_rows = choose_target_rows(rows, reviewed_targets)
        await ensure_rows_selected(page, target_rows)
        actions = await visible_actions(page)
        if list_visible_actions:
            output = format_visible_actions(actions)
            print(output)
            await browser.close()
            return {"mode": "list_visible_actions", "output": output}
        merge_action = choose_merge_action(actions)

        summary = {
            "reviewed_rows": [
                {
                    "row_id": row.get("row_id", ""),
                    "title": row.get("title", ""),
                    "citations": row.get("citations", ""),
                    "year": row.get("year", ""),
                    "checkbox_id": row.get("checkbox_id", ""),
                }
                for row in target_rows
            ],
            "merge_action": merge_action,
            "pre_artifacts": {key: str(value) for key, value in pre_artifacts.items()},
        }
        print(json.dumps(summary, indent=2, sort_keys=True))

        if not execute:
            print("")
            print("Dry run only. No mutation was performed.")
            print(f'If this reviewed family is correct, rerun with: --execute --confirm "{expected_confirmation}"')
            await browser.close()
            return {
                "mode": "dry_run",
                "summary": summary,
                "expected_confirmation": expected_confirmation,
            }

        await click_merge_action(page, merge_action)
        post_rows = await wait_for_post_merge_change(page, rows)
        post_artifacts = await capture_page_artifacts(
            page,
            stem="merge_post",
            capture_kind="post-mutation merge family review",
        )
        outcome = {
            "post_visible_row_count": len(post_rows),
            "post_artifacts": {key: str(value) for key, value in post_artifacts.items()},
        }
        print("")
        print(json.dumps(outcome, indent=2, sort_keys=True))
        await browser.close()
        return {
            "mode": "execute",
            "summary": summary,
            "outcome": outcome,
            "expected_confirmation": expected_confirmation,
        }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cdp-url", required=True, help="Chrome DevTools URL for an already-open logged-in browser.")
    parser.add_argument(
        "--target",
        action="append",
        help='Reviewed profile target in the form "<row-id>::<expected title>". Repeat for each row in the merge family.',
    )
    parser.add_argument(
        "--list-visible-rows",
        action="store_true",
        help="Read-only mode. Print the currently visible Scholar profile row ids/titles and exit.",
    )
    parser.add_argument(
        "--visible-row-limit",
        type=int,
        default=20,
        help="Maximum number of visible rows to print with --list-visible-rows.",
    )
    parser.add_argument(
        "--visible-row-title-filter",
        help="Optional case-insensitive title substring filter for --list-visible-rows.",
    )
    parser.add_argument(
        "--list-visible-actions",
        action="store_true",
        help="Read-only mode after selecting the reviewed rows. Print visible profile actions and exit.",
    )
    parser.add_argument(
        "--confirm",
        help='Explicit confirmation phrase. Must exactly match "MERGE <sorted row ids...>" when --execute is used.',
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually click the Merge action after target verification.",
    )
    parser.add_argument(
        "--artifact-dir",
        type=Path,
        default=default_artifact_dir(),
        help="Directory where pre/post merge evidence snapshots should be written.",
    )
    parser.add_argument(
        "--wait-seconds",
        type=int,
        default=20,
        help="How long to wait for profile readiness and post-click changes.",
    )
    args = parser.parse_args()
    if not args.list_visible_rows and not args.target:
        parser.error("the following arguments are required: --target (unless --list-visible-rows is used)")
    asyncio.run(
        run(
            cdp_url=args.cdp_url,
            targets=args.target or [],
            confirm=args.confirm,
            execute=args.execute,
            list_visible_rows=args.list_visible_rows,
            visible_row_limit=args.visible_row_limit,
            visible_row_title_filter=args.visible_row_title_filter,
            list_visible_actions=args.list_visible_actions,
            artifact_dir=args.artifact_dir,
            wait_seconds=args.wait_seconds,
        )
    )


if __name__ == "__main__":
    main()
