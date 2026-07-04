from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.scholar_merge_queue import (
    MERGE_QUEUE_STATUSES,
    default_merge_queue_path,
    format_merge_queue,
    format_merge_queue_item,
    format_merge_queue_triage,
    get_queue_item,
    load_merge_queue,
    save_merge_queue,
    select_queue_items,
    update_queue_item_status,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--queue-file",
        type=Path,
        default=default_merge_queue_path(),
        help="Path to the merge queue JSON artifact.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List merge queue items.")
    list_parser.add_argument("--status", choices=sorted(MERGE_QUEUE_STATUSES))
    list_parser.add_argument("--limit", type=int, default=20)
    list_parser.add_argument(
        "--triage",
        action="store_true",
        help="Compact triage view with one family summary per item.",
    )

    show_parser = subparsers.add_parser("show", help="Show one merge queue item.")
    show_parser.add_argument("--id", required=True, help="Queue item id to inspect.")

    update_parser = subparsers.add_parser("update", help="Update merge queue item status.")
    update_parser.add_argument("--id", required=True, help="Queue item id to update.")
    update_parser.add_argument("--status", required=True, choices=sorted(MERGE_QUEUE_STATUSES))
    update_parser.add_argument("--note", help="Optional review note to write into the queue item.")

    bulk_parser = subparsers.add_parser("bulk-update", help="Update many merge queue items by filter.")
    bulk_parser.add_argument("--status", required=True, choices=sorted(MERGE_QUEUE_STATUSES))
    bulk_parser.add_argument("--match-status", choices=sorted(MERGE_QUEUE_STATUSES))
    bulk_parser.add_argument("--family-type", choices=["pair", "multi"])
    bulk_parser.add_argument("--confidence", choices=["high", "medium", "low"])
    bulk_parser.add_argument("--contains", help="Case-insensitive substring filter over family label and target titles.")
    bulk_parser.add_argument("--exclude-contains", help="Case-insensitive substring exclusion over family label and target titles.")
    bulk_parser.add_argument("--limit", type=int, help="Optional maximum number of matching items to update.")
    bulk_parser.add_argument("--note", help="Optional review note to write into all updated items.")
    bulk_parser.add_argument("--dry-run", action="store_true", help="Print matching items without writing changes.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    payload = load_merge_queue(args.queue_file)

    if args.command == "list":
        formatter = format_merge_queue_triage if args.triage else format_merge_queue
        print(formatter(payload.get("items", []), status=args.status, limit=args.limit))
        return

    if args.command == "show":
        print(format_merge_queue_item(get_queue_item(payload, args.id)))
        return

    if args.command == "update":
        updated_payload = update_queue_item_status(
            payload,
            item_id=args.id,
            status=args.status,
            note=args.note,
        )
        save_merge_queue(args.queue_file, updated_payload)
        print(format_merge_queue_item(get_queue_item(updated_payload, args.id)))
        return

    if args.command == "bulk-update":
        matches = select_queue_items(
            payload,
            status=args.match_status,
            family_type=args.family_type,
            confidence=args.confidence,
            contains=args.contains,
            exclude_contains=args.exclude_contains,
            limit=args.limit,
        )
        if not matches:
            print("No merge queue items matched the requested filters.")
            return
        if args.dry_run:
            print(format_merge_queue_triage(matches, limit=len(matches)))
            return
        updated_payload = payload
        for item in matches:
            updated_payload = update_queue_item_status(
                updated_payload,
                item_id=item["id"],
                status=args.status,
                note=args.note,
            )
        save_merge_queue(args.queue_file, updated_payload)
        updated_matches = [get_queue_item(updated_payload, item["id"]) for item in matches]
        print(format_merge_queue_triage(updated_matches, limit=len(updated_matches)))
        return


if __name__ == "__main__":
    main()
