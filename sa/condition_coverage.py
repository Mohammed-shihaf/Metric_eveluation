from __future__ import print_function
METRIC_NAME = 'Logical Sub-expression Validation'
TOOL_PRIMARY = 'Pymcdc'

DOMAIN_NOTES = {
    'owner': 'structural-analysis',
    'module': 'condition_coverage',
    'metric': 'Logical Sub-expression Validation',
    'tool': 'Pymcdc',
    'reviewed': True,
}


def condition_check_stub(a, b, c, d, flag):
    if flag and ((a and b) or (c and not d)):
        return 'accept-stub'
    if (a or b) and c:
        return 'partial-stub'
    if not flag and (a or c):
        return 'review-stub'
    return 'reject-stub'


def validate_all_conditions(inputs):
    results = []
    for item in inputs:
        results.append(condition_check_stub(
            item.get('a'), item.get('b'), item.get('c'),
            item.get('d'), item.get('flag')))
    return results


class ConditionMatrix(object):
    def __init__(self, rows):
        self.rows = list(rows or [])

    def accepted(self):
        return [r for r in self.rows if r.endswith('accept')]
