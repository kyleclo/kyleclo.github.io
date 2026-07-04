# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "playwright",
# ]
# ///
"""
Dry-run approved Scholar merge queue items serially.

Live batch execution is intentionally disabled. Use
`run_next_scholar_merge_queue_item.py --execute` for one-item-at-a-time
mutation until stronger per-item revalidation is implemented.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.run_next_scholar_merge_queue_item import run_queue_item
from scripts.scholar_merge_queue import (
    default_merge_queue_path,
    format_merge_queue_triage,
    load_merge_queue,
    select_approved_items,
)


async def run_batch(
    *,
    cdp_url: str,
    queue_file: Path,
    execute: bool,
    artifact_dir: Path | None,
    wait_seconds: int,
    limit: int | None,
) -> list[dict]:
    if execute:
        raise RuntimeError(
            "Live batch execution is disabled. Use run_next_scholar_merge_queue_item.py --execute "
            "for one-item-at-a-time mutation."
        )

    approved_items = select_approved_items(load_merge_queue(queue_file), limit=limit)
    if not approved_items:
        raise RuntimeError("No approved merge queue items found.")

    print(format_merge_queue_triage(approved_items, limit=len(approved_items)))
    print("")

    results = []
    for index, item in enumerate(approved_items, start=1):
        print(f"[{index}/{len(approved_items)}] {item.get('family_label', '')}")
        result = await run_queue_item(
            cdp_url=cdp_url,
            queue_file=queue_file,
            item_id=item["id"],
            execute=execute,
            artifact_dir=artifact_dir,
            wait_seconds=wait_seconds,
        )
        results.append(result)
        print("")
    return results


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
        help="Disabled. Live execution must use run_next_scholar_merge_queue_item.py one item at a time.",
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
    parser.add_argument(
        "--limit",
        type=int,
        help="Optional maximum number of approved items to process this run.",
    )
    args = parser.parse_args()
    if args.execute:
        parser.error(
            "--execute is disabled for batch runs; use scripts/run_next_scholar_merge_queue_item.py --execute instead."
        )
    asyncio.run(
        run_batch(
            cdp_url=args.cdp_url,
            queue_file=args.queue_file,
            execute=args.execute,
            artifact_dir=args.artifact_dir,
            wait_seconds=args.wait_seconds,
            limit=args.limit,
        )
    )


if __name__ == "__main__":
    main()
