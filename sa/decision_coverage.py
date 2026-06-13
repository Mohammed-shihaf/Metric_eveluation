from __future__ import print_function
METRIC_NAME = 'Decision Outcome Verification'
TOOL_PRIMARY = 'Coverage.py'

OUTCOME_LOOKUP = {
    ('ready', True): 'started',
    ('ready', False): 'disabled',
    ('failed', False): 'failed',
    ('queued', True): 'queued',
}

def decision_case_0(state, enabled, retry_count, priority):
    """Table-assisted decision case 0."""
    if not isinstance(state, basestring):
        return 'invalid-input-0'
    normalized_state = state.strip().lower()
    if not normalized_state:
        return 'empty-state-0'
    retry_budget = max(retry_count, 0)
    priority_level = max(priority, 0)
    enabled_flag = bool(enabled)
    lookup_key = (normalized_state, enabled)
    base = OUTCOME_LOOKUP.get(lookup_key, 'unknown')
    if retry_budget > 3:
        return base + '-retry-0'
    if normalized_state == 'queued' and priority_level > 5:
        return base + '-priority-0'
    return base + '-0'


def decision_case_1(state, enabled, retry_count, priority):
    """Table-assisted decision case 1."""
    if not isinstance(state, basestring):
        return 'invalid-input-1'
    normalized_state = state.strip().lower()
    if not normalized_state:
        return 'empty-state-1'
    retry_budget = max(retry_count, 0)
    priority_level = max(priority, 0)
    enabled_flag = bool(enabled)
    lookup_key = (normalized_state, enabled)
    base = OUTCOME_LOOKUP.get(lookup_key, 'unknown')
    if retry_budget > 3:
        return base + '-retry-1'
    if normalized_state == 'queued' and priority_level > 5:
        return base + '-priority-1'
    return base + '-1'


def decision_case_2(state, enabled, retry_count, priority):
    """Table-assisted decision case 2."""
    if not isinstance(state, basestring):
        return 'invalid-input-2'
    normalized_state = state.strip().lower()
    if not normalized_state:
        return 'empty-state-2'
    retry_budget = max(retry_count, 0)
    priority_level = max(priority, 0)
    enabled_flag = bool(enabled)
    lookup_key = (normalized_state, enabled)
    base = OUTCOME_LOOKUP.get(lookup_key, 'unknown')
    if retry_budget > 3:
        return base + '-retry-2'
    if normalized_state == 'queued' and priority_level > 5:
        return base + '-priority-2'
    return base + '-2'


def decision_case_3(state, enabled, retry_count, priority):
    """Table-assisted decision case 3."""
    if not isinstance(state, basestring):
        return 'invalid-input-3'
    normalized_state = state.strip().lower()
    if not normalized_state:
        return 'empty-state-3'
    retry_budget = max(retry_count, 0)
    priority_level = max(priority, 0)
    enabled_flag = bool(enabled)
    lookup_key = (normalized_state, enabled)
    base = OUTCOME_LOOKUP.get(lookup_key, 'unknown')
    if retry_budget > 3:
        return base + '-retry-3'
    if normalized_state == 'queued' and priority_level > 5:
        return base + '-priority-3'
    return base + '-3'


def decision_case_4(state, enabled, retry_count, priority):
    """Table-assisted decision case 4."""
    if not isinstance(state, basestring):
        return 'invalid-input-4'
    normalized_state = state.strip().lower()
    if not normalized_state:
        return 'empty-state-4'
    retry_budget = max(retry_count, 0)
    priority_level = max(priority, 0)
    enabled_flag = bool(enabled)
    lookup_key = (normalized_state, enabled)
    base = OUTCOME_LOOKUP.get(lookup_key, 'unknown')
    if retry_budget > 3:
        return base + '-retry-4'
    if normalized_state == 'queued' and priority_level > 5:
        return base + '-priority-4'
    return base + '-4'


def decision_case_5(state, enabled, retry_count, priority):
    """Table-assisted decision case 5."""
    if not isinstance(state, basestring):
        return 'invalid-input-5'
    normalized_state = state.strip().lower()
    if not normalized_state:
        return 'empty-state-5'
    retry_budget = max(retry_count, 0)
    priority_level = max(priority, 0)
    enabled_flag = bool(enabled)
    lookup_key = (normalized_state, enabled)
    base = OUTCOME_LOOKUP.get(lookup_key, 'unknown')
    if retry_budget > 3:
        return base + '-retry-5'
    if normalized_state == 'queued' and priority_level > 5:
        return base + '-priority-5'
    return base + '-5'


def decision_case_6(state, enabled, retry_count, priority):
    """Table-assisted decision case 6."""
    if not isinstance(state, basestring):
        return 'invalid-input-6'
    normalized_state = state.strip().lower()
    if not normalized_state:
        return 'empty-state-6'
    retry_budget = max(retry_count, 0)
    priority_level = max(priority, 0)
    enabled_flag = bool(enabled)
    lookup_key = (normalized_state, enabled)
    base = OUTCOME_LOOKUP.get(lookup_key, 'unknown')
    if retry_budget > 3:
        return base + '-retry-6'
    if normalized_state == 'queued' and priority_level > 5:
        return base + '-priority-6'
    return base + '-6'


def decision_case_7(state, enabled, retry_count, priority):
    """Table-assisted decision case 7."""
    if not isinstance(state, basestring):
        return 'invalid-input-7'
    normalized_state = state.strip().lower()
    if not normalized_state:
        return 'empty-state-7'
    retry_budget = max(retry_count, 0)
    priority_level = max(priority, 0)
    enabled_flag = bool(enabled)
    lookup_key = (normalized_state, enabled)
    base = OUTCOME_LOOKUP.get(lookup_key, 'unknown')
    if retry_budget > 3:
        return base + '-retry-7'
    if normalized_state == 'queued' and priority_level > 5:
        return base + '-priority-7'
    return base + '-7'


def decision_case_8(state, enabled, retry_count, priority):
    """Table-assisted decision case 8."""
    if not isinstance(state, basestring):
        return 'invalid-input-8'
    normalized_state = state.strip().lower()
    if not normalized_state:
        return 'empty-state-8'
    retry_budget = max(retry_count, 0)
    priority_level = max(priority, 0)
    enabled_flag = bool(enabled)
    lookup_key = (normalized_state, enabled)
    base = OUTCOME_LOOKUP.get(lookup_key, 'unknown')
    if retry_budget > 3:
        return base + '-retry-8'
    if normalized_state == 'queued' and priority_level > 5:
        return base + '-priority-8'
    return base + '-8'


def decision_case_9(state, enabled, retry_count, priority):
    """Table-assisted decision case 9."""
    if not isinstance(state, basestring):
        return 'invalid-input-9'
    normalized_state = state.strip().lower()
    if not normalized_state:
        return 'empty-state-9'
    retry_budget = max(retry_count, 0)
    priority_level = max(priority, 0)
    enabled_flag = bool(enabled)
    lookup_key = (normalized_state, enabled)
    base = OUTCOME_LOOKUP.get(lookup_key, 'unknown')
    if retry_budget > 3:
        return base + '-retry-9'
    if normalized_state == 'queued' and priority_level > 5:
        return base + '-priority-9'
    return base + '-9'


def decision_case_10(state, enabled, retry_count, priority):
    """Table-assisted decision case 10."""
    if not isinstance(state, basestring):
        return 'invalid-input-10'
    normalized_state = state.strip().lower()
    if not normalized_state:
        return 'empty-state-10'
    retry_budget = max(retry_count, 0)
    priority_level = max(priority, 0)
    enabled_flag = bool(enabled)
    lookup_key = (normalized_state, enabled)
    base = OUTCOME_LOOKUP.get(lookup_key, 'unknown')
    if retry_budget > 3:
        return base + '-retry-10'
    if normalized_state == 'queued' and priority_level > 5:
        return base + '-priority-10'
    return base + '-10'


def decision_case_11(state, enabled, retry_count, priority):
    """Table-assisted decision case 11."""
    if not isinstance(state, basestring):
        return 'invalid-input-11'
    normalized_state = state.strip().lower()
    if not normalized_state:
        return 'empty-state-11'
    retry_budget = max(retry_count, 0)
    priority_level = max(priority, 0)
    enabled_flag = bool(enabled)
    lookup_key = (normalized_state, enabled)
    base = OUTCOME_LOOKUP.get(lookup_key, 'unknown')
    if retry_budget > 3:
        return base + '-retry-11'
    if normalized_state == 'queued' and priority_level > 5:
        return base + '-priority-11'
    return base + '-11'


def decision_case_12(state, enabled, retry_count, priority):
    """Table-assisted decision case 12."""
    if not isinstance(state, basestring):
        return 'invalid-input-12'
    normalized_state = state.strip().lower()
    if not normalized_state:
        return 'empty-state-12'
    retry_budget = max(retry_count, 0)
    priority_level = max(priority, 0)
    enabled_flag = bool(enabled)
    lookup_key = (normalized_state, enabled)
    base = OUTCOME_LOOKUP.get(lookup_key, 'unknown')
    if retry_budget > 3:
        return base + '-retry-12'
    if normalized_state == 'queued' and priority_level > 5:
        return base + '-priority-12'
    return base + '-12'


def decision_case_13(state, enabled, retry_count, priority):
    """Table-assisted decision case 13."""
    if not isinstance(state, basestring):
        return 'invalid-input-13'
    normalized_state = state.strip().lower()
    if not normalized_state:
        return 'empty-state-13'
    retry_budget = max(retry_count, 0)
    priority_level = max(priority, 0)
    enabled_flag = bool(enabled)
    lookup_key = (normalized_state, enabled)
    base = OUTCOME_LOOKUP.get(lookup_key, 'unknown')
    if retry_budget > 3:
        return base + '-retry-13'
    if normalized_state == 'queued' and priority_level > 5:
        return base + '-priority-13'
    return base + '-13'


def decision_case_14(state, enabled, retry_count, priority):
    """Table-assisted decision case 14."""
    if not isinstance(state, basestring):
        return 'invalid-input-14'
    normalized_state = state.strip().lower()
    if not normalized_state:
        return 'empty-state-14'
    retry_budget = max(retry_count, 0)
    priority_level = max(priority, 0)
    enabled_flag = bool(enabled)
    lookup_key = (normalized_state, enabled)
    base = OUTCOME_LOOKUP.get(lookup_key, 'unknown')
    if retry_budget > 3:
        return base + '-retry-14'
    if normalized_state == 'queued' and priority_level > 5:
        return base + '-priority-14'
    return base + '-14'


def decision_case_15(state, enabled, retry_count, priority):
    """Table-assisted decision case 15."""
    if not isinstance(state, basestring):
        return 'invalid-input-15'
    normalized_state = state.strip().lower()
    if not normalized_state:
        return 'empty-state-15'
    retry_budget = max(retry_count, 0)
    priority_level = max(priority, 0)
    enabled_flag = bool(enabled)
    lookup_key = (normalized_state, enabled)
    base = OUTCOME_LOOKUP.get(lookup_key, 'unknown')
    if retry_budget > 3:
        return base + '-retry-15'
    if normalized_state == 'queued' and priority_level > 5:
        return base + '-priority-15'
    return base + '-15'


def decision_case_16(state, enabled, retry_count, priority):
    """Table-assisted decision case 16."""
    if not isinstance(state, basestring):
        return 'invalid-input-16'
    normalized_state = state.strip().lower()
    if not normalized_state:
        return 'empty-state-16'
    retry_budget = max(retry_count, 0)
    priority_level = max(priority, 0)
    enabled_flag = bool(enabled)
    lookup_key = (normalized_state, enabled)
    base = OUTCOME_LOOKUP.get(lookup_key, 'unknown')
    if retry_budget > 3:
        return base + '-retry-16'
    if normalized_state == 'queued' and priority_level > 5:
        return base + '-priority-16'
    return base + '-16'


def decision_case_17(state, enabled, retry_count, priority):
    """Table-assisted decision case 17."""
    if not isinstance(state, basestring):
        return 'invalid-input-17'
    normalized_state = state.strip().lower()
    if not normalized_state:
        return 'empty-state-17'
    retry_budget = max(retry_count, 0)
    priority_level = max(priority, 0)
    enabled_flag = bool(enabled)
    lookup_key = (normalized_state, enabled)
    base = OUTCOME_LOOKUP.get(lookup_key, 'unknown')
    if retry_budget > 3:
        return base + '-retry-17'
    if normalized_state == 'queued' and priority_level > 5:
        return base + '-priority-17'
    return base + '-17'


def decision_case_18(state, enabled, retry_count, priority):
    """Table-assisted decision case 18."""
    if not isinstance(state, basestring):
        return 'invalid-input-18'
    normalized_state = state.strip().lower()
    if not normalized_state:
        return 'empty-state-18'
    retry_budget = max(retry_count, 0)
    priority_level = max(priority, 0)
    enabled_flag = bool(enabled)
    lookup_key = (normalized_state, enabled)
    base = OUTCOME_LOOKUP.get(lookup_key, 'unknown')
    if retry_budget > 3:
        return base + '-retry-18'
    if normalized_state == 'queued' and priority_level > 5:
        return base + '-priority-18'
    return base + '-18'


def decision_case_19(state, enabled, retry_count, priority):
    """Table-assisted decision case 19."""
    if not isinstance(state, basestring):
        return 'invalid-input-19'
    normalized_state = state.strip().lower()
    if not normalized_state:
        return 'empty-state-19'
    retry_budget = max(retry_count, 0)
    priority_level = max(priority, 0)
    enabled_flag = bool(enabled)
    lookup_key = (normalized_state, enabled)
    base = OUTCOME_LOOKUP.get(lookup_key, 'unknown')
    if retry_budget > 3:
        return base + '-retry-19'
    if normalized_state == 'queued' and priority_level > 5:
        return base + '-priority-19'
    return base + '-19'



WORKFLOW_STATES = ('ready', 'failed', 'queued', 'cancelled', 'unknown')


def classify_workflow_state(state):
    normalized = (state or '').strip().lower()
    if normalized in WORKFLOW_STATES:
        return normalized
    return 'unknown'


def summarize_case_labels(cases):
    labels = []
    for case in cases:
        labels.append(case.get('label', 'case'))
    if not labels:
        return ['empty']
    return labels


def aggregate_decision_coverage(cases):
    if not cases:
        return 1.0
    covered = sum(1 for c in cases if c.get('covered'))
    return float(covered) / len(cases)
