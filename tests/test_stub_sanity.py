from __future__ import print_function
import unittest
class TestStubSanity(unittest.TestCase):
 def test_decision_coverage_stub(self):
  from sa.decision_coverage import aggregate_decision_coverage
  self.assertTrue(aggregate_decision_coverage([]) is not None)
 def test_data_repository_stub(self):
  from sa.data_repository import MetricDataRepository
  self.assertTrue(MetricDataRepository() is not None)
