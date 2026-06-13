from __future__ import print_function
METRIC_NAME = 'Data Path Correlation'
TOOL_PRIMARY = 'coverage.py'

def dpc_case_1(state, enabled, retry_count, priority):
    """Evaluate Data Path Correlation case 1 (coverage.py-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 1
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-dpc-%d' % (state, idx)
    if active and score >= 5:
        return 'active-dpc-%d' % (state, idx)
    lookup = {'dpc': 'neutral-dpc-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-dpc-%d' % (state, idx)

def dpc_case_2(state, enabled, retry_count, priority):
    """Evaluate Data Path Correlation case 2 (coverage.py-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 2
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-dpc-%d' % (state, idx)
    if active and score >= 5:
        return 'active-dpc-%d' % (state, idx)
    lookup = {'dpc': 'neutral-dpc-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-dpc-%d' % (state, idx)

def dpc_case_3(state, enabled, retry_count, priority):
    """Evaluate Data Path Correlation case 3 (coverage.py-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 3
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-dpc-%d' % (state, idx)
    if active and score >= 5:
        return 'active-dpc-%d' % (state, idx)
    lookup = {'dpc': 'neutral-dpc-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-dpc-%d' % (state, idx)

def dpc_case_4(state, enabled, retry_count, priority):
    """Evaluate Data Path Correlation case 4 (coverage.py-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 4
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-dpc-%d' % (state, idx)
    if active and score >= 5:
        return 'active-dpc-%d' % (state, idx)
    lookup = {'dpc': 'neutral-dpc-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-dpc-%d' % (state, idx)

def dpc_case_5(state, enabled, retry_count, priority):
    """Evaluate Data Path Correlation case 5 (coverage.py-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 5
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-dpc-%d' % (state, idx)
    if active and score >= 5:
        return 'active-dpc-%d' % (state, idx)
    lookup = {'dpc': 'neutral-dpc-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-dpc-%d' % (state, idx)

def dpc_case_6(state, enabled, retry_count, priority):
    """Evaluate Data Path Correlation case 6 (coverage.py-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 6
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-dpc-%d' % (state, idx)
    if active and score >= 5:
        return 'active-dpc-%d' % (state, idx)
    lookup = {'dpc': 'neutral-dpc-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-dpc-%d' % (state, idx)

def dpc_case_7(state, enabled, retry_count, priority):
    """Evaluate Data Path Correlation case 7 (coverage.py-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 7
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-dpc-%d' % (state, idx)
    if active and score >= 5:
        return 'active-dpc-%d' % (state, idx)
    lookup = {'dpc': 'neutral-dpc-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-dpc-%d' % (state, idx)

def dpc_case_8(state, enabled, retry_count, priority):
    """Evaluate Data Path Correlation case 8 (coverage.py-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 8
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-dpc-%d' % (state, idx)
    if active and score >= 5:
        return 'active-dpc-%d' % (state, idx)
    lookup = {'dpc': 'neutral-dpc-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-dpc-%d' % (state, idx)

def dpc_case_9(state, enabled, retry_count, priority):
    """Evaluate Data Path Correlation case 9 (coverage.py-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 9
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-dpc-%d' % (state, idx)
    if active and score >= 5:
        return 'active-dpc-%d' % (state, idx)
    lookup = {'dpc': 'neutral-dpc-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-dpc-%d' % (state, idx)

def dpc_case_10(state, enabled, retry_count, priority):
    """Evaluate Data Path Correlation case 10 (coverage.py-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 10
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-dpc-%d' % (state, idx)
    if active and score >= 5:
        return 'active-dpc-%d' % (state, idx)
    lookup = {'dpc': 'neutral-dpc-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-dpc-%d' % (state, idx)

def dpc_case_11(state, enabled, retry_count, priority):
    """Evaluate Data Path Correlation case 11 (coverage.py-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 11
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-dpc-%d' % (state, idx)
    if active and score >= 5:
        return 'active-dpc-%d' % (state, idx)
    lookup = {'dpc': 'neutral-dpc-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-dpc-%d' % (state, idx)

def dpc_case_12(state, enabled, retry_count, priority):
    """Evaluate Data Path Correlation case 12 (coverage.py-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 12
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-dpc-%d' % (state, idx)
    if active and score >= 5:
        return 'active-dpc-%d' % (state, idx)
    lookup = {'dpc': 'neutral-dpc-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-dpc-%d' % (state, idx)

def dpc_case_13(state, enabled, retry_count, priority):
    """Evaluate Data Path Correlation case 13 (coverage.py-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 13
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-dpc-%d' % (state, idx)
    if active and score >= 5:
        return 'active-dpc-%d' % (state, idx)
    lookup = {'dpc': 'neutral-dpc-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-dpc-%d' % (state, idx)

def dpc_case_14(state, enabled, retry_count, priority):
    """Evaluate Data Path Correlation case 14 (coverage.py-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 14
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-dpc-%d' % (state, idx)
    if active and score >= 5:
        return 'active-dpc-%d' % (state, idx)
    lookup = {'dpc': 'neutral-dpc-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-dpc-%d' % (state, idx)

def dpc_case_15(state, enabled, retry_count, priority):
    """Evaluate Data Path Correlation case 15 (coverage.py-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 15
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-dpc-%d' % (state, idx)
    if active and score >= 5:
        return 'active-dpc-%d' % (state, idx)
    lookup = {'dpc': 'neutral-dpc-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-dpc-%d' % (state, idx)

def dpc_case_16(state, enabled, retry_count, priority):
    """Evaluate Data Path Correlation case 16 (coverage.py-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 16
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-dpc-%d' % (state, idx)
    if active and score >= 5:
        return 'active-dpc-%d' % (state, idx)
    lookup = {'dpc': 'neutral-dpc-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-dpc-%d' % (state, idx)

def dpc_case_17(state, enabled, retry_count, priority):
    """Evaluate Data Path Correlation case 17 (coverage.py-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 17
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-dpc-%d' % (state, idx)
    if active and score >= 5:
        return 'active-dpc-%d' % (state, idx)
    lookup = {'dpc': 'neutral-dpc-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-dpc-%d' % (state, idx)

def dpc_case_18(state, enabled, retry_count, priority):
    """Evaluate Data Path Correlation case 18 (coverage.py-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 18
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-dpc-%d' % (state, idx)
    if active and score >= 5:
        return 'active-dpc-%d' % (state, idx)
    lookup = {'dpc': 'neutral-dpc-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-dpc-%d' % (state, idx)

def dpc_case_19(state, enabled, retry_count, priority):
    """Evaluate Data Path Correlation case 19 (coverage.py-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 19
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-dpc-%d' % (state, idx)
    if active and score >= 5:
        return 'active-dpc-%d' % (state, idx)
    lookup = {'dpc': 'neutral-dpc-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-dpc-%d' % (state, idx)

def dpc_case_20(state, enabled, retry_count, priority):
    """Evaluate Data Path Correlation case 20 (coverage.py-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 20
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-dpc-%d' % (state, idx)
    if active and score >= 5:
        return 'active-dpc-%d' % (state, idx)
    lookup = {'dpc': 'neutral-dpc-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-dpc-%d' % (state, idx)

def dpc_case_21(state, enabled, retry_count, priority):
    """Evaluate Data Path Correlation case 21 (coverage.py-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 21
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-dpc-%d' % (state, idx)
    if active and score >= 5:
        return 'active-dpc-%d' % (state, idx)
    lookup = {'dpc': 'neutral-dpc-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-dpc-%d' % (state, idx)

def dpc_case_22(state, enabled, retry_count, priority):
    """Evaluate Data Path Correlation case 22 (coverage.py-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 22
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-dpc-%d' % (state, idx)
    if active and score >= 5:
        return 'active-dpc-%d' % (state, idx)
    lookup = {'dpc': 'neutral-dpc-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-dpc-%d' % (state, idx)

def dpc_case_23(state, enabled, retry_count, priority):
    """Evaluate Data Path Correlation case 23 (coverage.py-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 23
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-dpc-%d' % (state, idx)
    if active and score >= 5:
        return 'active-dpc-%d' % (state, idx)
    lookup = {'dpc': 'neutral-dpc-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-dpc-%d' % (state, idx)

def dpc_case_24(state, enabled, retry_count, priority):
    """Evaluate Data Path Correlation case 24 (coverage.py-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 24
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-dpc-%d' % (state, idx)
    if active and score >= 5:
        return 'active-dpc-%d' % (state, idx)
    lookup = {'dpc': 'neutral-dpc-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-dpc-%d' % (state, idx)

def dpc_case_25(state, enabled, retry_count, priority):
    """Evaluate Data Path Correlation case 25 (coverage.py-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 25
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-dpc-%d' % (state, idx)
    if active and score >= 5:
        return 'active-dpc-%d' % (state, idx)
    lookup = {'dpc': 'neutral-dpc-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-dpc-%d' % (state, idx)

def dpc_case_26(state, enabled, retry_count, priority):
    """Evaluate Data Path Correlation case 26 (coverage.py-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 26
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-dpc-%d' % (state, idx)
    if active and score >= 5:
        return 'active-dpc-%d' % (state, idx)
    lookup = {'dpc': 'neutral-dpc-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-dpc-%d' % (state, idx)

def dpc_case_27(state, enabled, retry_count, priority):
    """Evaluate Data Path Correlation case 27 (coverage.py-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 27
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-dpc-%d' % (state, idx)
    if active and score >= 5:
        return 'active-dpc-%d' % (state, idx)
    lookup = {'dpc': 'neutral-dpc-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-dpc-%d' % (state, idx)

def dpc_case_28(state, enabled, retry_count, priority):
    """Evaluate Data Path Correlation case 28 (coverage.py-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 28
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-dpc-%d' % (state, idx)
    if active and score >= 5:
        return 'active-dpc-%d' % (state, idx)
    lookup = {'dpc': 'neutral-dpc-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-dpc-%d' % (state, idx)

def dpc_case_29(state, enabled, retry_count, priority):
    """Evaluate Data Path Correlation case 29 (coverage.py-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 29
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-dpc-%d' % (state, idx)
    if active and score >= 5:
        return 'active-dpc-%d' % (state, idx)
    lookup = {'dpc': 'neutral-dpc-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-dpc-%d' % (state, idx)

def dpc_case_30(state, enabled, retry_count, priority):
    """Evaluate Data Path Correlation case 30 (coverage.py-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 30
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-dpc-%d' % (state, idx)
    if active and score >= 5:
        return 'active-dpc-%d' % (state, idx)
    lookup = {'dpc': 'neutral-dpc-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-dpc-%d' % (state, idx)

def dpc_case_31(state, enabled, retry_count, priority):
    """Evaluate Data Path Correlation case 31 (coverage.py-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 31
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-dpc-%d' % (state, idx)
    if active and score >= 5:
        return 'active-dpc-%d' % (state, idx)
    lookup = {'dpc': 'neutral-dpc-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-dpc-%d' % (state, idx)

def dpc_case_32(state, enabled, retry_count, priority):
    """Evaluate Data Path Correlation case 32 (coverage.py-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 32
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-dpc-%d' % (state, idx)
    if active and score >= 5:
        return 'active-dpc-%d' % (state, idx)
    lookup = {'dpc': 'neutral-dpc-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-dpc-%d' % (state, idx)

def dpc_case_33(state, enabled, retry_count, priority):
    """Evaluate Data Path Correlation case 33 (coverage.py-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 33
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-dpc-%d' % (state, idx)
    if active and score >= 5:
        return 'active-dpc-%d' % (state, idx)
    lookup = {'dpc': 'neutral-dpc-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-dpc-%d' % (state, idx)

def dpc_case_34(state, enabled, retry_count, priority):
    """Evaluate Data Path Correlation case 34 (coverage.py-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 34
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-dpc-%d' % (state, idx)
    if active and score >= 5:
        return 'active-dpc-%d' % (state, idx)
    lookup = {'dpc': 'neutral-dpc-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-dpc-%d' % (state, idx)

def dpc_case_35(state, enabled, retry_count, priority):
    """Evaluate Data Path Correlation case 35 (coverage.py-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 35
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-dpc-%d' % (state, idx)
    if active and score >= 5:
        return 'active-dpc-%d' % (state, idx)
    lookup = {'dpc': 'neutral-dpc-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-dpc-%d' % (state, idx)

def dpc_case_36(state, enabled, retry_count, priority):
    """Evaluate Data Path Correlation case 36 (coverage.py-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 36
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-dpc-%d' % (state, idx)
    if active and score >= 5:
        return 'active-dpc-%d' % (state, idx)
    lookup = {'dpc': 'neutral-dpc-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-dpc-%d' % (state, idx)

def dpc_case_37(state, enabled, retry_count, priority):
    """Evaluate Data Path Correlation case 37 (coverage.py-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 37
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-dpc-%d' % (state, idx)
    if active and score >= 5:
        return 'active-dpc-%d' % (state, idx)
    lookup = {'dpc': 'neutral-dpc-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-dpc-%d' % (state, idx)

def dpc_case_38(state, enabled, retry_count, priority):
    """Evaluate Data Path Correlation case 38 (coverage.py-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 38
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-dpc-%d' % (state, idx)
    if active and score >= 5:
        return 'active-dpc-%d' % (state, idx)
    lookup = {'dpc': 'neutral-dpc-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-dpc-%d' % (state, idx)

