"""Registry metric filter tests."""

from __future__ import print_function

import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from lib.registry import iter_branches, parse_metrics_filter, parse_qualified_metrics  # noqa: E402


class QualifiedMetricsTests(unittest.TestCase):
    def test_parse_qualified_metrics_splits_by_technique(self):
        by_tech, wildcards, has_qualified = parse_qualified_metrics("CQ:ABPO,RM:DEPR,DOV")
        self.assertTrue(has_qualified)
        self.assertEqual(by_tech.get("CQ"), ["ABPO"])
        self.assertEqual(by_tech.get("RM"), ["DEPR"])
        self.assertEqual(wildcards, ["DOV"])

    def test_parse_metrics_filter_skips_unrelated_technique(self):
        codes = parse_metrics_filter("CQ:ABPO,RM:DEPR", "SA")
        self.assertEqual(codes, [])

    def test_parse_metrics_filter_returns_technique_metrics(self):
        codes = parse_metrics_filter("CQ:ABPO,RM:DEPR", "CQ")
        self.assertEqual(codes, ["ABPO"])

    def test_iter_branches_multi_technique_no_error(self):
        branches = list(iter_branches("SA,CQ", "CQ:ABPO", types=["Bug"], version="2.6"))
        self.assertEqual(len(branches), 1)
        self.assertEqual(branches[0][0], "CQ")
        self.assertEqual(branches[0][1], "ABPO")

    def test_flat_list_still_works_single_technique(self):
        codes = parse_metrics_filter("DOV", "SA")
        self.assertIn("DOV", codes)


if __name__ == "__main__":
    unittest.main()
