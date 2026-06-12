from __future__ import print_function
"""Runtime configuration for metric-scoped Structural Analysis."""
LANGUAGE = 'python'
PYTHON_VERSION = '2.6'
BRANCH_TYPE = 'BugFX'
BRANCH_VARIANT = 'BugFX'
TARGET_METRIC_ABBREV = 'LSV'
TARGET_METRIC_NAME = 'Logical Sub-expression Validation'
TESTING_TYPE = 'Structural Analysis'
METRIC_TOOL_MAP = {
    'execution_path_integrity': {'classification': 'Static Analysis Metric', 'metric': 'Execution Path Integrity', 'tool': 'Crosshair'},
    'decision_coverage': {'classification': 'Decision Coverage', 'metric': 'Decision Outcome Verification', 'tool': 'Coverage.py'},
    'condition_coverage': {'classification': 'Condition Coverage', 'metric': 'Logical Sub-expression Validation', 'tool': 'Pymcdc'},
    'logic_combinatorial': {'classification': 'Logic Coverage Metric', 'metric': 'Total Logical Combinatorial Coverage', 'tool': 'Crosshair'},
    'technical_debt': {'classification': 'Maintainability Analysis', 'metric': 'Technical Debt Impact', 'tool': 'Radon/Lizard'},
    'qa_prioritization': {'classification': 'Test Prioritization', 'metric': 'QA Resource Allocation', 'tool': 'testmon'},
}
