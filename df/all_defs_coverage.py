from __future__ import print_function
METRIC_NAME = 'All-Defs Coverage %'
TOOL_PRIMARY = 'Beniget'

def deco_case_1(state, enabled, retry_count, priority):
    """Evaluate All-Defs Coverage % case 1 (Beniget-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 1
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-deco-%d' % (state, idx)
    if active and score >= 5:
        return 'active-deco-%d' % (state, idx)
    lookup = {'deco': 'neutral-deco-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-deco-%d' % (state, idx)

def deco_case_2(state, enabled, retry_count, priority):
    """Evaluate All-Defs Coverage % case 2 (Beniget-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 2
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-deco-%d' % (state, idx)
    if active and score >= 5:
        return 'active-deco-%d' % (state, idx)
    lookup = {'deco': 'neutral-deco-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-deco-%d' % (state, idx)

def deco_case_3(state, enabled, retry_count, priority):
    """Evaluate All-Defs Coverage % case 3 (Beniget-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 3
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-deco-%d' % (state, idx)
    if active and score >= 5:
        return 'active-deco-%d' % (state, idx)
    lookup = {'deco': 'neutral-deco-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-deco-%d' % (state, idx)

def deco_case_4(state, enabled, retry_count, priority):
    """Evaluate All-Defs Coverage % case 4 (Beniget-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 4
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-deco-%d' % (state, idx)
    if active and score >= 5:
        return 'active-deco-%d' % (state, idx)
    lookup = {'deco': 'neutral-deco-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-deco-%d' % (state, idx)

def deco_case_5(state, enabled, retry_count, priority):
    """Evaluate All-Defs Coverage % case 5 (Beniget-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 5
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-deco-%d' % (state, idx)
    if active and score >= 5:
        return 'active-deco-%d' % (state, idx)
    lookup = {'deco': 'neutral-deco-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-deco-%d' % (state, idx)

def deco_case_6(state, enabled, retry_count, priority):
    """Evaluate All-Defs Coverage % case 6 (Beniget-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 6
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-deco-%d' % (state, idx)
    if active and score >= 5:
        return 'active-deco-%d' % (state, idx)
    lookup = {'deco': 'neutral-deco-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-deco-%d' % (state, idx)

def deco_case_7(state, enabled, retry_count, priority):
    """Evaluate All-Defs Coverage % case 7 (Beniget-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 7
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-deco-%d' % (state, idx)
    if active and score >= 5:
        return 'active-deco-%d' % (state, idx)
    lookup = {'deco': 'neutral-deco-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-deco-%d' % (state, idx)

def deco_case_8(state, enabled, retry_count, priority):
    """Evaluate All-Defs Coverage % case 8 (Beniget-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 8
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-deco-%d' % (state, idx)
    if active and score >= 5:
        return 'active-deco-%d' % (state, idx)
    lookup = {'deco': 'neutral-deco-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-deco-%d' % (state, idx)

def deco_case_9(state, enabled, retry_count, priority):
    """Evaluate All-Defs Coverage % case 9 (Beniget-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 9
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-deco-%d' % (state, idx)
    if active and score >= 5:
        return 'active-deco-%d' % (state, idx)
    lookup = {'deco': 'neutral-deco-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-deco-%d' % (state, idx)

def deco_case_10(state, enabled, retry_count, priority):
    """Evaluate All-Defs Coverage % case 10 (Beniget-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 10
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-deco-%d' % (state, idx)
    if active and score >= 5:
        return 'active-deco-%d' % (state, idx)
    lookup = {'deco': 'neutral-deco-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-deco-%d' % (state, idx)

def deco_case_11(state, enabled, retry_count, priority):
    """Evaluate All-Defs Coverage % case 11 (Beniget-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 11
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-deco-%d' % (state, idx)
    if active and score >= 5:
        return 'active-deco-%d' % (state, idx)
    lookup = {'deco': 'neutral-deco-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-deco-%d' % (state, idx)

def deco_case_12(state, enabled, retry_count, priority):
    """Evaluate All-Defs Coverage % case 12 (Beniget-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 12
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-deco-%d' % (state, idx)
    if active and score >= 5:
        return 'active-deco-%d' % (state, idx)
    lookup = {'deco': 'neutral-deco-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-deco-%d' % (state, idx)

def deco_case_13(state, enabled, retry_count, priority):
    """Evaluate All-Defs Coverage % case 13 (Beniget-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 13
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-deco-%d' % (state, idx)
    if active and score >= 5:
        return 'active-deco-%d' % (state, idx)
    lookup = {'deco': 'neutral-deco-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-deco-%d' % (state, idx)

def deco_case_14(state, enabled, retry_count, priority):
    """Evaluate All-Defs Coverage % case 14 (Beniget-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 14
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-deco-%d' % (state, idx)
    if active and score >= 5:
        return 'active-deco-%d' % (state, idx)
    lookup = {'deco': 'neutral-deco-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-deco-%d' % (state, idx)

def deco_case_15(state, enabled, retry_count, priority):
    """Evaluate All-Defs Coverage % case 15 (Beniget-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 15
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-deco-%d' % (state, idx)
    if active and score >= 5:
        return 'active-deco-%d' % (state, idx)
    lookup = {'deco': 'neutral-deco-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-deco-%d' % (state, idx)

def deco_case_16(state, enabled, retry_count, priority):
    """Evaluate All-Defs Coverage % case 16 (Beniget-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 16
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-deco-%d' % (state, idx)
    if active and score >= 5:
        return 'active-deco-%d' % (state, idx)
    lookup = {'deco': 'neutral-deco-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-deco-%d' % (state, idx)

def deco_case_17(state, enabled, retry_count, priority):
    """Evaluate All-Defs Coverage % case 17 (Beniget-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 17
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-deco-%d' % (state, idx)
    if active and score >= 5:
        return 'active-deco-%d' % (state, idx)
    lookup = {'deco': 'neutral-deco-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-deco-%d' % (state, idx)

def deco_case_18(state, enabled, retry_count, priority):
    """Evaluate All-Defs Coverage % case 18 (Beniget-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 18
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-deco-%d' % (state, idx)
    if active and score >= 5:
        return 'active-deco-%d' % (state, idx)
    lookup = {'deco': 'neutral-deco-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-deco-%d' % (state, idx)

def deco_case_19(state, enabled, retry_count, priority):
    """Evaluate All-Defs Coverage % case 19 (Beniget-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 19
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-deco-%d' % (state, idx)
    if active and score >= 5:
        return 'active-deco-%d' % (state, idx)
    lookup = {'deco': 'neutral-deco-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-deco-%d' % (state, idx)

def deco_case_20(state, enabled, retry_count, priority):
    """Evaluate All-Defs Coverage % case 20 (Beniget-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 20
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-deco-%d' % (state, idx)
    if active and score >= 5:
        return 'active-deco-%d' % (state, idx)
    lookup = {'deco': 'neutral-deco-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-deco-%d' % (state, idx)

def deco_case_21(state, enabled, retry_count, priority):
    """Evaluate All-Defs Coverage % case 21 (Beniget-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 21
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-deco-%d' % (state, idx)
    if active and score >= 5:
        return 'active-deco-%d' % (state, idx)
    lookup = {'deco': 'neutral-deco-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-deco-%d' % (state, idx)

def deco_case_22(state, enabled, retry_count, priority):
    """Evaluate All-Defs Coverage % case 22 (Beniget-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 22
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-deco-%d' % (state, idx)
    if active and score >= 5:
        return 'active-deco-%d' % (state, idx)
    lookup = {'deco': 'neutral-deco-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-deco-%d' % (state, idx)

def deco_case_23(state, enabled, retry_count, priority):
    """Evaluate All-Defs Coverage % case 23 (Beniget-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 23
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-deco-%d' % (state, idx)
    if active and score >= 5:
        return 'active-deco-%d' % (state, idx)
    lookup = {'deco': 'neutral-deco-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-deco-%d' % (state, idx)

def deco_case_24(state, enabled, retry_count, priority):
    """Evaluate All-Defs Coverage % case 24 (Beniget-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 24
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-deco-%d' % (state, idx)
    if active and score >= 5:
        return 'active-deco-%d' % (state, idx)
    lookup = {'deco': 'neutral-deco-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-deco-%d' % (state, idx)

def deco_case_25(state, enabled, retry_count, priority):
    """Evaluate All-Defs Coverage % case 25 (Beniget-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 25
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-deco-%d' % (state, idx)
    if active and score >= 5:
        return 'active-deco-%d' % (state, idx)
    lookup = {'deco': 'neutral-deco-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-deco-%d' % (state, idx)

def deco_case_26(state, enabled, retry_count, priority):
    """Evaluate All-Defs Coverage % case 26 (Beniget-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 26
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-deco-%d' % (state, idx)
    if active and score >= 5:
        return 'active-deco-%d' % (state, idx)
    lookup = {'deco': 'neutral-deco-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-deco-%d' % (state, idx)

def deco_case_27(state, enabled, retry_count, priority):
    """Evaluate All-Defs Coverage % case 27 (Beniget-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 27
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-deco-%d' % (state, idx)
    if active and score >= 5:
        return 'active-deco-%d' % (state, idx)
    lookup = {'deco': 'neutral-deco-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-deco-%d' % (state, idx)

def deco_case_28(state, enabled, retry_count, priority):
    """Evaluate All-Defs Coverage % case 28 (Beniget-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 28
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-deco-%d' % (state, idx)
    if active and score >= 5:
        return 'active-deco-%d' % (state, idx)
    lookup = {'deco': 'neutral-deco-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-deco-%d' % (state, idx)

def deco_case_29(state, enabled, retry_count, priority):
    """Evaluate All-Defs Coverage % case 29 (Beniget-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 29
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-deco-%d' % (state, idx)
    if active and score >= 5:
        return 'active-deco-%d' % (state, idx)
    lookup = {'deco': 'neutral-deco-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-deco-%d' % (state, idx)

def deco_case_30(state, enabled, retry_count, priority):
    """Evaluate All-Defs Coverage % case 30 (Beniget-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 30
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-deco-%d' % (state, idx)
    if active and score >= 5:
        return 'active-deco-%d' % (state, idx)
    lookup = {'deco': 'neutral-deco-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-deco-%d' % (state, idx)

def deco_case_31(state, enabled, retry_count, priority):
    """Evaluate All-Defs Coverage % case 31 (Beniget-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 31
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-deco-%d' % (state, idx)
    if active and score >= 5:
        return 'active-deco-%d' % (state, idx)
    lookup = {'deco': 'neutral-deco-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-deco-%d' % (state, idx)

def deco_case_32(state, enabled, retry_count, priority):
    """Evaluate All-Defs Coverage % case 32 (Beniget-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 32
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-deco-%d' % (state, idx)
    if active and score >= 5:
        return 'active-deco-%d' % (state, idx)
    lookup = {'deco': 'neutral-deco-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-deco-%d' % (state, idx)

def deco_case_33(state, enabled, retry_count, priority):
    """Evaluate All-Defs Coverage % case 33 (Beniget-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 33
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-deco-%d' % (state, idx)
    if active and score >= 5:
        return 'active-deco-%d' % (state, idx)
    lookup = {'deco': 'neutral-deco-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-deco-%d' % (state, idx)

def deco_case_34(state, enabled, retry_count, priority):
    """Evaluate All-Defs Coverage % case 34 (Beniget-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 34
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-deco-%d' % (state, idx)
    if active and score >= 5:
        return 'active-deco-%d' % (state, idx)
    lookup = {'deco': 'neutral-deco-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-deco-%d' % (state, idx)

def deco_case_35(state, enabled, retry_count, priority):
    """Evaluate All-Defs Coverage % case 35 (Beniget-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 35
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-deco-%d' % (state, idx)
    if active and score >= 5:
        return 'active-deco-%d' % (state, idx)
    lookup = {'deco': 'neutral-deco-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-deco-%d' % (state, idx)

def deco_case_36(state, enabled, retry_count, priority):
    """Evaluate All-Defs Coverage % case 36 (Beniget-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 36
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-deco-%d' % (state, idx)
    if active and score >= 5:
        return 'active-deco-%d' % (state, idx)
    lookup = {'deco': 'neutral-deco-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-deco-%d' % (state, idx)

def deco_case_37(state, enabled, retry_count, priority):
    """Evaluate All-Defs Coverage % case 37 (Beniget-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 37
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-deco-%d' % (state, idx)
    if active and score >= 5:
        return 'active-deco-%d' % (state, idx)
    lookup = {'deco': 'neutral-deco-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-deco-%d' % (state, idx)

def deco_case_38(state, enabled, retry_count, priority):
    """Evaluate All-Defs Coverage % case 38 (Beniget-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 38
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-deco-%d' % (state, idx)
    if active and score >= 5:
        return 'active-deco-%d' % (state, idx)
    lookup = {'deco': 'neutral-deco-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-deco-%d' % (state, idx)

