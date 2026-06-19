"""Tests for per-technique taxonomy classification and whitebox completion."""

from __future__ import print_function

import os
import sys
import tempfile
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from lib.proofs import whitebox_completion  # noqa: E402


def _taxonomy_html(branch, run_id, commit_sha="abc123def456"):
    return (
        "<html><body>"
        "Branch name</th><td>%s</td>"
        "Commit ID</th><td>%s</td>"
        "Run ID</th><td>%s</td>"
        "</body></html>"
    ) % (branch, commit_sha, run_id)


def _write_report(class_dir, branch, run_id, ts="20260618T120000Z"):
    folder = os.path.join(class_dir, "%s_%s" % (branch, ts))
    os.makedirs(folder, exist_ok=True)
    html_path = os.path.join(folder, "taxonomy-gate-%s.html" % run_id)
    with open(html_path, "w", encoding="utf-8") as fh:
        fh.write(_taxonomy_html(branch, run_id))
    with open(os.path.join(folder, "run_id.txt"), "w", encoding="utf-8") as fh:
        fh.write(run_id)
    return html_path


class WhiteboxCompletionTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self.tax_root = os.path.join(self._tmpdir, "taxonomy_reports")
        os.makedirs(self.tax_root)

    def _class_dir(self, label):
        path = os.path.join(self.tax_root, label)
        os.makedirs(path, exist_ok=True)
        return path

    def test_sa_in_canonical_folder(self):
        branch = "SA_Decision-Outcome-Verification_Bug_2.6"
        _write_report(self._class_dir("Structural Analysis"), branch, "run-sa-001")
        result = whitebox_completion([branch], root=self._tmpdir)
        self.assertEqual(result[branch]["status"], "COMPLETED")

    def test_df_in_canonical_folder(self):
        branch = "DF_DU-Path-Validation_Bug_2.6"
        _write_report(self._class_dir("Data Flow Testing"), branch, "run-df-001")
        result = whitebox_completion([branch], root=self._tmpdir)
        self.assertEqual(result[branch]["status"], "COMPLETED")

    def test_df_misfiled_in_structural_analysis(self):
        branch = "DF_DU-Path-Validation_TCC_2.6"
        _write_report(self._class_dir("Structural Analysis"), branch, "run-df-002")
        result = whitebox_completion([branch], root=self._tmpdir)
        self.assertEqual(result[branch]["status"], "COMPLETED")
        self.assertTrue(result[branch]["html_path"])

    def test_br_misfiled_in_structural_analysis(self):
        branch = "BR_Sequence-Integrity-Mapping_Bug_2.6"
        _write_report(self._class_dir("Structural Analysis"), branch, "run-br-001")
        result = whitebox_completion([branch], root=self._tmpdir)
        self.assertEqual(result[branch]["status"], "COMPLETED")

    def test_missing_branch_not_completed(self):
        branch = "MU_Logic-Error-Sensitivity_CC_2.6"
        result = whitebox_completion([branch], root=self._tmpdir)
        self.assertEqual(result[branch]["status"], "NOT_COMPLETED")

    def test_json_only_report_folder_completed(self):
        branch = "SA_Decision-Outcome-Verification_Bug_2.6"
        class_dir = self._class_dir("Structural Analysis")
        folder = os.path.join(class_dir, "%s_20260619T061541Z" % branch)
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, "run_id.txt"), "w", encoding="utf-8") as fh:
            fh.write("598e3d1d-eede-495e-bf06-1831982fce13")
        with open(os.path.join(folder, "run_summary.json"), "w", encoding="utf-8") as fh:
            import json
            json.dump(
                {
                    "run_id": "598e3d1d-eede-495e-bf06-1831982fce13",
                    "commit_sha": "5677904bbd7e61627c206de4cbb31629c0b25e19",
                    "branch_name": branch,
                    "status": "failed",
                    "total_tasks": 28,
                    "completed_tasks": 27,
                    "failed_tasks": 1,
                },
                fh,
            )
        with open(os.path.join(folder, "taxonomy-gate.json"), "w", encoding="utf-8") as fh:
            import json
            json.dump({"gate_status": "completed", "weighted_breakdown": []}, fh)
        result = whitebox_completion([branch], root=self._tmpdir)
        self.assertEqual(result[branch]["status"], "COMPLETED")
        self.assertEqual(result[branch]["commit_sha"], "5677904bbd7e61627c206de4cbb31629c0b25e19")
        self.assertFalse(result[branch]["expects_s3"])

    def test_taxonomy_complete_with_failed_task_is_ok_health(self):
        branch = "SX_Entry-Point-Sanitization_Bug_2.6"
        class_dir = self._class_dir("Security White-box Testing")
        folder = os.path.join(class_dir, "%s_20260618T210012Z" % branch)
        os.makedirs(folder, exist_ok=True)
        html_path = os.path.join(folder, "taxonomy-gate-run.html")
        with open(html_path, "w", encoding="utf-8") as fh:
            fh.write(_taxonomy_html(branch, "run-sx-001"))
        with open(os.path.join(folder, "run_summary.json"), "w", encoding="utf-8") as fh:
            import json
            json.dump(
                {
                    "status": "failed",
                    "total_tasks": 28,
                    "completed_tasks": 27,
                    "failed_tasks": 1,
                },
                fh,
            )
        with open(os.path.join(folder, "taxonomy-gate.json"), "w", encoding="utf-8") as fh:
            import json
            json.dump({"gate_status": "completed", "weighted_breakdown": []}, fh)
        result = whitebox_completion([branch], root=self._tmpdir)
        self.assertEqual(result[branch]["status"], "COMPLETED")
        self.assertEqual(result[branch]["run_health"], "OK")
        self.assertEqual(result[branch]["failed_tasks"], 1)


if __name__ == "__main__":
    unittest.main()
