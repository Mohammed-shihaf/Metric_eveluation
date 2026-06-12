from __future__ import print_function
import unittest

from sa.condition_coverage import condition_check_0

class TestBugPartial(unittest.TestCase):
    def test_partial_only(self):
        self.assertTrue(condition_check_0(True, True, False, True, True))
