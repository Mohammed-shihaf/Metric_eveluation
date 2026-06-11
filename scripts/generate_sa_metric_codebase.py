#!/usr/bin/env python3
"""Generate metric-scoped SA branches (e.g. SA_EPI_Bug_2.6, SA_EPI_BugFX_2.6, ...).

Bug: defects only in the target metric module.
BugFX / TCC / CC: target module fixed/clean; TCC adds tool configs + full tests.
"""

from __future__ import print_function

import argparse
import os
import shutil
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

import generate_sa_codebase as gen  # noqa: E402
from sa_metric_modules import (  # noqa: E402
    gen_bulk_empty,
    gen_metric_stub,
    generate_module_content,
)
from sa_metrics import (  # noqa: E402
    ABBREV_TO_MODULE,
    BRANCH_TYPES,
    SA_METRICS,
    branch_name,
    module_variant,
)

BRANCH_TYPE_DESC = {
    "Bug": "intentional defects in the target metric module only",
    "BugFX": "same layout with target-metric defects fixed",
    "TCC": "tool-based clean code (Crosshair, Coverage.py, Pymcdc, Radon, testmon)",
    "CC": "general clean code without tool-optimized configs",
}


def gen_config_metric(abbrev, branch_type, target_metric_name):
    tools = "\n".join(
        "    '%s': {'classification': '%s', 'metric': '%s', 'tool': '%s'}," % (m, c, met, t)
        for m, _, c, met, t in SA_METRICS
    )
    return gen.FUTURE + (
        '"""Runtime configuration for metric-scoped Structural Analysis."""\n'
        "PYTHON_VERSION = '2.6'\n"
        "BRANCH_TYPE = '%(branch_type)s'\n"
        "BRANCH_VARIANT = '%(branch_type)s'\n"
        "TARGET_METRIC_ABBREV = '%(abbrev)s'\n"
        "TARGET_METRIC_NAME = '%(metric)s'\n"
        "TESTING_TYPE = 'Structural Analysis'\n"
        "METRIC_TOOL_MAP = {\n%(tools)s\n}\n"
    ) % {
        "branch_type": branch_type,
        "abbrev": abbrev,
        "metric": target_metric_name,
        "tools": tools,
    }


def gen_readme_metric(branch_name, abbrev, metric_name, classification, branch_type):
    table = "\n".join(
        "| %s | %s | %s | %s |" % (abbr, cls, met, tool)
        for _, abbr, cls, met, tool in SA_METRICS
    )
    note = BRANCH_TYPE_DESC.get(branch_type, branch_type)
    target_file = ABBREV_TO_MODULE[abbrev]
    if branch_type == "Bug":
        defect_line = "- Only `%s.py` contains intentional defects; all other SA modules are stubs.\n" % target_file
    elif branch_type == "BugFX":
        defect_line = "- `%s.py` has bugs fixed; other SA modules remain minimal stubs.\n" % target_file
    elif branch_type == "TCC":
        defect_line = "- `%s.py` uses tool-optimized clean code (distinct from BugFX/CC).\n" % target_file
    else:
        defect_line = "- `%s.py` uses general clean code (distinct structure from TCC/BugFX).\n" % target_file
    return (
        "# %s\n\n"
        "Python 2.6 Structural Analysis — **metric-scoped %s branch**.\n\n"
        "- **Target metric:** %s (`%s`)\n"
        "- **Classification:** %s\n"
        "- **Branch role:** %s\n"
        "%s\n"
        "| Abbrev | Classification | Metric | Tool |\n"
        "|---|---|---|---|\n"
        "%s\n"
    ) % (
        branch_name,
        branch_type,
        metric_name,
        abbrev,
        classification,
        note,
        defect_line,
        table,
    )


def gen_requirements_metric(branch_type):
    if branch_type == "TCC":
        return "# TCC tooling\n coverage==3.7.1\nradon==1.4.2\npytest==2.6.4\ntestmon==0.4.5\n"
    if branch_type in ("BugFX", "Bug") and True:
        return "# Tests optional; platform tools run on source\npytest==2.6.4\n"
    return "# Tooling installed by Testable platform\n"


def gen_tool_configs_metric(branch_type):
    if branch_type != "TCC":
        return {}
    return {
        ".coveragerc": "[run]\nbranch = True\nsource = sa\nomit = tests/*\n",
        "setup.cfg": "[radon]\ncc_min = A\n",
        "pytest.ini": "[pytest]\ntestpaths = tests\n",
        ".testmondata.ini": "[testmon]\ndepth = module\n",
    }


def _test_body(t, imports, cases):
    return t + imports + "\nclass T(unittest.TestCase):\n" + cases


def gen_tests_full(abbrev):
    """Full tests on the target metric module only (non-target modules are stubs)."""
    t = gen.FUTURE
    files = {"tests/__init__.py": t}
    if abbrev == "EPI":
        files["tests/test_execution_path_integrity.py"] = _test_body(
            t,
            "import unittest\nfrom sa.execution_path_integrity import evaluate_path_integrity, route_handler_1\n",
            " def test_default(self):\n  self.assertEqual(evaluate_path_integrity(5, 'fast', {}), 'ok-5')\n"
            " def test_audit(self):\n  self.assertEqual(evaluate_path_integrity(3, 'audit', {}), 'audit-3')\n"
            " def test_route(self):\n  self.assertEqual(route_handler_1({'value': 1}), 'ok-1')\n",
        )
    elif abbrev == "DOV":
        files["tests/test_decision_coverage.py"] = _test_body(
            t,
            "import unittest\nfrom sa.decision_coverage import decision_case_0, aggregate_decision_coverage\n",
            " def test_started(self):\n  self.assertTrue(decision_case_0('ready', True, 0).startswith('started'))\n"
            " def test_failed(self):\n  self.assertTrue(decision_case_0('failed', False, 0).startswith('failed'))\n"
            " def test_retry(self):\n  self.assertTrue(decision_case_0('ready', False, 5).startswith('retry'))\n"
            " def test_aggregate_empty(self):\n  self.assertEqual(aggregate_decision_coverage([]), 1.0)\n",
        )
    elif abbrev == "LSV":
        files["tests/test_condition_coverage.py"] = _test_body(
            t,
            "import unittest\nfrom sa.condition_coverage import condition_check_0, validate_all_conditions\n",
            " def test_accept(self):\n  self.assertEqual(condition_check_0(True,True,False,True,True), 'accept-0')\n"
            " def test_partial(self):\n  self.assertEqual(condition_check_0(False,True,True,False,False), 'partial-0')\n"
            " def test_validate(self):\n  self.assertEqual(len(validate_all_conditions([{'a':True,'b':True,'c':False,'d':True,'flag':True}])), 1)\n",
        )
    elif abbrev == "TLCC":
        files["tests/test_logic_combinatorial.py"] = _test_body(
            t,
            "import unittest\nfrom sa.logic_combinatorial import count_unique_paths, combinatorial_state_machine_0\n",
            " def test_paths(self):\n  self.assertEqual(count_unique_paths('x', 3), 8)\n"
            " def test_machine(self):\n  self.assertTrue(combinatorial_state_machine_0([True, False]))\n",
        )
    elif abbrev == "TDI":
        files["tests/test_technical_debt.py"] = _test_body(
            t,
            "import unittest\nfrom sa.technical_debt import debt_calculator_b0_v0\n",
            " def test_ok(self):\n  self.assertTrue(debt_calculator_b0_v0(100, 0.1, 2) >= 0)\n",
        )
    elif abbrev == "QRA":
        files["tests/test_qa_prioritization.py"] = _test_body(
            t,
            "import unittest\nfrom sa.qa_prioritization import prioritize_test_bucket_0\n",
            " def test_rank(self):\n  self.assertEqual(prioritize_test_bucket_0([{'name':'a','complexity':1}], {}), [('a', 'low')])\n",
        )
    return files


def gen_tests_bug_partial(abbrev):
    """Bug branch: weak tests on buggy target module only."""
    t = gen.FUTURE
    files = {"tests/__init__.py": t}
    if abbrev == "EPI":
        return files
    elif abbrev == "DOV":
        files["tests/test_decision_coverage.py"] = _test_body(
            t,
            "import unittest\nfrom sa.decision_coverage import decision_case_0\n",
            " def test_started_only(self):\n  self.assertTrue(decision_case_0('ready', True, 0).startswith('started'))\n",
        )
    elif abbrev == "LSV":
        files["tests/test_condition_coverage.py"] = _test_body(
            t,
            "import unittest\nfrom sa.condition_coverage import condition_check_0\n",
            " def test_partial_only(self):\n  self.assertEqual(condition_check_0(False, True, True, False, False), 'partial-0')\n",
        )
    elif abbrev == "TLCC":
        files["tests/test_logic_combinatorial.py"] = _test_body(
            t,
            "import unittest\nfrom sa.logic_combinatorial import count_unique_paths\n",
            " def test_zero(self):\n  self.assertEqual(count_unique_paths('x', 0), 0)\n",
        )
    elif abbrev == "TDI":
        return files
    elif abbrev == "QRA":
        files["tests/test_qa_prioritization.py"] = _test_body(
            t,
            "import unittest\nfrom sa.qa_prioritization import prioritize_test_bucket_0\n",
            " def test_low_only(self):\n  self.assertEqual(prioritize_test_bucket_0([{'name':'a','complexity':1}], {}), [('a', 'low')])\n",
        )
    return files


def gen_tests_cc_smoke(abbrev):
    """Minimal import smoke tests — CC branches rely on clean code, not full suites."""
    t = gen.FUTURE
    target = {
        "EPI": ("execution_path_integrity", "evaluate_path_integrity", "1, 'fast', {}"),
        "DOV": ("decision_coverage", "decision_case_0", "'ready', True, 0"),
        "LSV": ("condition_coverage", "condition_check_0", "True, True, False, True, True"),
        "TLCC": ("logic_combinatorial", "count_unique_paths", "'fn', 2"),
        "TDI": ("technical_debt", "debt_calculator_b0_v0", "10, 0.1, 1"),
        "QRA": ("qa_prioritization", "prioritize_test_bucket_0", "[{'name':'m','complexity':1}], {}"),
    }[abbrev]
    mod, fn, args = target
    return {
        "tests/__init__.py": t,
        "tests/test_%s_smoke.py" % mod: _test_body(
            t,
            "import unittest\nfrom sa.%s import %s\n" % (mod, fn),
            " def test_smoke(self):\n  self.assertTrue(%s(%s))\n" % (fn, args),
        ),
    }


def gen_tests_tcc(abbrev):
    """Full tests on all modules; target metric gets tool-oriented coverage cases."""
    files = gen_tests_full(abbrev)
    t = gen.FUTURE
    if abbrev == "DOV":
        files["tests/test_decision_coverage.py"] = _test_body(
            t,
            "import unittest\nfrom sa.decision_coverage import decision_case_0, aggregate_decision_coverage\n",
            " def test_started(self):\n  self.assertTrue(decision_case_0('ready', True, 0, 1).startswith('started'))\n"
            " def test_failed(self):\n  self.assertTrue(decision_case_0('failed', False, 0, 1).startswith('failed'))\n"
            " def test_priority(self):\n  self.assertTrue(decision_case_0('queued', True, 0, 9).startswith('priority'))\n"
            " def test_aggregate(self):\n  self.assertEqual(aggregate_decision_coverage([{'covered': True}]), 1.0)\n",
        )
    return files


def gen_tests_metric(abbrev, branch_type):
    if branch_type == "CC":
        return gen_tests_cc_smoke(abbrev)
    if branch_type == "TCC":
        return gen_tests_tcc(abbrev)
    if branch_type == "BugFX":
        return gen_tests_full(abbrev)
    if branch_type == "Bug":
        return gen_tests_bug_partial(abbrev)
    return {}


def gen_models_minimal():
    return gen.FUTURE + (
        "class AnalysisRecord(object):\n"
        "    def __init__(self, record_id, source_path, metric_name, score, status):\n"
        "        self.record_id = record_id\n"
    )


def gen_workflow_minimal():
    return gen.FUTURE + (
        "class StructuralAnalysisWorkflow(object):\n"
        "    def __init__(self, repository):\n"
        "        self.repository = repository\n"
        "    def run_all(self, snapshot):\n"
        "        return []\n"
    )


def _versions_text():
    path = os.path.join(ROOT, "versions.txt")
    if os.path.isfile(path):
        return open(path, encoding="utf-8").read()
    return "SA_<METRIC>_<TYPE>_2.6\n"


def generate_metric(root, abbrev, branch_type="Bug", version="2.6"):
    target_module = ABBREV_TO_MODULE[abbrev]
    meta = next(row for row in SA_METRICS if row[1] == abbrev)
    _, _, classification, metric_name, _ = meta
    bname = branch_name(abbrev, branch_type, version)

    module_meta = {row[0]: (row[3], row[4]) for row in SA_METRICS}

    def module_src(module_key):
        if module_key != target_module:
            met, tool = module_meta[module_key]
            return gen_metric_stub(module_key, met, tool)
        return generate_module_content(
            module_key, module_variant(module_key, target_module, branch_type))

    if os.path.isdir(root):
        shutil.rmtree(root)
    gen.ensure_dir(root)
    mapping = {
        "sa/__init__.py": gen.gen_init(),
        "sa/config.py": gen_config_metric(abbrev, branch_type, metric_name),
        "sa/models.py": gen_models_minimal(),
        "sa/execution_path_integrity.py": module_src("execution_path_integrity"),
        "sa/decision_coverage.py": module_src("decision_coverage"),
        "sa/condition_coverage.py": module_src("condition_coverage"),
        "sa/logic_combinatorial.py": module_src("logic_combinatorial"),
        "sa/technical_debt.py": module_src("technical_debt"),
        "sa/qa_prioritization.py": module_src("qa_prioritization"),
        "sa/rules_engine.py": gen_bulk_empty("rules_engine"),
        "sa/signal_processing.py": gen_bulk_empty("signal_processing"),
        "sa/integration_hub.py": gen_bulk_empty("integration_hub"),
        "sa/data_repository.py": gen.gen_repository("cc"),
        "sa/workflow_orchestrator.py": gen_workflow_minimal(),
        "sa/reporting.py": gen.gen_reporting("cc"),
        "main.py": gen.gen_main("cc"),
        "README.md": gen_readme_metric(bname, abbrev, metric_name, classification, branch_type),
        "requirements.txt": gen_requirements_metric(branch_type),
        "versions.txt": _versions_text(),
    }
    for rel, content in mapping.items():
        gen.write_file(root, rel, content)
    for rel, content in gen_tool_configs_metric(branch_type).items():
        gen.write_file(root, rel, content)
    for rel, content in gen_tests_metric(abbrev, branch_type).items():
        gen.write_file(root, rel, content)

    total = 0
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            if fn.endswith(".py"):
                with open(os.path.join(dirpath, fn), encoding="utf-8") as fh:
                    total += sum(1 for _ in fh)
    print("Generated %s (target=%s, type=%s, %d python lines)" % (bname, abbrev, branch_type, total))
    return bname


def main():
    parser = argparse.ArgumentParser(description="Generate metric-scoped SA branches")
    parser.add_argument(
        "--metric",
        choices=[abbrev for _, abbrev, _, _, _ in SA_METRICS] + ["all"],
        default="all",
    )
    parser.add_argument(
        "--branch-type",
        choices=list(BRANCH_TYPES) + ["all"],
        default="all",
        help="Bug, BugFX, TCC, CC, or all",
    )
    parser.add_argument("--version", default="2.6")
    parser.add_argument("--out", default="build")
    args = parser.parse_args()

    abbrevs = [a for _, a, _, _, _ in SA_METRICS] if args.metric == "all" else [args.metric]
    branch_types = list(BRANCH_TYPES) if args.branch_type == "all" else [args.branch_type]
    for abbrev in abbrevs:
        for bt in branch_types:
            bname = branch_name(abbrev, bt, args.version)
            generate_metric(
                os.path.join(args.out, bname),
                abbrev,
                branch_type=bt,
                version=args.version,
            )


if __name__ == "__main__":
    main()
