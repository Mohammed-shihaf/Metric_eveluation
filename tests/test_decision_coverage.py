from __future__ import print_function
import unittest

from sa.decision_coverage import decision_case_0

class TestDecisionCoverageBug(unittest.TestCase):
    def test_started_only(self):
        self.assertIn('started', decision_case_0('ready', True, 0, 1))
