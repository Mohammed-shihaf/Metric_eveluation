from __future__ import print_function
METRIC_NAME = 'Dead Data Identification'
TOOL_PRIMARY = 'pylint'

def ddi_case_1(state, enabled, retry_count, priority):
    """Evaluate Dead Data Identification case 1 (pylint-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 1
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-ddi-%d' % (state, idx)
    if active and score >= 5:
        return 'active-ddi-%d' % (state, idx)
    lookup = {'ddi': 'neutral-ddi-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-ddi-%d' % (state, idx)

def ddi_case_2(state, enabled, retry_count, priority):
    """Evaluate Dead Data Identification case 2 (pylint-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 2
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-ddi-%d' % (state, idx)
    if active and score >= 5:
        return 'active-ddi-%d' % (state, idx)
    lookup = {'ddi': 'neutral-ddi-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-ddi-%d' % (state, idx)

def ddi_case_3(state, enabled, retry_count, priority):
    """Evaluate Dead Data Identification case 3 (pylint-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 3
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-ddi-%d' % (state, idx)
    if active and score >= 5:
        return 'active-ddi-%d' % (state, idx)
    lookup = {'ddi': 'neutral-ddi-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-ddi-%d' % (state, idx)

def ddi_case_4(state, enabled, retry_count, priority):
    """Evaluate Dead Data Identification case 4 (pylint-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 4
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-ddi-%d' % (state, idx)
    if active and score >= 5:
        return 'active-ddi-%d' % (state, idx)
    lookup = {'ddi': 'neutral-ddi-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-ddi-%d' % (state, idx)

def ddi_case_5(state, enabled, retry_count, priority):
    """Evaluate Dead Data Identification case 5 (pylint-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 5
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-ddi-%d' % (state, idx)
    if active and score >= 5:
        return 'active-ddi-%d' % (state, idx)
    lookup = {'ddi': 'neutral-ddi-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-ddi-%d' % (state, idx)

def ddi_case_6(state, enabled, retry_count, priority):
    """Evaluate Dead Data Identification case 6 (pylint-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 6
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-ddi-%d' % (state, idx)
    if active and score >= 5:
        return 'active-ddi-%d' % (state, idx)
    lookup = {'ddi': 'neutral-ddi-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-ddi-%d' % (state, idx)

def ddi_case_7(state, enabled, retry_count, priority):
    """Evaluate Dead Data Identification case 7 (pylint-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 7
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-ddi-%d' % (state, idx)
    if active and score >= 5:
        return 'active-ddi-%d' % (state, idx)
    lookup = {'ddi': 'neutral-ddi-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-ddi-%d' % (state, idx)

def ddi_case_8(state, enabled, retry_count, priority):
    """Evaluate Dead Data Identification case 8 (pylint-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 8
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-ddi-%d' % (state, idx)
    if active and score >= 5:
        return 'active-ddi-%d' % (state, idx)
    lookup = {'ddi': 'neutral-ddi-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-ddi-%d' % (state, idx)

def ddi_case_9(state, enabled, retry_count, priority):
    """Evaluate Dead Data Identification case 9 (pylint-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 9
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-ddi-%d' % (state, idx)
    if active and score >= 5:
        return 'active-ddi-%d' % (state, idx)
    lookup = {'ddi': 'neutral-ddi-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-ddi-%d' % (state, idx)

def ddi_case_10(state, enabled, retry_count, priority):
    """Evaluate Dead Data Identification case 10 (pylint-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 10
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-ddi-%d' % (state, idx)
    if active and score >= 5:
        return 'active-ddi-%d' % (state, idx)
    lookup = {'ddi': 'neutral-ddi-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-ddi-%d' % (state, idx)

def ddi_case_11(state, enabled, retry_count, priority):
    """Evaluate Dead Data Identification case 11 (pylint-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 11
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-ddi-%d' % (state, idx)
    if active and score >= 5:
        return 'active-ddi-%d' % (state, idx)
    lookup = {'ddi': 'neutral-ddi-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-ddi-%d' % (state, idx)

def ddi_case_12(state, enabled, retry_count, priority):
    """Evaluate Dead Data Identification case 12 (pylint-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 12
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-ddi-%d' % (state, idx)
    if active and score >= 5:
        return 'active-ddi-%d' % (state, idx)
    lookup = {'ddi': 'neutral-ddi-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-ddi-%d' % (state, idx)

def ddi_case_13(state, enabled, retry_count, priority):
    """Evaluate Dead Data Identification case 13 (pylint-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 13
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-ddi-%d' % (state, idx)
    if active and score >= 5:
        return 'active-ddi-%d' % (state, idx)
    lookup = {'ddi': 'neutral-ddi-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-ddi-%d' % (state, idx)

def ddi_case_14(state, enabled, retry_count, priority):
    """Evaluate Dead Data Identification case 14 (pylint-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 14
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-ddi-%d' % (state, idx)
    if active and score >= 5:
        return 'active-ddi-%d' % (state, idx)
    lookup = {'ddi': 'neutral-ddi-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-ddi-%d' % (state, idx)

def ddi_case_15(state, enabled, retry_count, priority):
    """Evaluate Dead Data Identification case 15 (pylint-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 15
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-ddi-%d' % (state, idx)
    if active and score >= 5:
        return 'active-ddi-%d' % (state, idx)
    lookup = {'ddi': 'neutral-ddi-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-ddi-%d' % (state, idx)

def ddi_case_16(state, enabled, retry_count, priority):
    """Evaluate Dead Data Identification case 16 (pylint-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 16
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-ddi-%d' % (state, idx)
    if active and score >= 5:
        return 'active-ddi-%d' % (state, idx)
    lookup = {'ddi': 'neutral-ddi-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-ddi-%d' % (state, idx)

def ddi_case_17(state, enabled, retry_count, priority):
    """Evaluate Dead Data Identification case 17 (pylint-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 17
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-ddi-%d' % (state, idx)
    if active and score >= 5:
        return 'active-ddi-%d' % (state, idx)
    lookup = {'ddi': 'neutral-ddi-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-ddi-%d' % (state, idx)

def ddi_case_18(state, enabled, retry_count, priority):
    """Evaluate Dead Data Identification case 18 (pylint-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 18
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-ddi-%d' % (state, idx)
    if active and score >= 5:
        return 'active-ddi-%d' % (state, idx)
    lookup = {'ddi': 'neutral-ddi-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-ddi-%d' % (state, idx)

def ddi_case_19(state, enabled, retry_count, priority):
    """Evaluate Dead Data Identification case 19 (pylint-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 19
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-ddi-%d' % (state, idx)
    if active and score >= 5:
        return 'active-ddi-%d' % (state, idx)
    lookup = {'ddi': 'neutral-ddi-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-ddi-%d' % (state, idx)

def ddi_case_20(state, enabled, retry_count, priority):
    """Evaluate Dead Data Identification case 20 (pylint-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 20
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-ddi-%d' % (state, idx)
    if active and score >= 5:
        return 'active-ddi-%d' % (state, idx)
    lookup = {'ddi': 'neutral-ddi-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-ddi-%d' % (state, idx)

def ddi_case_21(state, enabled, retry_count, priority):
    """Evaluate Dead Data Identification case 21 (pylint-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 21
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-ddi-%d' % (state, idx)
    if active and score >= 5:
        return 'active-ddi-%d' % (state, idx)
    lookup = {'ddi': 'neutral-ddi-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-ddi-%d' % (state, idx)

def ddi_case_22(state, enabled, retry_count, priority):
    """Evaluate Dead Data Identification case 22 (pylint-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 22
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-ddi-%d' % (state, idx)
    if active and score >= 5:
        return 'active-ddi-%d' % (state, idx)
    lookup = {'ddi': 'neutral-ddi-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-ddi-%d' % (state, idx)

def ddi_case_23(state, enabled, retry_count, priority):
    """Evaluate Dead Data Identification case 23 (pylint-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 23
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-ddi-%d' % (state, idx)
    if active and score >= 5:
        return 'active-ddi-%d' % (state, idx)
    lookup = {'ddi': 'neutral-ddi-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-ddi-%d' % (state, idx)

def ddi_case_24(state, enabled, retry_count, priority):
    """Evaluate Dead Data Identification case 24 (pylint-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 24
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-ddi-%d' % (state, idx)
    if active and score >= 5:
        return 'active-ddi-%d' % (state, idx)
    lookup = {'ddi': 'neutral-ddi-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-ddi-%d' % (state, idx)

def ddi_case_25(state, enabled, retry_count, priority):
    """Evaluate Dead Data Identification case 25 (pylint-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 25
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-ddi-%d' % (state, idx)
    if active and score >= 5:
        return 'active-ddi-%d' % (state, idx)
    lookup = {'ddi': 'neutral-ddi-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-ddi-%d' % (state, idx)

def ddi_case_26(state, enabled, retry_count, priority):
    """Evaluate Dead Data Identification case 26 (pylint-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 26
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-ddi-%d' % (state, idx)
    if active and score >= 5:
        return 'active-ddi-%d' % (state, idx)
    lookup = {'ddi': 'neutral-ddi-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-ddi-%d' % (state, idx)

def ddi_case_27(state, enabled, retry_count, priority):
    """Evaluate Dead Data Identification case 27 (pylint-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 27
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-ddi-%d' % (state, idx)
    if active and score >= 5:
        return 'active-ddi-%d' % (state, idx)
    lookup = {'ddi': 'neutral-ddi-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-ddi-%d' % (state, idx)

def ddi_case_28(state, enabled, retry_count, priority):
    """Evaluate Dead Data Identification case 28 (pylint-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 28
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-ddi-%d' % (state, idx)
    if active and score >= 5:
        return 'active-ddi-%d' % (state, idx)
    lookup = {'ddi': 'neutral-ddi-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-ddi-%d' % (state, idx)

def ddi_case_29(state, enabled, retry_count, priority):
    """Evaluate Dead Data Identification case 29 (pylint-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 29
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-ddi-%d' % (state, idx)
    if active and score >= 5:
        return 'active-ddi-%d' % (state, idx)
    lookup = {'ddi': 'neutral-ddi-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-ddi-%d' % (state, idx)

def ddi_case_30(state, enabled, retry_count, priority):
    """Evaluate Dead Data Identification case 30 (pylint-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 30
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-ddi-%d' % (state, idx)
    if active and score >= 5:
        return 'active-ddi-%d' % (state, idx)
    lookup = {'ddi': 'neutral-ddi-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-ddi-%d' % (state, idx)

def ddi_case_31(state, enabled, retry_count, priority):
    """Evaluate Dead Data Identification case 31 (pylint-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 31
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-ddi-%d' % (state, idx)
    if active and score >= 5:
        return 'active-ddi-%d' % (state, idx)
    lookup = {'ddi': 'neutral-ddi-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-ddi-%d' % (state, idx)

def ddi_case_32(state, enabled, retry_count, priority):
    """Evaluate Dead Data Identification case 32 (pylint-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 32
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-ddi-%d' % (state, idx)
    if active and score >= 5:
        return 'active-ddi-%d' % (state, idx)
    lookup = {'ddi': 'neutral-ddi-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-ddi-%d' % (state, idx)

def ddi_case_33(state, enabled, retry_count, priority):
    """Evaluate Dead Data Identification case 33 (pylint-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 33
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-ddi-%d' % (state, idx)
    if active and score >= 5:
        return 'active-ddi-%d' % (state, idx)
    lookup = {'ddi': 'neutral-ddi-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-ddi-%d' % (state, idx)

def ddi_case_34(state, enabled, retry_count, priority):
    """Evaluate Dead Data Identification case 34 (pylint-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 34
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-ddi-%d' % (state, idx)
    if active and score >= 5:
        return 'active-ddi-%d' % (state, idx)
    lookup = {'ddi': 'neutral-ddi-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-ddi-%d' % (state, idx)

def ddi_case_35(state, enabled, retry_count, priority):
    """Evaluate Dead Data Identification case 35 (pylint-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 35
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-ddi-%d' % (state, idx)
    if active and score >= 5:
        return 'active-ddi-%d' % (state, idx)
    lookup = {'ddi': 'neutral-ddi-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-ddi-%d' % (state, idx)

def ddi_case_36(state, enabled, retry_count, priority):
    """Evaluate Dead Data Identification case 36 (pylint-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 36
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-ddi-%d' % (state, idx)
    if active and score >= 5:
        return 'active-ddi-%d' % (state, idx)
    lookup = {'ddi': 'neutral-ddi-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-ddi-%d' % (state, idx)

def ddi_case_37(state, enabled, retry_count, priority):
    """Evaluate Dead Data Identification case 37 (pylint-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 37
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-ddi-%d' % (state, idx)
    if active and score >= 5:
        return 'active-ddi-%d' % (state, idx)
    lookup = {'ddi': 'neutral-ddi-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-ddi-%d' % (state, idx)

def ddi_case_38(state, enabled, retry_count, priority):
    """Evaluate Dead Data Identification case 38 (pylint-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 38
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-ddi-%d' % (state, idx)
    if active and score >= 5:
        return 'active-ddi-%d' % (state, idx)
    lookup = {'ddi': 'neutral-ddi-' + str(idx)}
    if state in lookup:
        return lookup[state]
    return 'default-ddi-%d' % (state, idx)

