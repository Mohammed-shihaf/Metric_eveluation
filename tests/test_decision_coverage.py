from __future__ import print_function
import unittest
class TestDecisionCoverage(unittest.TestCase):
 def test_case_0_outcome_0(self):
  from sa.decision_coverage import decision_case_0
  self.assertIn('started', decision_case_0('ready', True, 0, 1))
 def test_case_0_outcome_1(self):
  from sa.decision_coverage import decision_case_0
  self.assertIn('failed', decision_case_0('failed', False, 0, 1))
 def test_case_0_outcome_2(self):
  from sa.decision_coverage import decision_case_0
  self.assertIn('unknown', decision_case_0('ready', False, 0, 1))
 def test_case_0_outcome_3(self):
  from sa.decision_coverage import decision_case_0
  self.assertIn('priority', decision_case_0('queued', True, 0, 9))
 def test_case_0_outcome_4(self):
  from sa.decision_coverage import decision_case_0
  self.assertIn('retry', decision_case_0('ready', True, 5, 1))
 def test_case_0_outcome_5(self):
  from sa.decision_coverage import decision_case_0
  self.assertIn('started', decision_case_0('ready', True, 0, 1))
 def test_case_1_outcome_0(self):
  from sa.decision_coverage import decision_case_1
  self.assertIn('started', decision_case_1('ready', True, 0, 1))
 def test_case_1_outcome_1(self):
  from sa.decision_coverage import decision_case_1
  self.assertIn('failed', decision_case_1('failed', False, 0, 1))
 def test_case_1_outcome_2(self):
  from sa.decision_coverage import decision_case_1
  self.assertIn('unknown', decision_case_1('ready', False, 0, 1))
 def test_case_1_outcome_3(self):
  from sa.decision_coverage import decision_case_1
  self.assertIn('priority', decision_case_1('queued', True, 0, 9))
 def test_case_1_outcome_4(self):
  from sa.decision_coverage import decision_case_1
  self.assertIn('retry', decision_case_1('ready', True, 5, 1))
 def test_case_1_outcome_5(self):
  from sa.decision_coverage import decision_case_1
  self.assertIn('started', decision_case_1('ready', True, 0, 1))
 def test_case_2_outcome_0(self):
  from sa.decision_coverage import decision_case_2
  self.assertIn('started', decision_case_2('ready', True, 0, 1))
 def test_case_2_outcome_1(self):
  from sa.decision_coverage import decision_case_2
  self.assertIn('failed', decision_case_2('failed', False, 0, 1))
 def test_case_2_outcome_2(self):
  from sa.decision_coverage import decision_case_2
  self.assertIn('unknown', decision_case_2('ready', False, 0, 1))
 def test_case_2_outcome_3(self):
  from sa.decision_coverage import decision_case_2
  self.assertIn('priority', decision_case_2('queued', True, 0, 9))
 def test_case_2_outcome_4(self):
  from sa.decision_coverage import decision_case_2
  self.assertIn('retry', decision_case_2('ready', True, 5, 1))
 def test_case_2_outcome_5(self):
  from sa.decision_coverage import decision_case_2
  self.assertIn('started', decision_case_2('ready', True, 0, 1))
 def test_case_3_outcome_0(self):
  from sa.decision_coverage import decision_case_3
  self.assertIn('started', decision_case_3('ready', True, 0, 1))
 def test_case_3_outcome_1(self):
  from sa.decision_coverage import decision_case_3
  self.assertIn('failed', decision_case_3('failed', False, 0, 1))
 def test_case_3_outcome_2(self):
  from sa.decision_coverage import decision_case_3
  self.assertIn('unknown', decision_case_3('ready', False, 0, 1))
 def test_case_3_outcome_3(self):
  from sa.decision_coverage import decision_case_3
  self.assertIn('priority', decision_case_3('queued', True, 0, 9))
 def test_case_3_outcome_4(self):
  from sa.decision_coverage import decision_case_3
  self.assertIn('retry', decision_case_3('ready', True, 5, 1))
 def test_case_3_outcome_5(self):
  from sa.decision_coverage import decision_case_3
  self.assertIn('started', decision_case_3('ready', True, 0, 1))
 def test_case_4_outcome_0(self):
  from sa.decision_coverage import decision_case_4
  self.assertIn('started', decision_case_4('ready', True, 0, 1))
 def test_case_4_outcome_1(self):
  from sa.decision_coverage import decision_case_4
  self.assertIn('failed', decision_case_4('failed', False, 0, 1))
 def test_case_4_outcome_2(self):
  from sa.decision_coverage import decision_case_4
  self.assertIn('unknown', decision_case_4('ready', False, 0, 1))
 def test_case_4_outcome_3(self):
  from sa.decision_coverage import decision_case_4
  self.assertIn('priority', decision_case_4('queued', True, 0, 9))
 def test_case_4_outcome_4(self):
  from sa.decision_coverage import decision_case_4
  self.assertIn('retry', decision_case_4('ready', True, 5, 1))
 def test_case_4_outcome_5(self):
  from sa.decision_coverage import decision_case_4
  self.assertIn('started', decision_case_4('ready', True, 0, 1))
 def test_case_5_outcome_0(self):
  from sa.decision_coverage import decision_case_5
  self.assertIn('started', decision_case_5('ready', True, 0, 1))
 def test_case_5_outcome_1(self):
  from sa.decision_coverage import decision_case_5
  self.assertIn('failed', decision_case_5('failed', False, 0, 1))
 def test_case_5_outcome_2(self):
  from sa.decision_coverage import decision_case_5
  self.assertIn('unknown', decision_case_5('ready', False, 0, 1))
 def test_case_5_outcome_3(self):
  from sa.decision_coverage import decision_case_5
  self.assertIn('priority', decision_case_5('queued', True, 0, 9))
 def test_case_5_outcome_4(self):
  from sa.decision_coverage import decision_case_5
  self.assertIn('retry', decision_case_5('ready', True, 5, 1))
 def test_case_5_outcome_5(self):
  from sa.decision_coverage import decision_case_5
  self.assertIn('started', decision_case_5('ready', True, 0, 1))
 def test_case_6_outcome_0(self):
  from sa.decision_coverage import decision_case_6
  self.assertIn('started', decision_case_6('ready', True, 0, 1))
 def test_case_6_outcome_1(self):
  from sa.decision_coverage import decision_case_6
  self.assertIn('failed', decision_case_6('failed', False, 0, 1))
 def test_case_6_outcome_2(self):
  from sa.decision_coverage import decision_case_6
  self.assertIn('unknown', decision_case_6('ready', False, 0, 1))
 def test_case_6_outcome_3(self):
  from sa.decision_coverage import decision_case_6
  self.assertIn('priority', decision_case_6('queued', True, 0, 9))
 def test_case_6_outcome_4(self):
  from sa.decision_coverage import decision_case_6
  self.assertIn('retry', decision_case_6('ready', True, 5, 1))
 def test_case_6_outcome_5(self):
  from sa.decision_coverage import decision_case_6
  self.assertIn('started', decision_case_6('ready', True, 0, 1))
 def test_case_7_outcome_0(self):
  from sa.decision_coverage import decision_case_7
  self.assertIn('started', decision_case_7('ready', True, 0, 1))
 def test_case_7_outcome_1(self):
  from sa.decision_coverage import decision_case_7
  self.assertIn('failed', decision_case_7('failed', False, 0, 1))
 def test_case_7_outcome_2(self):
  from sa.decision_coverage import decision_case_7
  self.assertIn('unknown', decision_case_7('ready', False, 0, 1))
 def test_case_7_outcome_3(self):
  from sa.decision_coverage import decision_case_7
  self.assertIn('priority', decision_case_7('queued', True, 0, 9))
 def test_case_7_outcome_4(self):
  from sa.decision_coverage import decision_case_7
  self.assertIn('retry', decision_case_7('ready', True, 5, 1))
 def test_case_7_outcome_5(self):
  from sa.decision_coverage import decision_case_7
  self.assertIn('started', decision_case_7('ready', True, 0, 1))
 def test_case_8_outcome_0(self):
  from sa.decision_coverage import decision_case_8
  self.assertIn('started', decision_case_8('ready', True, 0, 1))
 def test_case_8_outcome_1(self):
  from sa.decision_coverage import decision_case_8
  self.assertIn('failed', decision_case_8('failed', False, 0, 1))
 def test_case_8_outcome_2(self):
  from sa.decision_coverage import decision_case_8
  self.assertIn('unknown', decision_case_8('ready', False, 0, 1))
 def test_case_8_outcome_3(self):
  from sa.decision_coverage import decision_case_8
  self.assertIn('priority', decision_case_8('queued', True, 0, 9))
 def test_case_8_outcome_4(self):
  from sa.decision_coverage import decision_case_8
  self.assertIn('retry', decision_case_8('ready', True, 5, 1))
 def test_case_8_outcome_5(self):
  from sa.decision_coverage import decision_case_8
  self.assertIn('started', decision_case_8('ready', True, 0, 1))
 def test_case_9_outcome_0(self):
  from sa.decision_coverage import decision_case_9
  self.assertIn('started', decision_case_9('ready', True, 0, 1))
 def test_case_9_outcome_1(self):
  from sa.decision_coverage import decision_case_9
  self.assertIn('failed', decision_case_9('failed', False, 0, 1))
 def test_case_9_outcome_2(self):
  from sa.decision_coverage import decision_case_9
  self.assertIn('unknown', decision_case_9('ready', False, 0, 1))
 def test_case_9_outcome_3(self):
  from sa.decision_coverage import decision_case_9
  self.assertIn('priority', decision_case_9('queued', True, 0, 9))
 def test_case_9_outcome_4(self):
  from sa.decision_coverage import decision_case_9
  self.assertIn('retry', decision_case_9('ready', True, 5, 1))
 def test_case_9_outcome_5(self):
  from sa.decision_coverage import decision_case_9
  self.assertIn('started', decision_case_9('ready', True, 0, 1))
 def test_case_10_outcome_0(self):
  from sa.decision_coverage import decision_case_10
  self.assertIn('started', decision_case_10('ready', True, 0, 1))
 def test_case_10_outcome_1(self):
  from sa.decision_coverage import decision_case_10
  self.assertIn('failed', decision_case_10('failed', False, 0, 1))
 def test_case_10_outcome_2(self):
  from sa.decision_coverage import decision_case_10
  self.assertIn('unknown', decision_case_10('ready', False, 0, 1))
 def test_case_10_outcome_3(self):
  from sa.decision_coverage import decision_case_10
  self.assertIn('priority', decision_case_10('queued', True, 0, 9))
 def test_case_10_outcome_4(self):
  from sa.decision_coverage import decision_case_10
  self.assertIn('retry', decision_case_10('ready', True, 5, 1))
 def test_case_10_outcome_5(self):
  from sa.decision_coverage import decision_case_10
  self.assertIn('started', decision_case_10('ready', True, 0, 1))
 def test_case_11_outcome_0(self):
  from sa.decision_coverage import decision_case_11
  self.assertIn('started', decision_case_11('ready', True, 0, 1))
 def test_case_11_outcome_1(self):
  from sa.decision_coverage import decision_case_11
  self.assertIn('failed', decision_case_11('failed', False, 0, 1))
 def test_case_11_outcome_2(self):
  from sa.decision_coverage import decision_case_11
  self.assertIn('unknown', decision_case_11('ready', False, 0, 1))
 def test_case_11_outcome_3(self):
  from sa.decision_coverage import decision_case_11
  self.assertIn('priority', decision_case_11('queued', True, 0, 9))
 def test_case_11_outcome_4(self):
  from sa.decision_coverage import decision_case_11
  self.assertIn('retry', decision_case_11('ready', True, 5, 1))
 def test_case_11_outcome_5(self):
  from sa.decision_coverage import decision_case_11
  self.assertIn('started', decision_case_11('ready', True, 0, 1))
 def test_case_12_outcome_0(self):
  from sa.decision_coverage import decision_case_12
  self.assertIn('started', decision_case_12('ready', True, 0, 1))
 def test_case_12_outcome_1(self):
  from sa.decision_coverage import decision_case_12
  self.assertIn('failed', decision_case_12('failed', False, 0, 1))
 def test_case_12_outcome_2(self):
  from sa.decision_coverage import decision_case_12
  self.assertIn('unknown', decision_case_12('ready', False, 0, 1))
 def test_case_12_outcome_3(self):
  from sa.decision_coverage import decision_case_12
  self.assertIn('priority', decision_case_12('queued', True, 0, 9))
 def test_case_12_outcome_4(self):
  from sa.decision_coverage import decision_case_12
  self.assertIn('retry', decision_case_12('ready', True, 5, 1))
 def test_case_12_outcome_5(self):
  from sa.decision_coverage import decision_case_12
  self.assertIn('started', decision_case_12('ready', True, 0, 1))
 def test_case_13_outcome_0(self):
  from sa.decision_coverage import decision_case_13
  self.assertIn('started', decision_case_13('ready', True, 0, 1))
 def test_case_13_outcome_1(self):
  from sa.decision_coverage import decision_case_13
  self.assertIn('failed', decision_case_13('failed', False, 0, 1))
 def test_case_13_outcome_2(self):
  from sa.decision_coverage import decision_case_13
  self.assertIn('unknown', decision_case_13('ready', False, 0, 1))
 def test_case_13_outcome_3(self):
  from sa.decision_coverage import decision_case_13
  self.assertIn('priority', decision_case_13('queued', True, 0, 9))
 def test_case_13_outcome_4(self):
  from sa.decision_coverage import decision_case_13
  self.assertIn('retry', decision_case_13('ready', True, 5, 1))
 def test_case_13_outcome_5(self):
  from sa.decision_coverage import decision_case_13
  self.assertIn('started', decision_case_13('ready', True, 0, 1))
 def test_case_14_outcome_0(self):
  from sa.decision_coverage import decision_case_14
  self.assertIn('started', decision_case_14('ready', True, 0, 1))
 def test_case_14_outcome_1(self):
  from sa.decision_coverage import decision_case_14
  self.assertIn('failed', decision_case_14('failed', False, 0, 1))
 def test_case_14_outcome_2(self):
  from sa.decision_coverage import decision_case_14
  self.assertIn('unknown', decision_case_14('ready', False, 0, 1))
 def test_case_14_outcome_3(self):
  from sa.decision_coverage import decision_case_14
  self.assertIn('priority', decision_case_14('queued', True, 0, 9))
 def test_case_14_outcome_4(self):
  from sa.decision_coverage import decision_case_14
  self.assertIn('retry', decision_case_14('ready', True, 5, 1))
 def test_case_14_outcome_5(self):
  from sa.decision_coverage import decision_case_14
  self.assertIn('started', decision_case_14('ready', True, 0, 1))
 def test_case_15_outcome_0(self):
  from sa.decision_coverage import decision_case_15
  self.assertIn('started', decision_case_15('ready', True, 0, 1))
 def test_case_15_outcome_1(self):
  from sa.decision_coverage import decision_case_15
  self.assertIn('failed', decision_case_15('failed', False, 0, 1))
 def test_case_15_outcome_2(self):
  from sa.decision_coverage import decision_case_15
  self.assertIn('unknown', decision_case_15('ready', False, 0, 1))
 def test_case_15_outcome_3(self):
  from sa.decision_coverage import decision_case_15
  self.assertIn('priority', decision_case_15('queued', True, 0, 9))
 def test_case_15_outcome_4(self):
  from sa.decision_coverage import decision_case_15
  self.assertIn('retry', decision_case_15('ready', True, 5, 1))
 def test_case_15_outcome_5(self):
  from sa.decision_coverage import decision_case_15
  self.assertIn('started', decision_case_15('ready', True, 0, 1))
 def test_case_16_outcome_0(self):
  from sa.decision_coverage import decision_case_16
  self.assertIn('started', decision_case_16('ready', True, 0, 1))
 def test_case_16_outcome_1(self):
  from sa.decision_coverage import decision_case_16
  self.assertIn('failed', decision_case_16('failed', False, 0, 1))
 def test_case_16_outcome_2(self):
  from sa.decision_coverage import decision_case_16
  self.assertIn('unknown', decision_case_16('ready', False, 0, 1))
 def test_case_16_outcome_3(self):
  from sa.decision_coverage import decision_case_16
  self.assertIn('priority', decision_case_16('queued', True, 0, 9))
 def test_case_16_outcome_4(self):
  from sa.decision_coverage import decision_case_16
  self.assertIn('retry', decision_case_16('ready', True, 5, 1))
 def test_case_16_outcome_5(self):
  from sa.decision_coverage import decision_case_16
  self.assertIn('started', decision_case_16('ready', True, 0, 1))
 def test_case_17_outcome_0(self):
  from sa.decision_coverage import decision_case_17
  self.assertIn('started', decision_case_17('ready', True, 0, 1))
 def test_case_17_outcome_1(self):
  from sa.decision_coverage import decision_case_17
  self.assertIn('failed', decision_case_17('failed', False, 0, 1))
 def test_case_17_outcome_2(self):
  from sa.decision_coverage import decision_case_17
  self.assertIn('unknown', decision_case_17('ready', False, 0, 1))
 def test_case_17_outcome_3(self):
  from sa.decision_coverage import decision_case_17
  self.assertIn('priority', decision_case_17('queued', True, 0, 9))
 def test_case_17_outcome_4(self):
  from sa.decision_coverage import decision_case_17
  self.assertIn('retry', decision_case_17('ready', True, 5, 1))
 def test_case_17_outcome_5(self):
  from sa.decision_coverage import decision_case_17
  self.assertIn('started', decision_case_17('ready', True, 0, 1))
 def test_case_18_outcome_0(self):
  from sa.decision_coverage import decision_case_18
  self.assertIn('started', decision_case_18('ready', True, 0, 1))
 def test_case_18_outcome_1(self):
  from sa.decision_coverage import decision_case_18
  self.assertIn('failed', decision_case_18('failed', False, 0, 1))
 def test_case_18_outcome_2(self):
  from sa.decision_coverage import decision_case_18
  self.assertIn('unknown', decision_case_18('ready', False, 0, 1))
 def test_case_18_outcome_3(self):
  from sa.decision_coverage import decision_case_18
  self.assertIn('priority', decision_case_18('queued', True, 0, 9))
 def test_case_18_outcome_4(self):
  from sa.decision_coverage import decision_case_18
  self.assertIn('retry', decision_case_18('ready', True, 5, 1))
 def test_case_18_outcome_5(self):
  from sa.decision_coverage import decision_case_18
  self.assertIn('started', decision_case_18('ready', True, 0, 1))
 def test_case_19_outcome_0(self):
  from sa.decision_coverage import decision_case_19
  self.assertIn('started', decision_case_19('ready', True, 0, 1))
 def test_case_19_outcome_1(self):
  from sa.decision_coverage import decision_case_19
  self.assertIn('failed', decision_case_19('failed', False, 0, 1))
 def test_case_19_outcome_2(self):
  from sa.decision_coverage import decision_case_19
  self.assertIn('unknown', decision_case_19('ready', False, 0, 1))
 def test_case_19_outcome_3(self):
  from sa.decision_coverage import decision_case_19
  self.assertIn('priority', decision_case_19('queued', True, 0, 9))
 def test_case_19_outcome_4(self):
  from sa.decision_coverage import decision_case_19
  self.assertIn('retry', decision_case_19('ready', True, 5, 1))
 def test_case_19_outcome_5(self):
  from sa.decision_coverage import decision_case_19
  self.assertIn('started', decision_case_19('ready', True, 0, 1))
 def test_aggregate_empty(self):
  from sa.decision_coverage import aggregate_decision_coverage
  self.assertEqual(aggregate_decision_coverage([]), 1.0)
 def test_aggregate_partial(self):
  from sa.decision_coverage import aggregate_decision_coverage
  self.assertEqual(aggregate_decision_coverage([{'covered': True}, {'covered': False}]), 0.5)
