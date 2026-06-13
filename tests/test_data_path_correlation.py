from __future__ import print_function
import unittest
from df.data_path_correlation import dpc_case_0

class TestBugPartial(unittest.TestCase):
    def test_one_case(self):
        self.assertTrue(dpc_case_0('x', True, 1, 3))
