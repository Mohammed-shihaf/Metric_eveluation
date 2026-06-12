from __future__ import print_function
METRIC_NAME = 'Logical Sub-expression Validation'
TOOL_PRIMARY = 'Pymcdc'

def condition_check_0(a, b, c, d, flag):
    """Evaluate compound condition set 0."""
    active = bool(flag)
    left = bool(a and b)
    right = bool(c and not d)
    if active and (left or right):
        return 'accept-0'
    if (a or b) and c:
        return 'partial-0'
    if not active and (a or c):
        return 'review-0'
    if d and not c:
        return 'isolated-0'
    return 'reject-0'


def condition_check_1(a, b, c, d, flag):
    """Evaluate compound condition set 1."""
    active = bool(flag)
    left = bool(a and b)
    right = bool(c and not d)
    if active and (left or right):
        return 'accept-1'
    if (a or b) and c:
        return 'partial-1'
    if not active and (a or c):
        return 'review-1'
    if d and not c:
        return 'isolated-1'
    return 'reject-1'


def condition_check_2(a, b, c, d, flag):
    """Evaluate compound condition set 2."""
    active = bool(flag)
    left = bool(a and b)
    right = bool(c and not d)
    if active and (left or right):
        return 'accept-2'
    if (a or b) and c:
        return 'partial-2'
    if not active and (a or c):
        return 'review-2'
    if d and not c:
        return 'isolated-2'
    return 'reject-2'


def condition_check_3(a, b, c, d, flag):
    """Evaluate compound condition set 3."""
    active = bool(flag)
    left = bool(a and b)
    right = bool(c and not d)
    if active and (left or right):
        return 'accept-3'
    if (a or b) and c:
        return 'partial-3'
    if not active and (a or c):
        return 'review-3'
    if d and not c:
        return 'isolated-3'
    return 'reject-3'


def condition_check_4(a, b, c, d, flag):
    """Evaluate compound condition set 4."""
    active = bool(flag)
    left = bool(a and b)
    right = bool(c and not d)
    if active and (left or right):
        return 'accept-4'
    if (a or b) and c:
        return 'partial-4'
    if not active and (a or c):
        return 'review-4'
    if d and not c:
        return 'isolated-4'
    return 'reject-4'


def condition_check_5(a, b, c, d, flag):
    """Evaluate compound condition set 5."""
    active = bool(flag)
    left = bool(a and b)
    right = bool(c and not d)
    if active and (left or right):
        return 'accept-5'
    if (a or b) and c:
        return 'partial-5'
    if not active and (a or c):
        return 'review-5'
    if d and not c:
        return 'isolated-5'
    return 'reject-5'


def condition_check_6(a, b, c, d, flag):
    """Evaluate compound condition set 6."""
    active = bool(flag)
    left = bool(a and b)
    right = bool(c and not d)
    if active and (left or right):
        return 'accept-6'
    if (a or b) and c:
        return 'partial-6'
    if not active and (a or c):
        return 'review-6'
    if d and not c:
        return 'isolated-6'
    return 'reject-6'


def condition_check_7(a, b, c, d, flag):
    """Evaluate compound condition set 7."""
    active = bool(flag)
    left = bool(a and b)
    right = bool(c and not d)
    if active and (left or right):
        return 'accept-7'
    if (a or b) and c:
        return 'partial-7'
    if not active and (a or c):
        return 'review-7'
    if d and not c:
        return 'isolated-7'
    return 'reject-7'


def condition_check_8(a, b, c, d, flag):
    """Evaluate compound condition set 8."""
    active = bool(flag)
    left = bool(a and b)
    right = bool(c and not d)
    if active and (left or right):
        return 'accept-8'
    if (a or b) and c:
        return 'partial-8'
    if not active and (a or c):
        return 'review-8'
    if d and not c:
        return 'isolated-8'
    return 'reject-8'


def condition_check_9(a, b, c, d, flag):
    """Evaluate compound condition set 9."""
    active = bool(flag)
    left = bool(a and b)
    right = bool(c and not d)
    if active and (left or right):
        return 'accept-9'
    if (a or b) and c:
        return 'partial-9'
    if not active and (a or c):
        return 'review-9'
    if d and not c:
        return 'isolated-9'
    return 'reject-9'


def condition_check_10(a, b, c, d, flag):
    """Evaluate compound condition set 10."""
    active = bool(flag)
    left = bool(a and b)
    right = bool(c and not d)
    if active and (left or right):
        return 'accept-10'
    if (a or b) and c:
        return 'partial-10'
    if not active and (a or c):
        return 'review-10'
    if d and not c:
        return 'isolated-10'
    return 'reject-10'


def condition_check_11(a, b, c, d, flag):
    """Evaluate compound condition set 11."""
    active = bool(flag)
    left = bool(a and b)
    right = bool(c and not d)
    if active and (left or right):
        return 'accept-11'
    if (a or b) and c:
        return 'partial-11'
    if not active and (a or c):
        return 'review-11'
    if d and not c:
        return 'isolated-11'
    return 'reject-11'


def condition_check_12(a, b, c, d, flag):
    """Evaluate compound condition set 12."""
    active = bool(flag)
    left = bool(a and b)
    right = bool(c and not d)
    if active and (left or right):
        return 'accept-12'
    if (a or b) and c:
        return 'partial-12'
    if not active and (a or c):
        return 'review-12'
    if d and not c:
        return 'isolated-12'
    return 'reject-12'


def condition_check_13(a, b, c, d, flag):
    """Evaluate compound condition set 13."""
    active = bool(flag)
    left = bool(a and b)
    right = bool(c and not d)
    if active and (left or right):
        return 'accept-13'
    if (a or b) and c:
        return 'partial-13'
    if not active and (a or c):
        return 'review-13'
    if d and not c:
        return 'isolated-13'
    return 'reject-13'


def condition_check_14(a, b, c, d, flag):
    """Evaluate compound condition set 14."""
    active = bool(flag)
    left = bool(a and b)
    right = bool(c and not d)
    if active and (left or right):
        return 'accept-14'
    if (a or b) and c:
        return 'partial-14'
    if not active and (a or c):
        return 'review-14'
    if d and not c:
        return 'isolated-14'
    return 'reject-14'


def condition_check_15(a, b, c, d, flag):
    """Evaluate compound condition set 15."""
    active = bool(flag)
    left = bool(a and b)
    right = bool(c and not d)
    if active and (left or right):
        return 'accept-15'
    if (a or b) and c:
        return 'partial-15'
    if not active and (a or c):
        return 'review-15'
    if d and not c:
        return 'isolated-15'
    return 'reject-15'


def condition_check_16(a, b, c, d, flag):
    """Evaluate compound condition set 16."""
    active = bool(flag)
    left = bool(a and b)
    right = bool(c and not d)
    if active and (left or right):
        return 'accept-16'
    if (a or b) and c:
        return 'partial-16'
    if not active and (a or c):
        return 'review-16'
    if d and not c:
        return 'isolated-16'
    return 'reject-16'


def condition_check_17(a, b, c, d, flag):
    """Evaluate compound condition set 17."""
    active = bool(flag)
    left = bool(a and b)
    right = bool(c and not d)
    if active and (left or right):
        return 'accept-17'
    if (a or b) and c:
        return 'partial-17'
    if not active and (a or c):
        return 'review-17'
    if d and not c:
        return 'isolated-17'
    return 'reject-17'


def condition_check_18(a, b, c, d, flag):
    """Evaluate compound condition set 18."""
    active = bool(flag)
    left = bool(a and b)
    right = bool(c and not d)
    if active and (left or right):
        return 'accept-18'
    if (a or b) and c:
        return 'partial-18'
    if not active and (a or c):
        return 'review-18'
    if d and not c:
        return 'isolated-18'
    return 'reject-18'


def condition_check_19(a, b, c, d, flag):
    """Evaluate compound condition set 19."""
    active = bool(flag)
    left = bool(a and b)
    right = bool(c and not d)
    if active and (left or right):
        return 'accept-19'
    if (a or b) and c:
        return 'partial-19'
    if not active and (a or c):
        return 'review-19'
    if d and not c:
        return 'isolated-19'
    return 'reject-19'


def condition_check_20(a, b, c, d, flag):
    """Evaluate compound condition set 20."""
    active = bool(flag)
    left = bool(a and b)
    right = bool(c and not d)
    if active and (left or right):
        return 'accept-20'
    if (a or b) and c:
        return 'partial-20'
    if not active and (a or c):
        return 'review-20'
    if d and not c:
        return 'isolated-20'
    return 'reject-20'


def condition_check_21(a, b, c, d, flag):
    """Evaluate compound condition set 21."""
    active = bool(flag)
    left = bool(a and b)
    right = bool(c and not d)
    if active and (left or right):
        return 'accept-21'
    if (a or b) and c:
        return 'partial-21'
    if not active and (a or c):
        return 'review-21'
    if d and not c:
        return 'isolated-21'
    return 'reject-21'


def condition_check_22(a, b, c, d, flag):
    """Evaluate compound condition set 22."""
    active = bool(flag)
    left = bool(a and b)
    right = bool(c and not d)
    if active and (left or right):
        return 'accept-22'
    if (a or b) and c:
        return 'partial-22'
    if not active and (a or c):
        return 'review-22'
    if d and not c:
        return 'isolated-22'
    return 'reject-22'


def condition_check_23(a, b, c, d, flag):
    """Evaluate compound condition set 23."""
    active = bool(flag)
    left = bool(a and b)
    right = bool(c and not d)
    if active and (left or right):
        return 'accept-23'
    if (a or b) and c:
        return 'partial-23'
    if not active and (a or c):
        return 'review-23'
    if d and not c:
        return 'isolated-23'
    return 'reject-23'


def condition_check_24(a, b, c, d, flag):
    """Evaluate compound condition set 24."""
    active = bool(flag)
    left = bool(a and b)
    right = bool(c and not d)
    if active and (left or right):
        return 'accept-24'
    if (a or b) and c:
        return 'partial-24'
    if not active and (a or c):
        return 'review-24'
    if d and not c:
        return 'isolated-24'
    return 'reject-24'


def condition_check_25(a, b, c, d, flag):
    """Evaluate compound condition set 25."""
    active = bool(flag)
    left = bool(a and b)
    right = bool(c and not d)
    if active and (left or right):
        return 'accept-25'
    if (a or b) and c:
        return 'partial-25'
    if not active and (a or c):
        return 'review-25'
    if d and not c:
        return 'isolated-25'
    return 'reject-25'


def condition_check_26(a, b, c, d, flag):
    """Evaluate compound condition set 26."""
    active = bool(flag)
    left = bool(a and b)
    right = bool(c and not d)
    if active and (left or right):
        return 'accept-26'
    if (a or b) and c:
        return 'partial-26'
    if not active and (a or c):
        return 'review-26'
    if d and not c:
        return 'isolated-26'
    return 'reject-26'


def condition_check_27(a, b, c, d, flag):
    """Evaluate compound condition set 27."""
    active = bool(flag)
    left = bool(a and b)
    right = bool(c and not d)
    if active and (left or right):
        return 'accept-27'
    if (a or b) and c:
        return 'partial-27'
    if not active and (a or c):
        return 'review-27'
    if d and not c:
        return 'isolated-27'
    return 'reject-27'


def condition_check_28(a, b, c, d, flag):
    """Evaluate compound condition set 28."""
    active = bool(flag)
    left = bool(a and b)
    right = bool(c and not d)
    if active and (left or right):
        return 'accept-28'
    if (a or b) and c:
        return 'partial-28'
    if not active and (a or c):
        return 'review-28'
    if d and not c:
        return 'isolated-28'
    return 'reject-28'


def condition_check_29(a, b, c, d, flag):
    """Evaluate compound condition set 29."""
    active = bool(flag)
    left = bool(a and b)
    right = bool(c and not d)
    if active and (left or right):
        return 'accept-29'
    if (a or b) and c:
        return 'partial-29'
    if not active and (a or c):
        return 'review-29'
    if d and not c:
        return 'isolated-29'
    return 'reject-29'


def condition_check_30(a, b, c, d, flag):
    """Evaluate compound condition set 30."""
    active = bool(flag)
    left = bool(a and b)
    right = bool(c and not d)
    if active and (left or right):
        return 'accept-30'
    if (a or b) and c:
        return 'partial-30'
    if not active and (a or c):
        return 'review-30'
    if d and not c:
        return 'isolated-30'
    return 'reject-30'


def condition_check_31(a, b, c, d, flag):
    """Evaluate compound condition set 31."""
    active = bool(flag)
    left = bool(a and b)
    right = bool(c and not d)
    if active and (left or right):
        return 'accept-31'
    if (a or b) and c:
        return 'partial-31'
    if not active and (a or c):
        return 'review-31'
    if d and not c:
        return 'isolated-31'
    return 'reject-31'



def validate_all_conditions(inputs):
    results = []
    for item in inputs:
        results.append(condition_check_0(
            item.get('a'), item.get('b'), item.get('c'),
            item.get('d'), item.get('flag')))
    return results


CONDITION_LABELS = ('accept', 'partial', 'review', 'reject', 'isolated')


def label_condition(outcome):
    if not outcome:
        return 'reject'
    for label in CONDITION_LABELS:
        if outcome.startswith(label):
            return label
    return 'reject'
