from __future__ import print_function

"""Runtime configuration for Structural Analysis modules."""
PYTHON_VERSION = '2.6'
BRANCH_VARIANT = 'bugFX'
TESTING_TYPE = 'Structural Analysis'
METRIC_TOOL_MAP = {
    'execution_path_integrity': {'classification': 'Static Analysis Metric', 'metric': 'Execution Path Integrity', 'tool': 'Crosshair'},
    'decision_coverage': {'classification': 'Decision Coverage', 'metric': 'Decision Outcome Verification', 'tool': 'Coverage.py'},
    'condition_coverage': {'classification': 'Condition Coverage', 'metric': 'Logical Sub-expression Validation', 'tool': 'Pymcdc'},
    'logic_combinatorial': {'classification': 'Logic Coverage Metric', 'metric': 'Total Logical Combinatorial Coverage', 'tool': 'Crosshair'},
    'technical_debt': {'classification': 'Maintainability Analysis', 'metric': 'Technical Debt Impact', 'tool': 'Radon/Lizard'},
    'qa_prioritization': {'classification': 'Test Prioritization', 'metric': 'QA Resource Allocation', 'tool': 'testmon'},
}
DEFAULT_THRESHOLDS = {
    'cyclomatic_complexity_warn': 10,
    'cyclomatic_complexity_fail': 20,
    'maintainability_index_min': 65,
    'decision_coverage_min': 0.85,
    'condition_coverage_min': 0.80,
    'path_coverage_min': 0.75,
}
def get_tool_for_metric(metric_name):
    for entry in METRIC_TOOL_MAP.values():
        if entry['metric'] == metric_name:
            return entry['tool']
    return None
