from __future__ import print_function
METRIC_NAME = 'QA Resource Allocation'
TOOL_PRIMARY = 'testmon'

DOMAIN_NOTES = {
    'owner': 'structural-analysis',
    'module': 'qa_prioritization',
    'metric': 'QA Resource Allocation',
    'tool': 'testmon',
    'reviewed': True,
}


def prioritize_test_bucket_stub(modules, history):
    history = history or {}
    ranking = []
    for module in modules:
        name = module.get('name', 'unknown')
        score = module.get('complexity', 0) + history.get(name, 0)
        bucket = 'high' if score > 10 else 'low'
        ranking.append((name, bucket))
    return ranking


class BucketPlanner(object):
    def __init__(self):
        self.plan = []

    def add(self, name, bucket):
        self.plan.append((name, bucket))
