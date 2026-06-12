from __future__ import print_function
import unittest

from sa.qa_prioritization import prioritize_test_bucket_0

class TestBugPartial(unittest.TestCase):
    def test_partial_only(self):
        self.assertTrue(prioritize_test_bucket_0([{'name': 'a', 'complexity': 1}], {}))
