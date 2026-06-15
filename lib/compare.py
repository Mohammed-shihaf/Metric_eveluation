"""Compare S3 and local standard tool reports."""

from __future__ import print_function

import json
import os
from pathlib import Path

from lib.report_schema import SCHEMA_VERSION, load_report, save_report

COMPARE_TOLERANCE = 0.5  # percentage points for float metric values


def _status_compatible(s3_status, local_status):
    if s3_status == local_status:
        return True
    warn_set = {"PASS", "WARN"}
    if s3_status in warn_set and local_status in warn_set:
        return True
    return False


def _metric_diff(key, left_val, right_val, left_label="left", right_label="right"):
    if left_val is None and right_val is None:
        return None
    if left_val is None or right_val is None:
        return {"field": key, left_label: left_val, right_label: right_val, "match": False}
    if isinstance(left_val, (int, float)) and isinstance(right_val, (int, float)):
        match = abs(float(left_val) - float(right_val)) <= COMPARE_TOLERANCE
        return {
            "field": key, left_label: left_val, right_label: right_val,
            "match": match, "delta": float(right_val) - float(left_val),
        }
    return {
        "field": key, left_label: left_val, right_label: right_val,
        "match": left_val == right_val,
    }


def compare_reports_pair(
    left_report,
    right_report,
    left_label="s3",
    right_label="local",
    require_tool_match=True,
    shared_metrics_only=False,
):
    """Return structured comparison between two standard tool reports."""
    branch = left_report.get("branch_name") or right_report.get("branch_name", "")
    diffs = []

    if left_report.get("branch_name") != right_report.get("branch_name"):
        diffs.append({
            "field": "branch_name",
            left_label: left_report.get("branch_name"),
            right_label: right_report.get("branch_name"),
            "match": False,
        })

    left_status = left_report.get("status", "ERROR")
    right_status = right_report.get("status", "ERROR")
    status_match = _status_compatible(left_status, right_status)
    diffs.append({
        "field": "status",
        left_label: left_status,
        right_label: right_status,
        "match": status_match,
    })

    left_tool = left_report.get("tool_name", "")
    right_tool = right_report.get("tool_name", "")
    tool_match = True if not require_tool_match else _tool_names_compatible(left_tool, right_tool)
    diffs.append({
        "field": "tool_name",
        left_label: left_tool,
        right_label: right_tool,
        "match": tool_match,
    })

    left_values = left_report.get("metric_values") or {}
    right_values = right_report.get("metric_values") or {}
    if shared_metrics_only:
        all_keys = sorted(set(left_values) & set(right_values))
    else:
        all_keys = sorted(set(left_values) | set(right_values))
    metric_diffs = []
    for key in all_keys:
        row = _metric_diff(key, left_values.get(key), right_values.get(key), left_label, right_label)
        if row:
            metric_diffs.append(row)
            diffs.append(row)

    hard_mismatches = [d for d in diffs if not d.get("match")]
    if not hard_mismatches:
        verdict = "MATCH"
    elif status_match and not metric_diffs:
        verdict = "PARTIAL"
    elif status_match:
        verdict = "PARTIAL"
    else:
        verdict = "MISMATCH"

    reasons = []
    if not status_match:
        reasons.append("status differs: %s=%s %s=%s" % (left_label, left_status, right_label, right_status))
    if require_tool_match and not tool_match:
        reasons.append("tool differs: %s=%r %s=%r" % (left_label, left_tool, right_label, right_tool))
    for md in metric_diffs:
        if not md.get("match"):
            reasons.append(
                "%s differs: %s=%s %s=%s"
                % (md["field"], left_label, md.get(left_label), right_label, md.get(right_label))
            )

    align_msg = "%s and %s reports align" % (left_label, right_label)
    return {
        "schema_version": SCHEMA_VERSION,
        "branch_name": branch,
        "verdict": verdict,
        "status_match": status_match,
        "tool_match": tool_match,
        "field_diffs": diffs,
        "metric_diffs": metric_diffs,
        "summary": "; ".join(reasons) if reasons else align_msg,
        "%s_report_path" % left_label: left_report.get("_path", ""),
        "%s_report_path" % right_label: right_report.get("_path", ""),
    }


def compare_reports(s3_report, local_report):
    """Return structured comparison between S3 and local standard tool reports."""
    result = compare_reports_pair(s3_report, local_report, "s3", "local")
    result["s3_report_path"] = result.pop("s3_report_path", s3_report.get("_path", ""))
    result["local_report_path"] = result.pop("local_report_path", local_report.get("_path", ""))
    if result["summary"].endswith("reports align"):
        result["summary"] = "S3 and local reports align"
    return result


def _tool_names_compatible(s3_tool, local_tool):
    if not s3_tool or not local_tool:
        return True
    s3 = s3_tool.lower().replace(" ", "")
    local = local_tool.lower().replace(" ", "")
    if s3 == local:
        return True
    if "coverage" in s3 and "coverage" in local:
        return True
    if s3 in local or local in s3:
        return True
    return False


def compare_report_files(s3_path, local_path):
    s3_report = load_report(s3_path)
    local_report = load_report(local_path)
    s3_report["_path"] = str(s3_path)
    local_report["_path"] = str(local_path)
    return compare_reports(s3_report, local_report)


def compare_batch(proof_root, branches=None):
    """Compare s3_report.json vs local_report.json for branches under proof_root."""
    proof_root = Path(proof_root)
    results = []
    for tech_dir in sorted(proof_root.iterdir()):
        if not tech_dir.is_dir():
            continue
        for branch_dir in sorted(tech_dir.iterdir()):
            if not branch_dir.is_dir():
                continue
            branch_name = branch_dir.name
            if branches and branch_name not in branches:
                continue
            s3_path = branch_dir / "s3_report.json"
            local_path = branch_dir / "local_report.json"
            if not s3_path.is_file() or not local_path.is_file():
                results.append({
                    "branch_name": branch_name,
                    "verdict": "INCOMPLETE",
                    "summary": "missing %s" % (
                        "both reports"
                        if not s3_path.is_file() and not local_path.is_file()
                        else ("s3_report" if not s3_path.is_file() else "local_report")
                    ),
                    "proof_dir": str(branch_dir),
                })
                continue
            comparison = compare_report_files(s3_path, local_path)
            comparison["proof_dir"] = str(branch_dir)
            out_path = branch_dir / "comparison.json"
            save_report(comparison, out_path)
            comparison["comparison_path"] = str(out_path)
            results.append(comparison)
    return results


def compare_three_reports(taxonomy_report, s3_report, local_report):
    """Compare taxonomy, S3, and local standard reports."""
    s3_local = compare_reports(s3_report, local_report)
    tax_status = (taxonomy_report or {}).get("status", "SKIPPED")
    s3_status = (s3_report or {}).get("status", "SKIPPED")
    local_status = (local_report or {}).get("status", "SKIPPED")
    all_match = tax_status == s3_status == local_status or (
        tax_status in ("PASS", "WARN") and s3_status in ("PASS", "WARN") and local_status in ("PASS", "WARN")
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "branch_name": s3_report.get("branch_name") or local_report.get("branch_name", ""),
        "verdict": "MATCH" if all_match and s3_local["verdict"] == "MATCH" else (
            "PARTIAL" if s3_local["verdict"] in ("MATCH", "PARTIAL") else "MISMATCH"
        ),
        "taxonomy_status": tax_status,
        "s3_status": s3_status,
        "local_status": local_status,
        "s3_vs_local": s3_local,
        "summary": "taxonomy=%s s3=%s local=%s; %s" % (
            tax_status, s3_status, local_status, s3_local.get("summary", "")),
    }


def _statuses_compatible(*statuses):
    normalized = [s for s in statuses if s and s != "SKIPPED"]
    if not normalized:
        return True
    first = normalized[0]
    if all(s == first for s in normalized):
        return True
    warn_set = {"PASS", "WARN"}
    return all(s in warn_set for s in normalized)


def compare_four_reports(taxonomy_report, s3_report, local_report, sonar_report):
    """Compare taxonomy, S3, local, and SonarQube standard reports."""
    s3_local = compare_reports(s3_report, local_report)
    local_sonar = compare_reports_pair(
        local_report,
        sonar_report,
        left_label="local",
        right_label="sonar",
        require_tool_match=False,
        shared_metrics_only=True,
    )

    tax_status = (taxonomy_report or {}).get("status", "SKIPPED")
    s3_status = (s3_report or {}).get("status", "SKIPPED")
    local_status = (local_report or {}).get("status", "SKIPPED")
    sonar_status = (sonar_report or {}).get("status", "SKIPPED")

    all_status_match = _statuses_compatible(
        tax_status, s3_status, local_status, sonar_status
    )
    tool_pair_match = (
        local_sonar["verdict"] == "MATCH"
        and s3_local["verdict"] in ("MATCH", "PARTIAL")
    )

    if all_status_match and local_sonar["verdict"] == "MATCH":
        verdict = "MATCH"
    elif all_status_match or tool_pair_match:
        verdict = "PARTIAL"
    else:
        verdict = "MISMATCH"

    summary_parts = [
        "taxonomy=%s s3=%s local=%s sonar=%s" % (
            tax_status, s3_status, local_status, sonar_status),
        "local_vs_sonar: %s" % local_sonar.get("summary", ""),
        "s3_vs_local: %s" % s3_local.get("summary", ""),
    ]

    return {
        "schema_version": SCHEMA_VERSION,
        "branch_name": (
            sonar_report.get("branch_name")
            or local_report.get("branch_name")
            or s3_report.get("branch_name", "")
        ),
        "verdict": verdict,
        "taxonomy_status": tax_status,
        "s3_status": s3_status,
        "local_status": local_status,
        "sonar_status": sonar_status,
        "s3_vs_local": s3_local,
        "local_vs_sonar": local_sonar,
        "summary": "; ".join(summary_parts),
    }


def summarize_comparisons(results):
    total = len(results)
    match = sum(1 for r in results if r.get("verdict") == "MATCH")
    partial = sum(1 for r in results if r.get("verdict") == "PARTIAL")
    mismatch = sum(1 for r in results if r.get("verdict") == "MISMATCH")
    incomplete = sum(1 for r in results if r.get("verdict") == "INCOMPLETE")
    return {
        "total": total,
        "match": match,
        "partial": partial,
        "mismatch": mismatch,
        "incomplete": incomplete,
    }
