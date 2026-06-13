from __future__ import print_function
"""Runtime configuration for Data Flow Testing / All Definition Coverage."""
LANGUAGE = 'python'
PYTHON_VERSION = '2.6'
BRANCH_TYPE = 'BugFX'
BRANCH_VARIANT = 'BugFX'
TARGET_TECHNIQUE = 'DF'
TARGET_METRIC_ABBREV = 'DPV'
TARGET_METRIC_NAME = 'DU-Path Validation'
TESTING_TYPE = 'Data Flow Testing'
TECHNIQUE = 'All Definition Coverage'
METRIC_TOOL_MAP = {
    'all_defs_coverage': {'classification': 'Variable Definition Detection', 'metric': 'All-Defs Coverage %', 'tool': 'Beniget'},
    'data_path_correlation': {'classification': 'Definition-Use Mapping', 'metric': 'Data Path Correlation', 'tool': 'coverage.py'},
    'du_path_validation': {'classification': 'Coverage Measurement', 'metric': 'DU-Path Validation', 'tool': 'Beniget'},
    'dead_data_identification': {'classification': 'Uncovered Definition Detection', 'metric': 'Dead Data Identification', 'tool': 'pylint'},
    'null_and_boundary_flow_analysis': {'classification': 'Edge Case Handling', 'metric': 'Null and Boundary Flow Analysis', 'tool': 'CrossHair'},
    'audit_trail_verification': {'classification': 'Reporting Validation', 'metric': 'Audit Trail Verification', 'tool': 'pydriller'},
}
