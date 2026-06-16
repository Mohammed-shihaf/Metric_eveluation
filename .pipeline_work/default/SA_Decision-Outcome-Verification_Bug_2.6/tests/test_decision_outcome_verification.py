from __future__ import print_function
import unittest
from sa.decision_outcome_verification import dov_case_1

class TestBugPartial(unittest.TestCase):
    def test_one_case(self):
        self.assertTrue(dov_case_1('x', True, 1, 3))
