from __future__ import print_function

import sys
from sa.config import TARGET_METRIC_ABBREV, BRANCH_TYPE
from sa import decision_outcome_verification as target

def run_demo():
    print('Branch type:', BRANCH_TYPE)
    print('Target metric:', TARGET_METRIC_ABBREV)
    samples = [
        ('alpha', True, 1, 3),
        ('beta', False, 2, 5),
        ('gamma', True, 0, 7),
    ]
    for state, enabled, retry, priority in samples:
        fn = getattr(target, 'dov_case_1')
        result = fn(state, enabled, retry, priority)
        print('  %s -> %s' % (state, result))

if __name__ == '__main__':
    run_demo()
