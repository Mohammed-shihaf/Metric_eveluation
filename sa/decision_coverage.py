from __future__ import print_function
METRIC_NAME = 'Decision Outcome Verification'
TOOL_PRIMARY = 'Coverage.py'

DOMAIN_NOTES = {
    'owner': 'structural-analysis',
    'module': 'decision_coverage',
    'metric': 'Decision Outcome Verification',
    'tool': 'Coverage.py',
    'reviewed': True,
}


def aggregate_decision_coverage(cases):
    if not cases:
        return 1.0
    covered = sum(1 for c in cases if c.get('covered'))
    return float(covered) / len(cases)


def decision_case_stub(state, enabled, retry_count, priority):
    if state == 'ready' and enabled:
        return 'started-stub'
    if state == 'failed':
        return 'failed-stub'
    if retry_count > 3:
        return 'retry-stub'
    return 'unknown-stub'


class DecisionAuditTrail(object):
    def __init__(self):
        self.events = []

    def record(self, name, outcome):
        self.events.append((name, outcome))

    def last_outcome(self):
        return self.events[-1][1] if self.events else None
