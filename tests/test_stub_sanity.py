from __future__ import print_function
import unittest
import os

class TestStubs(unittest.TestCase):
    def test_pkg_exists(self):
        self.assertTrue(os.path.isdir('df'))
