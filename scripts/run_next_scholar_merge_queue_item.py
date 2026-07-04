# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "playwright",
# ]
# ///
"""
Execute exactly one approved Scholar merge queue item.
"""

from __future__ import annotations

import argparse
import asyncio
import re
import traceback
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.mutate_scholar_merge_family import build_confirmation_phrase, run as run_merge_family
from scripts.scholar_merge_queue import (
    default_merge_queue_path,
    format_merge_queue_item,
    load_merge_queue,
    save_merge_queue,
    select_approved_items,
    update_queue_item_result,
    update_queue_item_verification,
    summarize_verification_output,
)


def build_verification_filter(item: dict) -> str:
    family_label = item.get("family_label", "")
    words = re.findall(r"[A-Za-z0-9]+", family_label)
    significant = [word for word in words if len(word) >= 4]
    return " ".join(significant[:6]) if significant else family_label


async def run(
    *,
    cdp_url: str,
    queue_file: Path,
    execute: bool,
    artifact_dir: Path | None,
    wait_seconds: int,
) -> None:
    item = select_approved_items(load_merge_queue(queue_file), limit=1)
    if not item:
        raise RuntimeError("No approved merge queue items found.")
    await run_queue_item(
        cdp_url=cdp_url,
        queue_file=queue_file,
        item_id=item[0]["id"],
        execute=execute,
        artifact_dir=artifact_dir,
        wait_seconds=wait_seconds,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cdp-url", required=True, help="Chrome DevTools URL for an already-open logged-in browser.")
    parser.add_argument(
        "--queue-file",
        type=Path,
        default=default_merge_queue_path(),
        help="Path to the merge queue JSON artifact.",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually execute the next approved merge item. Otherwise run a dry-run and record review state.",
    )
    parser.add_argument(
        "--artifact-dir",
        type=Path,
        help="Optional artifact directory override for pre/post merge evidence.",
    )
    parser.add_argument(
        "--wait-seconds",
        type=int,
        default=20,
        help="How long to wait for profile readiness and post-click changes.",
    )
    args = parser.parse_args()
    asyncio.run(
        run(
            cdp_url=args.cdp_url,
            queue_file=args.queue_file,
            execute=args.execute,
            artifact_dir=args.artifact_dir,
            wait_seconds=args.wait_seconds,
        )
    )


async def run_queue_item(
    *,
    cdp_url: str,
    queue_file: Path,
    item_id: str,
    execute: bool,
    artifact_dir: Path | None,
    wait_seconds: int,
) -> dict:
    payload = load_merge_queue(queue_file)
    approved_items = select_approved_items(payload)
    item = next((candidate for candidate in approved_items if candidate.get("id") == item_id), None)
    if item is None:
        raise RuntimeError(f"Approved merge queue item not found: {item_id}")
    print(format_merge_queue_item(item))
    print("")

    targets = [f"{target['row_id']}::{target['title']}" for target in item.get("targets", [])]
    confirm = build_confirmation_phrase([target["row_id"] for target in item.get("targets", [])]) if execute else None

    try:
        result = await run_merge_family(
            cdp_url=cdp_url,
            targets=targets,
            confirm=confirm,
            execute=execute,
            list_visible_rows=False,
            visible_row_limit=20,
            visible_row_title_filter=None,
            list_visible_actions=False,
            artifact_dir=artifact_dir or (queue_file.parent),
            wait_seconds=wait_seconds,
        )
        verification = None
        if execute:
            verification = await run_merge_family(
                cdp_url=cdp_url,
                targets=[],
                confirm=None,
                execute=False,
                list_visible_rows=True,
                visible_row_limit=20,
                visible_row_title_filter=build_verification_filter(item),
                list_visible_actions=False,
                artifact_dir=artifact_dir or (queue_file.parent),
                wait_seconds=wait_seconds,
            )
        updated = update_queue_item_result(
            payload,
            item_id=item["id"],
            result={
                "runner_mode": result.get("mode"),
                "summary": result.get("summary"),
                "outcome": result.get("outcome"),
                "expected_confirmation": result.get("expected_confirmation"),
            },
            status="merged" if execute else "approved",
            increment_execution_attempts=execute,
        )
        if execute and verification is not None:
            updated = update_queue_item_verification(
                updated,
                item_id=item["id"],
                verification=summarize_verification_output(verification.get("output", "")),
            )
    except Exception as exc:
        updated = update_queue_item_result(
            payload,
            item_id=item["id"],
            result={
                "error": str(exc),
                "traceback": traceback.format_exc(),
            },
            status="failed",
            increment_execution_attempts=execute,
        )
        save_merge_queue(queue_file, updated)
        raise

    save_merge_queue(queue_file, updated)
    return {
        "item_id": item["id"],
        "family_label": item.get("family_label", ""),
        "execute": execute,
        "status": "merged" if execute else "approved",
    }


if __name__ == "__main__":
    main()
