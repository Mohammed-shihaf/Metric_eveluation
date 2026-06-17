"""Classify local tool reports for branch-generation diagnostics."""

from __future__ import print_function

import csv
import json
import os
from collections import defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DIAGNOSTICS_DIR = os.path.join(ROOT, "proofs", "_diagnostics")


def _report_extra(report):
    return report.get("extra") or {}


def _tool_outcome(report):
    extra = _report_extra(report)
    if extra.get("tool_outcome"):
        return str(extra["tool_outcome"]).upper()
    raw = (extra.get("actual_outcome") or report.get("raw_summary") or "").upper()
    if raw.startswith("FAIL"):
        return "FAIL"
    if raw.startswith("PASS") or raw.startswith("WARN"):
        return "PASS"
    status = str(report.get("status") or "").upper()
    if status in ("PASS", "FAIL"):
        return status
    return ""


def _assert_status(report):
    extra = _report_extra(report)
    if extra.get("assert_status"):
        return str(extra["assert_status"]).upper()
    status = str(report.get("status") or "").upper()
    if status in ("PASS", "FAIL"):
        return status
    return status


def _bool_val(value):
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    text = str(value).strip().lower()
    if text in ("true", "1", "yes"):
        return True
    if text in ("false", "0", "no"):
        return False
    return None


def classify_branch(report):
    """Return {category, reason} for a local_report.json dict."""
    extra = _report_extra(report)
    branch_type = report.get("branch_type") or ""
    status = str(report.get("status") or "").upper()
    real_tool = _bool_val(extra.get("real_tool"))
    tool_outcome = _tool_outcome(report)
    assert_status = _assert_status(report)
    strength_pass = _bool_val(extra.get("strength_pass"))
    config_effective = _bool_val(extra.get("config_effective"))

    if status in ("UNAVAILABLE",) or real_tool is False:
        return {
            "category": "unavailable",
            "reason": extra.get("tool_unavailable") or extra.get("skip_reason") or "real tool did not execute",
        }
    if status == "ERROR":
        return {
            "category": "error",
            "reason": extra.get("tool_stderr") or extra.get("install_error") or report.get("raw_summary") or "execution error",
        }
    if status == "SKIPPED":
        return {
            "category": "error",
            "reason": extra.get("skip_reason") or "skipped",
        }

    if assert_status == "PASS":
        return {"category": "correct", "reason": "assert PASS (type + strength + isolation)"}

    if branch_type == "Bug" and tool_outcome == "PASS":
        return {
            "category": "wrong_pass",
            "reason": "Bug branch expected tool FAIL but got PASS (defect too weak)",
        }
    if branch_type != "Bug" and tool_outcome == "FAIL":
        return {
            "category": "wrong_fail",
            "reason": "non-Bug branch expected tool PASS but got FAIL (defect not resolved)",
        }
    if branch_type == "TCC" and config_effective is False:
        return {
            "category": "config_ineffective",
            "reason": "TCC branch missing effective tool config (.coveragerc, etc.)",
        }
    if strength_pass is False:
        return {
            "category": "weak_strength",
            "reason": extra.get("strength_reason") or "strength_pass=False",
        }

    return {
        "category": "weak_strength",
        "reason": extra.get("actual_outcome") or extra.get("strength_reason") or "assert FAIL (unclassified)",
    }


def report_row(report, report_path=""):
    """Flatten a report into a diagnostic row dict."""
    extra = _report_extra(report)
    classification = classify_branch(report)
    return {
        "branch_name": report.get("branch_name", ""),
        "technique_code": report.get("technique_code", ""),
        "metric_code": report.get("metric_code", ""),
        "branch_type": report.get("branch_type", ""),
        "family": extra.get("tool_family", ""),
        "status": report.get("status", ""),
        "assert_status": extra.get("assert_status", ""),
        "executed_tool": extra.get("executed_tool", report.get("tool_name", "")),
        "real_tool": extra.get("real_tool"),
        "tool_outcome": extra.get("tool_outcome", _tool_outcome(report)),
        "metric_value": extra.get("metric_value", ""),
        "raw_metric_value": extra.get("raw_metric_value", report.get("raw_summary", "")),
        "strength_score": extra.get("strength_score", ""),
        "strength_pass": extra.get("strength_pass", ""),
        "config_effective": extra.get("config_effective", ""),
        "category": classification["category"],
        "reason": classification["reason"],
        "report_path": report_path or extra.get("report_path", ""),
    }


def aggregate(rows):
    """Build summary counts from diagnostic rows."""
    by_category = defaultdict(int)
    by_technique = defaultdict(lambda: defaultdict(int))
    by_metric = defaultdict(lambda: defaultdict(int))
    by_branch_type = defaultdict(lambda: defaultdict(int))
    by_family = defaultdict(lambda: defaultdict(int))

    for row in rows:
        cat = row.get("category", "unknown")
        tech = row.get("technique_code", "?")
        metric = "%s/%s" % (tech, row.get("metric_code", "?"))
        bt = row.get("branch_type", "?")
        family = row.get("family", "?")

        by_category[cat] += 1
        by_technique[tech][cat] += 1
        by_metric[metric][cat] += 1
        by_branch_type[bt][cat] += 1
        by_family[family][cat] += 1

    def _hotspots(bucket, limit=10):
        scored = []
        for key, counts in bucket.items():
            bad = sum(counts.get(c, 0) for c in (
                "wrong_pass", "wrong_fail", "weak_strength", "config_ineffective", "unavailable", "error"
            ))
            if bad:
                scored.append((bad, key, dict(counts)))
        scored.sort(reverse=True)
        return [{"key": k, "bad_count": bad, "counts": counts} for bad, k, counts in scored[:limit]]

    total = len(rows)
    correct = by_category.get("correct", 0)
    return {
        "total": total,
        "correct": correct,
        "correct_pct": round(100.0 * correct / total, 1) if total else 0.0,
        "by_category": dict(by_category),
        "by_technique": {k: dict(v) for k, v in by_technique.items()},
        "by_metric": {k: dict(v) for k, v in by_metric.items()},
        "by_branch_type": {k: dict(v) for k, v in by_branch_type.items()},
        "by_family": {k: dict(v) for k, v in by_family.items()},
        "hotspots": {
            "techniques": _hotspots(by_technique),
            "metrics": _hotspots(by_metric),
            "families": _hotspots(by_family),
        },
    }


def load_local_reports(proofs_root=None, branch_names=None):
    """Load local_report.json files from proofs/."""
    proofs_root = proofs_root or os.path.join(ROOT, "proofs")
    rows = []
    if not os.path.isdir(proofs_root):
        return rows

    wanted = set(branch_names or [])
    for tech in sorted(os.listdir(proofs_root)):
        tech_dir = os.path.join(proofs_root, tech)
        if not os.path.isdir(tech_dir) or tech.startswith("_"):
            continue
        for bname in sorted(os.listdir(tech_dir)):
            if wanted and bname not in wanted:
                continue
            report_path = os.path.join(tech_dir, bname, "local_report.json")
            if not os.path.isfile(report_path):
                continue
            try:
                with open(report_path, encoding="utf-8") as fh:
                    report = json.load(fh)
            except (ValueError, OSError, TypeError):
                continue
            rows.append(report_row(report, report_path))
    return rows


def write_sweep_outputs(rows, aggregates, output_dir=None):
    """Write sweep_report.json, sweep_report.csv, sweep_summary.md."""
    output_dir = output_dir or DIAGNOSTICS_DIR
    os.makedirs(output_dir, exist_ok=True)

    payload = {
        "rows": rows,
        "aggregates": aggregates,
    }
    json_path = os.path.join(output_dir, "sweep_report.json")
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)

    csv_path = os.path.join(output_dir, "sweep_report.csv")
    if rows:
        fieldnames = list(rows[0].keys())
        with open(csv_path, "w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    md_path = os.path.join(output_dir, "sweep_summary.md")
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write("# All-Tools Sweep Summary\n\n")
        fh.write("Total branches: **%d** | Correct: **%d** (%.1f%%)\n\n" % (
            aggregates.get("total", 0),
            aggregates.get("correct", 0),
            aggregates.get("correct_pct", 0),
        ))
        fh.write("## By category\n\n")
        fh.write("| Category | Count |\n|----------|-------|\n")
        for cat, count in sorted((aggregates.get("by_category") or {}).items()):
            fh.write("| %s | %d |\n" % (cat, count))
        fh.write("\n## Generation hotspots (techniques)\n\n")
        for item in (aggregates.get("hotspots") or {}).get("techniques", []):
            fh.write("- **%s**: %d issues — %s\n" % (item["key"], item["bad_count"], item["counts"]))
        fh.write("\n## Generation hotspots (families)\n\n")
        for item in (aggregates.get("hotspots") or {}).get("families", []):
            fh.write("- **%s**: %d issues — %s\n" % (item["key"], item["bad_count"], item["counts"]))
        fh.write("\n## Generation hotspots (metrics)\n\n")
        for item in (aggregates.get("hotspots") or {}).get("metrics", [])[:15]:
            fh.write("- **%s**: %d issues — %s\n" % (item["key"], item["bad_count"], item["counts"]))

    return {"json": json_path, "csv": csv_path, "md": md_path}


def build_diagnostics(proofs_root=None, branch_names=None, output_dir=None):
    """Load reports, classify, aggregate, and write outputs."""
    rows = load_local_reports(proofs_root=proofs_root, branch_names=branch_names)
    aggregates = aggregate(rows)
    paths = write_sweep_outputs(rows, aggregates, output_dir=output_dir)
    return {"rows": rows, "aggregates": aggregates, "paths": paths}
