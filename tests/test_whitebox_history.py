"""Tests for whitebox run history helpers."""

from __future__ import print_function

import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from lib.whitebox_history import branch_run_history, split_completed_pending  # noqa: E402


class WhiteboxHistoryTests(unittest.TestCase):
    def _make_taxonomy_tree(self, root, branch_name):
        class_dir = os.path.join(root, "taxonomy_reports", "SA")
        os.makedirs(class_dir, exist_ok=True)
        folder = "report_%s_20260101120000" % branch_name.replace("-", "_")
        report_dir = os.path.join(class_dir, folder)
        os.makedirs(report_dir, exist_ok=True)
        with open(os.path.join(report_dir, "run_id.txt"), "w", encoding="utf-8") as fh:
            fh.write("run-123")
        with open(os.path.join(report_dir, "run_summary.json"), "w", encoding="utf-8") as fh:
            json.dump({
                "branch_name": branch_name,
                "commit_sha": "deadbeef",
                "status": "completed",
                "total_tasks": 4,
                "completed_tasks": 4,
                "failed_tasks": 0,
            }, fh)
        html_path = os.path.join(report_dir, "taxonomy-gate.html")
        with open(html_path, "w", encoding="utf-8") as fh:
            fh.write("<html></html>")
        manifest = {
            "runs": [{
                "branch": branch_name,
                "run_id": "run-123",
                "commit_sha": "deadbeef",
            }],
        }
        with open(os.path.join(class_dir, "manifest.json"), "w", encoding="utf-8") as fh:
            json.dump(manifest, fh)
        return branch_name

    def test_branch_run_history_and_split(self):
        with tempfile.TemporaryDirectory() as tmp:
            branch = "SA_Decision-Outcome-Verification_Bug_2.6"
            self._make_taxonomy_tree(tmp, branch)
            history = branch_run_history(branch, root=tmp)
            self.assertGreaterEqual(len(history), 1)
            self.assertEqual(history[0]["run_id"], "run-123")

            completed, pending = split_completed_pending(
                [branch, "SA_Other-Metric_Bug_2.6"],
                root=tmp,
            )
            self.assertIn(branch, completed)
            self.assertIn("SA_Other-Metric_Bug_2.6", pending)


if __name__ == "__main__":
    unittest.main()
