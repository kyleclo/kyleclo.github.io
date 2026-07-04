from __future__ import annotations

import unittest

from scripts.run_next_scholar_merge_queue_item import build_verification_filter


class TestRunNextScholarMergeQueueItem(unittest.TestCase):
    def test_build_verification_filter(self) -> None:
        self.assertEqual(
            build_verification_filter({"family_label": "OLMo: Accelerating the science of language models"}),
            "OLMo Accelerating science language models",
        )
        self.assertEqual(
            build_verification_filter({"family_label": "2 OLMo 2 Furious"}),
            "OLMo Furious",
        )


if __name__ == "__main__":
    unittest.main()
