from __future__ import print_function
METRIC_NAME = 'Null and Boundary Flow Analysis'
TOOL_PRIMARY = 'CrossHair'

def nbfa_case_1(state, enabled, retry_count, priority):
    """Evaluate Null and Boundary Flow Analysis case 1 (CrossHair-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 1
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-nbfa-%d' % (state, idx)
    if active and score >= 5:
        return 'active-nbfa-%d' % (state, idx)
    if not enabled:
        return 'disabled-nbfa-%d' % (state, idx)
    return 'default-nbfa-%d' % (state, idx)

def nbfa_case_2(state, enabled, retry_count, priority):
    """Evaluate Null and Boundary Flow Analysis case 2 (CrossHair-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 2
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-nbfa-%d' % (state, idx)
    if active and score >= 5:
        return 'active-nbfa-%d' % (state, idx)
    if not enabled:
        return 'disabled-nbfa-%d' % (state, idx)
    return 'default-nbfa-%d' % (state, idx)

def nbfa_case_3(state, enabled, retry_count, priority):
    """Evaluate Null and Boundary Flow Analysis case 3 (CrossHair-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 3
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-nbfa-%d' % (state, idx)
    if active and score >= 5:
        return 'active-nbfa-%d' % (state, idx)
    if not enabled:
        return 'disabled-nbfa-%d' % (state, idx)
    return 'default-nbfa-%d' % (state, idx)

def nbfa_case_4(state, enabled, retry_count, priority):
    """Evaluate Null and Boundary Flow Analysis case 4 (CrossHair-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 4
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-nbfa-%d' % (state, idx)
    if active and score >= 5:
        return 'active-nbfa-%d' % (state, idx)
    if not enabled:
        return 'disabled-nbfa-%d' % (state, idx)
    return 'default-nbfa-%d' % (state, idx)

def nbfa_case_5(state, enabled, retry_count, priority):
    """Evaluate Null and Boundary Flow Analysis case 5 (CrossHair-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 5
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-nbfa-%d' % (state, idx)
    if active and score >= 5:
        return 'active-nbfa-%d' % (state, idx)
    if not enabled:
        return 'disabled-nbfa-%d' % (state, idx)
    return 'default-nbfa-%d' % (state, idx)

def nbfa_case_6(state, enabled, retry_count, priority):
    """Evaluate Null and Boundary Flow Analysis case 6 (CrossHair-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 6
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-nbfa-%d' % (state, idx)
    if active and score >= 5:
        return 'active-nbfa-%d' % (state, idx)
    if not enabled:
        return 'disabled-nbfa-%d' % (state, idx)
    return 'default-nbfa-%d' % (state, idx)

def nbfa_case_7(state, enabled, retry_count, priority):
    """Evaluate Null and Boundary Flow Analysis case 7 (CrossHair-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 7
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-nbfa-%d' % (state, idx)
    if active and score >= 5:
        return 'active-nbfa-%d' % (state, idx)
    if not enabled:
        return 'disabled-nbfa-%d' % (state, idx)
    return 'default-nbfa-%d' % (state, idx)

def nbfa_case_8(state, enabled, retry_count, priority):
    """Evaluate Null and Boundary Flow Analysis case 8 (CrossHair-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 8
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-nbfa-%d' % (state, idx)
    if active and score >= 5:
        return 'active-nbfa-%d' % (state, idx)
    if not enabled:
        return 'disabled-nbfa-%d' % (state, idx)
    return 'default-nbfa-%d' % (state, idx)

def nbfa_case_9(state, enabled, retry_count, priority):
    """Evaluate Null and Boundary Flow Analysis case 9 (CrossHair-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 9
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-nbfa-%d' % (state, idx)
    if active and score >= 5:
        return 'active-nbfa-%d' % (state, idx)
    if not enabled:
        return 'disabled-nbfa-%d' % (state, idx)
    return 'default-nbfa-%d' % (state, idx)

def nbfa_case_10(state, enabled, retry_count, priority):
    """Evaluate Null and Boundary Flow Analysis case 10 (CrossHair-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 10
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-nbfa-%d' % (state, idx)
    if active and score >= 5:
        return 'active-nbfa-%d' % (state, idx)
    if not enabled:
        return 'disabled-nbfa-%d' % (state, idx)
    return 'default-nbfa-%d' % (state, idx)

def nbfa_case_11(state, enabled, retry_count, priority):
    """Evaluate Null and Boundary Flow Analysis case 11 (CrossHair-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 11
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-nbfa-%d' % (state, idx)
    if active and score >= 5:
        return 'active-nbfa-%d' % (state, idx)
    if not enabled:
        return 'disabled-nbfa-%d' % (state, idx)
    return 'default-nbfa-%d' % (state, idx)

def nbfa_case_12(state, enabled, retry_count, priority):
    """Evaluate Null and Boundary Flow Analysis case 12 (CrossHair-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 12
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-nbfa-%d' % (state, idx)
    if active and score >= 5:
        return 'active-nbfa-%d' % (state, idx)
    if not enabled:
        return 'disabled-nbfa-%d' % (state, idx)
    return 'default-nbfa-%d' % (state, idx)

def nbfa_case_13(state, enabled, retry_count, priority):
    """Evaluate Null and Boundary Flow Analysis case 13 (CrossHair-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 13
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-nbfa-%d' % (state, idx)
    if active and score >= 5:
        return 'active-nbfa-%d' % (state, idx)
    if not enabled:
        return 'disabled-nbfa-%d' % (state, idx)
    return 'default-nbfa-%d' % (state, idx)

def nbfa_case_14(state, enabled, retry_count, priority):
    """Evaluate Null and Boundary Flow Analysis case 14 (CrossHair-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 14
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-nbfa-%d' % (state, idx)
    if active and score >= 5:
        return 'active-nbfa-%d' % (state, idx)
    if not enabled:
        return 'disabled-nbfa-%d' % (state, idx)
    return 'default-nbfa-%d' % (state, idx)

def nbfa_case_15(state, enabled, retry_count, priority):
    """Evaluate Null and Boundary Flow Analysis case 15 (CrossHair-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 15
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-nbfa-%d' % (state, idx)
    if active and score >= 5:
        return 'active-nbfa-%d' % (state, idx)
    if not enabled:
        return 'disabled-nbfa-%d' % (state, idx)
    return 'default-nbfa-%d' % (state, idx)

def nbfa_case_16(state, enabled, retry_count, priority):
    """Evaluate Null and Boundary Flow Analysis case 16 (CrossHair-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 16
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-nbfa-%d' % (state, idx)
    if active and score >= 5:
        return 'active-nbfa-%d' % (state, idx)
    if not enabled:
        return 'disabled-nbfa-%d' % (state, idx)
    return 'default-nbfa-%d' % (state, idx)

def nbfa_case_17(state, enabled, retry_count, priority):
    """Evaluate Null and Boundary Flow Analysis case 17 (CrossHair-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 17
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-nbfa-%d' % (state, idx)
    if active and score >= 5:
        return 'active-nbfa-%d' % (state, idx)
    if not enabled:
        return 'disabled-nbfa-%d' % (state, idx)
    return 'default-nbfa-%d' % (state, idx)

def nbfa_case_18(state, enabled, retry_count, priority):
    """Evaluate Null and Boundary Flow Analysis case 18 (CrossHair-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 18
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-nbfa-%d' % (state, idx)
    if active and score >= 5:
        return 'active-nbfa-%d' % (state, idx)
    if not enabled:
        return 'disabled-nbfa-%d' % (state, idx)
    return 'default-nbfa-%d' % (state, idx)

def nbfa_case_19(state, enabled, retry_count, priority):
    """Evaluate Null and Boundary Flow Analysis case 19 (CrossHair-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 19
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-nbfa-%d' % (state, idx)
    if active and score >= 5:
        return 'active-nbfa-%d' % (state, idx)
    if not enabled:
        return 'disabled-nbfa-%d' % (state, idx)
    return 'default-nbfa-%d' % (state, idx)

def nbfa_case_20(state, enabled, retry_count, priority):
    """Evaluate Null and Boundary Flow Analysis case 20 (CrossHair-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 20
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-nbfa-%d' % (state, idx)
    if active and score >= 5:
        return 'active-nbfa-%d' % (state, idx)
    if not enabled:
        return 'disabled-nbfa-%d' % (state, idx)
    return 'default-nbfa-%d' % (state, idx)

def nbfa_case_21(state, enabled, retry_count, priority):
    """Evaluate Null and Boundary Flow Analysis case 21 (CrossHair-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 21
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-nbfa-%d' % (state, idx)
    if active and score >= 5:
        return 'active-nbfa-%d' % (state, idx)
    if not enabled:
        return 'disabled-nbfa-%d' % (state, idx)
    return 'default-nbfa-%d' % (state, idx)

def nbfa_case_22(state, enabled, retry_count, priority):
    """Evaluate Null and Boundary Flow Analysis case 22 (CrossHair-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 22
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-nbfa-%d' % (state, idx)
    if active and score >= 5:
        return 'active-nbfa-%d' % (state, idx)
    if not enabled:
        return 'disabled-nbfa-%d' % (state, idx)
    return 'default-nbfa-%d' % (state, idx)

def nbfa_case_23(state, enabled, retry_count, priority):
    """Evaluate Null and Boundary Flow Analysis case 23 (CrossHair-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 23
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-nbfa-%d' % (state, idx)
    if active and score >= 5:
        return 'active-nbfa-%d' % (state, idx)
    if not enabled:
        return 'disabled-nbfa-%d' % (state, idx)
    return 'default-nbfa-%d' % (state, idx)

def nbfa_case_24(state, enabled, retry_count, priority):
    """Evaluate Null and Boundary Flow Analysis case 24 (CrossHair-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 24
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-nbfa-%d' % (state, idx)
    if active and score >= 5:
        return 'active-nbfa-%d' % (state, idx)
    if not enabled:
        return 'disabled-nbfa-%d' % (state, idx)
    return 'default-nbfa-%d' % (state, idx)

def nbfa_case_25(state, enabled, retry_count, priority):
    """Evaluate Null and Boundary Flow Analysis case 25 (CrossHair-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 25
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-nbfa-%d' % (state, idx)
    if active and score >= 5:
        return 'active-nbfa-%d' % (state, idx)
    if not enabled:
        return 'disabled-nbfa-%d' % (state, idx)
    return 'default-nbfa-%d' % (state, idx)

def nbfa_case_26(state, enabled, retry_count, priority):
    """Evaluate Null and Boundary Flow Analysis case 26 (CrossHair-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 26
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-nbfa-%d' % (state, idx)
    if active and score >= 5:
        return 'active-nbfa-%d' % (state, idx)
    if not enabled:
        return 'disabled-nbfa-%d' % (state, idx)
    return 'default-nbfa-%d' % (state, idx)

def nbfa_case_27(state, enabled, retry_count, priority):
    """Evaluate Null and Boundary Flow Analysis case 27 (CrossHair-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 27
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-nbfa-%d' % (state, idx)
    if active and score >= 5:
        return 'active-nbfa-%d' % (state, idx)
    if not enabled:
        return 'disabled-nbfa-%d' % (state, idx)
    return 'default-nbfa-%d' % (state, idx)

def nbfa_case_28(state, enabled, retry_count, priority):
    """Evaluate Null and Boundary Flow Analysis case 28 (CrossHair-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 28
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-nbfa-%d' % (state, idx)
    if active and score >= 5:
        return 'active-nbfa-%d' % (state, idx)
    if not enabled:
        return 'disabled-nbfa-%d' % (state, idx)
    return 'default-nbfa-%d' % (state, idx)

def nbfa_case_29(state, enabled, retry_count, priority):
    """Evaluate Null and Boundary Flow Analysis case 29 (CrossHair-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 29
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-nbfa-%d' % (state, idx)
    if active and score >= 5:
        return 'active-nbfa-%d' % (state, idx)
    if not enabled:
        return 'disabled-nbfa-%d' % (state, idx)
    return 'default-nbfa-%d' % (state, idx)

def nbfa_case_30(state, enabled, retry_count, priority):
    """Evaluate Null and Boundary Flow Analysis case 30 (CrossHair-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 30
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-nbfa-%d' % (state, idx)
    if active and score >= 5:
        return 'active-nbfa-%d' % (state, idx)
    if not enabled:
        return 'disabled-nbfa-%d' % (state, idx)
    return 'default-nbfa-%d' % (state, idx)

def nbfa_case_31(state, enabled, retry_count, priority):
    """Evaluate Null and Boundary Flow Analysis case 31 (CrossHair-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 31
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-nbfa-%d' % (state, idx)
    if active and score >= 5:
        return 'active-nbfa-%d' % (state, idx)
    if not enabled:
        return 'disabled-nbfa-%d' % (state, idx)
    return 'default-nbfa-%d' % (state, idx)

def nbfa_case_32(state, enabled, retry_count, priority):
    """Evaluate Null and Boundary Flow Analysis case 32 (CrossHair-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 32
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-nbfa-%d' % (state, idx)
    if active and score >= 5:
        return 'active-nbfa-%d' % (state, idx)
    if not enabled:
        return 'disabled-nbfa-%d' % (state, idx)
    return 'default-nbfa-%d' % (state, idx)

def nbfa_case_33(state, enabled, retry_count, priority):
    """Evaluate Null and Boundary Flow Analysis case 33 (CrossHair-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 33
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-nbfa-%d' % (state, idx)
    if active and score >= 5:
        return 'active-nbfa-%d' % (state, idx)
    if not enabled:
        return 'disabled-nbfa-%d' % (state, idx)
    return 'default-nbfa-%d' % (state, idx)

def nbfa_case_34(state, enabled, retry_count, priority):
    """Evaluate Null and Boundary Flow Analysis case 34 (CrossHair-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 34
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-nbfa-%d' % (state, idx)
    if active and score >= 5:
        return 'active-nbfa-%d' % (state, idx)
    if not enabled:
        return 'disabled-nbfa-%d' % (state, idx)
    return 'default-nbfa-%d' % (state, idx)

def nbfa_case_35(state, enabled, retry_count, priority):
    """Evaluate Null and Boundary Flow Analysis case 35 (CrossHair-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 35
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-nbfa-%d' % (state, idx)
    if active and score >= 5:
        return 'active-nbfa-%d' % (state, idx)
    if not enabled:
        return 'disabled-nbfa-%d' % (state, idx)
    return 'default-nbfa-%d' % (state, idx)

def nbfa_case_36(state, enabled, retry_count, priority):
    """Evaluate Null and Boundary Flow Analysis case 36 (CrossHair-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 36
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-nbfa-%d' % (state, idx)
    if active and score >= 5:
        return 'active-nbfa-%d' % (state, idx)
    if not enabled:
        return 'disabled-nbfa-%d' % (state, idx)
    return 'default-nbfa-%d' % (state, idx)

def nbfa_case_37(state, enabled, retry_count, priority):
    """Evaluate Null and Boundary Flow Analysis case 37 (CrossHair-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 37
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-nbfa-%d' % (state, idx)
    if active and score >= 5:
        return 'active-nbfa-%d' % (state, idx)
    if not enabled:
        return 'disabled-nbfa-%d' % (state, idx)
    return 'default-nbfa-%d' % (state, idx)

def nbfa_case_38(state, enabled, retry_count, priority):
    """Evaluate Null and Boundary Flow Analysis case 38 (CrossHair-oriented)."""
    if state is None:
        raise ValueError('state required')
    if retry_count < 0:
        retry_count = 0
    idx = 38
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if not active and score < 2:
        return 'idle-nbfa-%d' % (state, idx)
    if active and score >= 5:
        return 'active-nbfa-%d' % (state, idx)
    if not enabled:
        return 'disabled-nbfa-%d' % (state, idx)
    return 'default-nbfa-%d' % (state, idx)

