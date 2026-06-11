"""Structural Analysis metric registry and branch naming."""

from __future__ import print_function

# module_key, abbrev, classification (taxonomy leaf), metric name, tool
SA_METRICS = [
    ("execution_path_integrity", "EPI", "Static Analysis Metric", "Execution Path Integrity", "Crosshair"),
    ("decision_coverage", "DOV", "Decision Coverage", "Decision Outcome Verification", "Coverage.py"),
    ("condition_coverage", "LSV", "Condition Coverage", "Logical Sub-expression Validation", "Pymcdc"),
    ("logic_combinatorial", "TLCC", "Logic Coverage Metric", "Total Logical Combinatorial Coverage", "Crosshair"),
    ("technical_debt", "TDI", "Maintainability Analysis", "Technical Debt Impact", "Radon/Lizard"),
    ("qa_prioritization", "QRA", "Test Prioritization", "QA Resource Allocation", "testmon"),
]

BRANCH_TYPES = ("Bug", "BugFX", "TCC", "CC")

ABBREV_TO_MODULE = {abbrev: module for module, abbrev, _, _, _ in SA_METRICS}
ABBREV_TO_CLASSIFICATION = {abbrev: cls for _, abbrev, cls, _, _ in SA_METRICS}
MODULE_TO_ABBREV = {module: abbrev for module, abbrev, _, _, _ in SA_METRICS}


def branch_name(abbrev, branch_type="Bug", version="2.6"):
    return "SA_%s_%s_%s" % (abbrev, branch_type, version)


def all_metric_branches(version="2.6", branch_types=None):
    types = branch_types or BRANCH_TYPES
    out = []
    for _, abbrev, _, _, _ in SA_METRICS:
        for bt in types:
            out.append(branch_name(abbrev, bt, version))
    return out


def all_bug_branches(version="2.6"):
    return all_metric_branches(version, ("Bug",))


def all_metric_branches_csv(version="2.6", branch_types=None):
    return ",".join(all_metric_branches(version, branch_types))


def module_variant(module_key, target_module_key, branch_type):
    """Map branch type to target-module code variant (non-target modules use stubs)."""
    if module_key != target_module_key:
        return "stub"
    return {
        "Bug": "bug",
        "BugFX": "bugfx",
        "TCC": "tcc",
        "CC": "cc",
    }[branch_type]
