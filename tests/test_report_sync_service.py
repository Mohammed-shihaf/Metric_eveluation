"""Tests for background report sync service."""

from __future__ import print_function

import os
import sys
import time
import unittest
from unittest.mock import patch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

import lib.report_sync_service as rss  # noqa: E402


class ReportSyncServiceTests(unittest.TestCase):
    def setUp(self):
        rss._WORKERS.clear()

    def tearDown(self):
        for user in list(rss._WORKERS.keys()):
            rss.stop(user)

    def test_start_stop_status(self):
        with patch.object(rss, "_sync_tick") as tick:
            rss.start("user1", root=ROOT, scope_branches=["B1"], interval_sec=1)
            time.sleep(0.2)
            st = rss.status("user1")
            self.assertTrue(st["running"])
            rss.stop("user1")
            time.sleep(0.2)
            self.assertFalse(rss.status("user1")["running"])

    def test_scope_refresh(self):
        rss.start("user1", root=ROOT, scope_branches=["A"])
        with rss._LOCK:
            self.assertEqual(rss._WORKERS["user1"]["scope_branches"], ["A"])
        rss.start("user1", root=ROOT, scope_branches=["A", "B"])
        with rss._LOCK:
            self.assertEqual(rss._WORKERS["user1"]["scope_branches"], ["A", "B"])

    def test_branches_needing_sync_skips_completed_with_proof(self):
        with patch("lib.proofs.whitebox_completion") as wb, patch(
            "lib.report_schema.find_s3_report_path", return_value="/tmp/has-data",
        ), patch("pathlib.Path.is_dir", return_value=True), patch(
            "pathlib.Path.iterdir", return_value=iter([1]),
        ):
            wb.return_value = {
                "Branch_A": {
                    "status": "COMPLETED",
                    "expects_s3": True,
                    "commit_sha": "abc",
                    "run_id": "run1",
                    "meta": {},
                },
            }
            pending = rss._branches_needing_sync(["Branch_A"], ROOT)
        self.assertEqual(pending, [])


if __name__ == "__main__":
    unittest.main()
