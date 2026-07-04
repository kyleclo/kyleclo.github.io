from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from scripts.run_batch_scholar_merge_queue import run_batch
from scripts.scholar_merge_queue import save_merge_queue


class TestRunBatchScholarMergeQueue(unittest.IsolatedAsyncioTestCase):
    async def test_run_batch_rejects_live_execute(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            queue_file = Path(tmpdir) / "merge_queue.json"
            save_merge_queue(
                queue_file,
                {
                    "generated_at": None,
                    "items": [
                        {
                            "id": "a",
                            "status": "approved",
                            "approved_by_operator": True,
                            "approved_at": "2026-04-13T00:00:01Z",
                            "family_label": "A",
                            "targets": [],
                        }
                    ],
                },
            )
            with self.assertRaisesRegex(RuntimeError, "Live batch execution is disabled"):
                await run_batch(
                    cdp_url="http://127.0.0.1:9224",
                    queue_file=queue_file,
                    execute=True,
                    artifact_dir=None,
                    wait_seconds=20,
                    limit=None,
                )

    async def test_run_batch_processes_approved_items_in_order(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            queue_file = Path(tmpdir) / "merge_queue.json"
            save_merge_queue(
                queue_file,
                {
                    "generated_at": None,
                    "items": [
                        {
                            "id": "b",
                            "status": "approved",
                            "approved_by_operator": True,
                            "approved_at": "2026-04-13T00:00:02Z",
                            "family_label": "B",
                            "targets": [],
                        },
                        {
                            "id": "a",
                            "status": "approved",
                            "approved_by_operator": True,
                            "approved_at": "2026-04-13T00:00:01Z",
                            "family_label": "A",
                            "targets": [],
                        },
                    ],
                },
            )
            mock = AsyncMock(side_effect=[{"item_id": "a"}, {"item_id": "b"}])
            with patch("scripts.run_batch_scholar_merge_queue.run_queue_item", mock):
                results = await run_batch(
                    cdp_url="http://127.0.0.1:9224",
                    queue_file=queue_file,
                    execute=False,
                    artifact_dir=None,
                    wait_seconds=20,
                    limit=None,
                )
            self.assertEqual([call.kwargs["item_id"] for call in mock.await_args_list], ["a", "b"])
            self.assertEqual(results, [{"item_id": "a"}, {"item_id": "b"}])

    async def test_run_batch_respects_limit(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            queue_file = Path(tmpdir) / "merge_queue.json"
            save_merge_queue(
                queue_file,
                {
                    "generated_at": None,
                    "items": [
                        {
                            "id": "a",
                            "status": "approved",
                            "approved_by_operator": True,
                            "approved_at": "2026-04-13T00:00:01Z",
                            "family_label": "A",
                            "targets": [],
                        },
                        {
                            "id": "b",
                            "status": "approved",
                            "approved_by_operator": True,
                            "approved_at": "2026-04-13T00:00:02Z",
                            "family_label": "B",
                            "targets": [],
                        },
                    ],
                },
            )
            mock = AsyncMock(return_value={"item_id": "a"})
            with patch("scripts.run_batch_scholar_merge_queue.run_queue_item", mock):
                await run_batch(
                    cdp_url="http://127.0.0.1:9224",
                    queue_file=queue_file,
                    execute=False,
                    artifact_dir=None,
                    wait_seconds=20,
                    limit=1,
                )
            self.assertEqual([call.kwargs["item_id"] for call in mock.await_args_list], ["a"])


if __name__ == "__main__":
    unittest.main()
