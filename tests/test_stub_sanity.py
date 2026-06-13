from __future__ import print_function
import unittest
class TestStubSanity(unittest.TestCase):
 def test_execution_path_integrity_stub(self):
  from sa.execution_path_integrity import evaluate_path_integrity
  self.assertTrue(evaluate_path_integrity(1, 'fast', {}) is not None)
 def test_data_repository_stub(self):
  from sa.data_repository import MetricDataRepository
  self.assertTrue(MetricDataRepository() is not None)
