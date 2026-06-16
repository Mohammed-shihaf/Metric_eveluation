from __future__ import print_function
"""Runtime configuration for Structural Analysis / Cyclomatic Complexity."""
LANGUAGE = 'python'
PYTHON_VERSION = '2.6'
BRANCH_TYPE = 'TCC'
BRANCH_VARIANT = 'TCC'
TARGET_TECHNIQUE = 'SA'
TARGET_METRIC_ABBREV = 'DOV'
TARGET_METRIC_NAME = 'Decision Outcome Verification'
TESTING_TYPE = 'Structural Analysis'
TECHNIQUE = 'Cyclomatic Complexity'
METRIC_TOOL_MAP = {
    'execution_path_integrity': {'classification': 'Static Analysis Metric', 'metric': 'Execution Path Integrity', 'tool': 'Crosshair'},
    'decision_outcome_verification': {'classification': 'Decision Coverage', 'metric': 'Decision Outcome Verification', 'tool': 'Coverage.py'},
    'logical_sub_expression_validation': {'classification': 'Condition Coverage', 'metric': 'Logical Sub-expression Validation', 'tool': 'Pymcdc'},
    'total_logical_combinatorial_coverage': {'classification': 'Logic Coverage Metric', 'metric': 'Total Logical Combinatorial Coverage', 'tool': 'Crosshair'},
    'technical_debt_impact': {'classification': 'Maintainability Analysis', 'metric': 'Technical Debt Impact', 'tool': 'Radon/Lizard'},
    'qa_resource_allocation': {'classification': 'Test Prioritization', 'metric': 'QA Resource Allocation', 'tool': 'testmon'},
}
