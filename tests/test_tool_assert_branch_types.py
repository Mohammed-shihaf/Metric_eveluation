"""Branch-type tool assert and report normalization tests."""

from __future__ import print_function

import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from lib.report_schema import _status_from_metric_values, from_tool_assert_result  # noqa: E402
from lib.tool_assert import metric_violation, tool_assert_branch  # noqa: E402


class MetricViolationTests(unittest.TestCase):
    def test_bugfx_coverage_low_pct_full_suite_passes(self):
        self.assertFalse(
            metric_violation(
                "coverage",
                {"coverage_pct": 30.0, "tests": 72},
                branch_type="BugFX",
                n_tests=72,
            )
        )

    def test_bug_coverage_low_pct_partial_suite_fails(self):
        self.assertTrue(
            metric_violation(
                "coverage",
                {"coverage_pct": 30.0, "tests": 1},
                branch_type="Bug",
                n_tests=1,
            )
        )

    def test_status_from_metric_values_bugfx_pass(self):
        status = _status_from_metric_values(
            "coverage",
            {"coverage_pct": 35.0, "tests": 72},
            branch_type="BugFX",
            n_tests=72,
        )
        self.assertEqual(status, "PASS")

    def test_status_from_metric_values_bug_fail(self):
        status = _status_from_metric_values(
            "coverage",
            {"coverage_pct": 35.0, "tests": 1},
            branch_type="Bug",
            n_tests=1,
        )
        self.assertEqual(status, "FAIL")

    def test_s3_assumes_resolved_suite_for_non_bug(self):
        status = _status_from_metric_values(
            "coverage",
            {"coverage_pct": 35.0},
            branch_type="BugFX",
        )
        self.assertEqual(status, "PASS")

    def test_from_tool_assert_result_prefers_tool_outcome(self):
        result = {
            "branch_name": "SA_Decision-Outcome-Verification_BugFX_2.6",
            "technique_code": "SA",
            "metric_code": "DOV",
            "branch_type": "BugFX",
            "status": "PASS",
            "tool_used": "coverage.py",
            "tool_outcome": "PASS",
            "raw_metric_value": "35.0% cov tests=72",
            "real_tool": True,
        }
        report = from_tool_assert_result(result, source="local")
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["extra"]["assert_status"], "PASS")


class ToolAssertIntegrationTests(unittest.TestCase):
    _work_roots = [
        os.path.join(ROOT, ".pipeline_work", "08b2473015be749b"),
        os.path.join(ROOT, ".pipeline_work", "default"),
    ]

    def _branch_path(self, folder):
        for work in self._work_roots:
            path = os.path.join(work, folder)
            if os.path.isdir(path):
                return path
        return None

    @unittest.skipUnless(
        os.path.isdir(os.path.join(ROOT, ".pipeline_work", "08b2473015be749b", "SA_Decision-Outcome-Verification_BugFX_2.6")),
        "SA DOV pipeline copies not present",
    )
    def test_sa_dov_all_types_assert_and_report_align(self):
        expected = {
            "Bug": ("PASS", "FAIL", "FAIL"),
            "BugFX": ("PASS", "PASS", "PASS"),
            "TCC": ("PASS", "PASS", "PASS"),
            "CC": ("PASS", "PASS", "PASS"),
        }
        for bt, (assert_st, tool_out, report_st) in expected.items():
            folder = "SA_Decision-Outcome-Verification_%s_2.6" % bt
            path = self._branch_path(folder)
            self.assertIsNotNone(path, "missing %s" % folder)
            try:
                result = tool_assert_branch(path, "SA", "DOV", bt)
            except Exception as exc:
                self.skipTest("tool env unavailable: %s" % exc)
            report = from_tool_assert_result(result, source="local")
            self.assertEqual(result["status"], assert_st, bt)
            self.assertEqual(result.get("tool_outcome"), tool_out, bt)
            self.assertEqual(report["status"], report_st, bt)

    @unittest.skipUnless(
        os.path.isdir(os.path.join(ROOT, ".pipeline_work", "default", "SX_Entry-Point-Sanitization_BugFX_2.6")),
        "SX EPS pipeline copies not present",
    )
    def test_sx_eps_non_bug_pass(self):
        for bt in ("BugFX", "TCC", "CC"):
            folder = "SX_Entry-Point-Sanitization_%s_2.6" % bt
            path = self._branch_path(folder)
            try:
                result = tool_assert_branch(path, "SX", "EPS", bt)
            except Exception as exc:
                self.skipTest("tool env unavailable: %s" % exc)
            report = from_tool_assert_result(result, source="local")
            self.assertEqual(result["status"], "PASS", bt)
            self.assertEqual(result.get("tool_outcome"), "PASS", bt)
            self.assertEqual(report["status"], "PASS", bt)


if __name__ == "__main__":
    unittest.main()
