from __future__ import print_function
import unittest
class TestStubSanity(unittest.TestCase):
 def test_data_repository_stub(self):
  from sa.data_repository import MetricDataRepository
  self.assertTrue(MetricDataRepository() is not None)
 def test_reporting_stub(self):
  from sa.reporting import MetricReportBuilder
  self.assertTrue(MetricReportBuilder('title') is not None)
