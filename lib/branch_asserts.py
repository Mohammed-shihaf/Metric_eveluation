"""Combined per-branch assert validation: structure + tool-support + metric-behavior."""

from __future__ import print_function

import os

from lib.registry import iter_branches, metric_entry
from lib.tool_assert import RUNNERS, tool_assert_branch, tool_family
from lib.tool_map import metric_tool, pip_packages_for_family
from lib.lang_tool_runners import packages_for_language
from lib.validate import BranchValidationError, validate_branch


def _check_tool_support(technique_code, metric_code, branch_path, language="python"):
    info = metric_tool(technique_code, metric_code, language)
    family = info["family"]
    primary = info["primary"]
    if family == "unknown":
        return "FAIL", "unknown tool family for primary %r" % primary
    if (language or "python").lower() == "python" and family not in RUNNERS:
        return "FAIL", "no runner for family %s" % family
    pkgs = packages_for_language(family, primary, language) or pip_packages_for_family(family, primary)
    return "PASS", "family=%s lang=%s packages=%s" % (family, language, ",".join(pkgs))


def assert_branch_full(branch_path, technique_code=None, metric_code=None, branch_type=None,
                       version="2.6", language="python", run_tool=True, require_real_tool=False):
    """Run all three assert layers for one branch directory."""
    folder = os.path.basename(os.path.normpath(branch_path))
    from lib.metrics import parse_branch_name

    parsed = parse_branch_name(folder)
    if not parsed:
        return {
            "branch_name": folder,
            "overall": "FAIL",
            "structure": "FAIL",
            "tool_support": "FAIL",
            "metric_behavior": "SKIPPED",
            "messages": ["unparseable branch name"],
        }

    technique_code = (technique_code or parsed["tech"]).upper()
    metric_code = (metric_code or parsed["metric"]).upper()
    branch_type = branch_type or parsed["type"]
    messages = []

    try:
        validate_branch(branch_path, technique_code, metric_code, branch_type, version, language)
        structure = "PASS"
    except BranchValidationError as exc:
        structure = "FAIL"
        messages.append("structure: %s" % exc)

    ts_status, ts_msg = _check_tool_support(technique_code, metric_code, branch_path, language)
    tool_support = ts_status
    messages.append("tool_support: %s" % ts_msg)

    metric_behavior = "SKIPPED"
    tr = None
    if run_tool and structure == "PASS":
        tr = tool_assert_branch(
            branch_path,
            technique_code,
            metric_code,
            branch_type,
            language,
            require_real_tool=require_real_tool,
        )
        actual = str(tr.get("actual_outcome", "")).upper()
        strength_pass = tr.get("strength_pass", False)
        real_tool = tr.get("real_tool", True)
        if tr.get("status") == "UNAVAILABLE" or (require_real_tool and not real_tool):
            metric_behavior = "FAIL"
        elif tr.get("status") == "SKIPPED":
            metric_behavior = "SKIPPED"
        elif strength_pass and tr.get("status") == "PASS":
            metric_behavior = "PASS"
        else:
            metric_behavior = "FAIL"
        messages.append(
            "metric_behavior: tool=%s raw=%s strength=%.1f expected=%s actual=%s"
            % (
                tr.get("tool_used"),
                tr.get("raw_metric_value"),
                tr.get("strength_score", 0),
                tr.get("expected_threshold", "")[:40],
                tr.get("actual_outcome"),
            )
        )
        if require_real_tool:
            messages.append("real_tool=%s" % real_tool)
        if tr.get("strength_reason"):
            messages.append("strength: %s" % tr.get("strength_reason"))

    overall = "PASS"
    if structure != "PASS" or tool_support != "PASS" or metric_behavior == "FAIL":
        overall = "FAIL"
    elif metric_behavior == "SKIPPED":
        overall = "PARTIAL"

    _, metric = metric_entry(technique_code, metric_code)
    row = {
        "branch_name": folder,
        "technique_code": technique_code,
        "metric_code": metric_code,
        "branch_type": branch_type,
        "module_key": metric["module_key"],
        "structure": structure,
        "tool_support": tool_support,
        "metric_behavior": metric_behavior,
        "overall": overall,
        "messages": messages,
        "strength_score": tr.get("strength_score") if tr else None,
        "expected_threshold": metric.get("expected_threshold", ""),
        "strength_pass": tr.get("strength_pass") if tr else None,
    }
    return row


def assert_build_batch(techniques="all", metrics="all", types=None, version="2.6",
                       language="python", build_dir="build", root=None, run_tool=True,
                       progress_callback=None):
    repo_root = root or os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    planned = list(iter_branches(techniques, metrics, types, version))
    total = len(planned)
    results = []
    for idx, (tech, metric, bt, bname) in enumerate(planned, start=1):
        path = os.path.join(repo_root, build_dir, bname)
        if progress_callback:
            progress_callback("assert", idx - 1, total, bname, "validating")
        if not os.path.isdir(path):
            row = {
                "branch_name": bname,
                "overall": "FAIL",
                "structure": "MISSING",
                "tool_support": "SKIPPED",
                "metric_behavior": "SKIPPED",
                "messages": ["build dir missing"],
            }
        else:
            row = assert_branch_full(path, tech, metric, bt, version, language, run_tool)
        results.append(row)
        if progress_callback:
            progress_callback("assert", idx, total, bname, row["overall"])
    return results
