"""Canonical tool-report schema — one format for S3 and local execution."""

from __future__ import print_function

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from lib.tool_assert import (
    CHURN_FAIL_THRESHOLD,
    COMPLEXITY_FAIL_THRESHOLD,
    COVERAGE_FAIL_THRESHOLD,
    DUP_FAIL_THRESHOLD,
    MUTATION_RATIO_FAIL,
    _branch_context,
)

SCHEMA_VERSION = "1.0"
VALID_SOURCES = ("s3", "local", "taxonomy", "sonar")
VALID_STATUSES = ("PASS", "FAIL", "WARN", "SKIPPED", "ERROR")


def _utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _normalize_status(value):
    if not value:
        return "ERROR"
    v = str(value).strip().upper()
    if v in VALID_STATUSES:
        return v
    if v.startswith("PASS"):
        return "PASS"
    if v.startswith("FAIL"):
        return "FAIL"
    if v.startswith("WARN"):
        return "WARN"
    if v.startswith("SKIP"):
        return "SKIPPED"
    return "ERROR"


def _outcome_from_violation(violation):
    return "FAIL" if violation else "PASS"


def make_report(
    technique_code,
    metric_code,
    branch_name,
    branch_type,
    version,
    tool_name,
    source,
    status,
    metric_values=None,
    raw_summary="",
    commit_sha=None,
    run_id=None,
    generated_at=None,
    extra=None,
):
    report = {
        "schema_version": SCHEMA_VERSION,
        "technique_code": technique_code.upper(),
        "metric_code": metric_code.upper(),
        "branch_name": branch_name,
        "branch_type": branch_type,
        "version": str(version),
        "tool_name": tool_name or "",
        "source": source if source in VALID_SOURCES else "local",
        "status": _normalize_status(status),
        "metric_values": dict(metric_values or {}),
        "raw_summary": raw_summary or "",
        "commit_sha": commit_sha or "",
        "run_id": run_id or "",
        "generated_at": generated_at or _utc_now(),
    }
    if extra:
        report["extra"] = extra
    return report


def save_report(report, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    return str(path)


def load_report(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _parse_metric_values_from_raw(raw_summary):
    values = {}
    if not raw_summary:
        return values
    for key, pattern in (
        ("coverage_pct", r"([\d.]+)%\s*cov"),
        ("max_cc", r"max_cc=(\d+)"),
        ("findings", r"findings=(\d+)"),
        ("vulns", r"vulns=(\d+)"),
        ("test_fn_ratio", r"test_fn_ratio=([\d.]+)"),
        ("churn_score", r"churn_score=([\d.]+)"),
        ("dup_pct", r"dup=([\d.]+)%"),
        ("issues", r"issues=(\d+)"),
        ("tests", r"tests=(\d+)"),
    ):
        m = re.search(pattern, raw_summary)
        if m:
            try:
                values[key] = float(m.group(1)) if "." in m.group(1) else int(m.group(1))
            except ValueError:
                values[key] = m.group(1)
    return values


def from_tool_assert_result(result, source="local", commit_sha=None, run_id=None, version=None):
    """Convert tool_assert_branch() output into the standard schema."""
    branch_name = result.get("branch_name", "")
    technique_code = result.get("technique_code", "")
    metric_code = result.get("metric_code", "")
    branch_type = result.get("branch_type", "")
    raw = result.get("raw_metric_value", "")

    extra = {}
    if result.get("log"):
        extra["tool_log"] = result.get("log")
    if result.get("status") == "SKIPPED" and result.get("message"):
        extra["skip_reason"] = result.get("message")
    if result.get("status") == "SKIPPED":
        norm_status = "SKIPPED"
        metric_values = {}
        family = ""
        raw = raw or result.get("message", "")
    else:
        metric_values = _parse_metric_values_from_raw(raw)
        family = _tool_family_for_metric(technique_code, metric_code)
        if metric_values and family:
            norm_status = _status_from_metric_values(family, metric_values, branch_type)
        elif not raw:
            norm_status = "ERROR"
        else:
            norm_status = "ERROR"

    if not version:
        from lib.metrics import parse_branch_name

        parsed = parse_branch_name(branch_name)
        version = parsed["version"] if parsed else "2.6"

    if family:
        extra["tool_family"] = family

    return make_report(
        technique_code=technique_code,
        metric_code=metric_code,
        branch_name=branch_name,
        branch_type=branch_type,
        version=version,
        tool_name=result.get("tool_used", ""),
        source=source,
        status=norm_status,
        metric_values=metric_values,
        raw_summary=raw,
        commit_sha=commit_sha,
        run_id=run_id,
        extra=extra or None,
    )


def _tool_family_for_metric(technique_code, metric_code):
    from lib.registry import metric_entry
    from lib.tool_assert import tool_family

    try:
        tech, metric = metric_entry(technique_code, metric_code)
        tools = (metric.get("tools") or {}).get("python", {})
        primary = (tools.get("primary") or "").strip()
        return tool_family(primary, tech["technique_code"])
    except (KeyError, TypeError):
        return ""


def _read_json(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError, TypeError):
        return None


def _coverage_from_json(data, target_rel):
    totals = data.get("totals") or {}
    files = data.get("files") or {}
    target_key = target_rel.replace("\\", "/")
    file_entry = files.get(target_key)
    if not file_entry:
        for k, v in files.items():
            if k.replace("\\", "/").endswith(target_key.split("/")[-1]):
                file_entry = v
                break
    covered = int(totals.get("covered_lines") or 0)
    statements = int(totals.get("num_statements") or 0)
    pct = round(100.0 * covered / statements, 1) if statements else 0.0
    target_stmts = 0
    if file_entry:
        target_stmts = int((file_entry.get("summary") or {}).get("num_statements") or 0)
    return {
        "coverage_pct": pct,
        "num_statements": statements,
        "covered_lines": covered,
        "target_statements": target_stmts,
    }


def _status_from_metric_values(family, values, branch_type=None):
    if family == "coverage":
        pct = float(values.get("coverage_pct", 0))
        violation = pct < COVERAGE_FAIL_THRESHOLD
        return _outcome_from_violation(violation)
    if family == "complexity":
        max_cc = int(values.get("max_cc", 0))
        return _outcome_from_violation(max_cc > COMPLEXITY_FAIL_THRESHOLD)
    if family == "security":
        findings = int(values.get("findings", 0))
        return _outcome_from_violation(findings > 0)
    if family == "sca":
        vulns = int(values.get("vulns", 0))
        return _outcome_from_violation(vulns > 0)
    if family == "mutation":
        ratio = float(values.get("test_fn_ratio", 1))
        return _outcome_from_violation(ratio < MUTATION_RATIO_FAIL)
    if family == "churn":
        score = float(values.get("churn_score", 0))
        return _outcome_from_violation(score > CHURN_FAIL_THRESHOLD)
    if family == "duplication":
        dup = float(values.get("dup_pct", 0))
        return _outcome_from_violation(dup > DUP_FAIL_THRESHOLD)
    if family == "lint":
        issues = int(values.get("issues", 0))
        return _outcome_from_violation(issues > 0)
    return "PASS"


def _extract_s3_metric_values(tool_root, family, ctx):
    root = Path(tool_root)
    values = {}
    raw_parts = []

    if family in ("coverage", "crosshair", "pymcdc"):
        cov_path = root / "coverage-py" / "0" / "coverage.json"
        data = _read_json(cov_path)
        if data:
            values.update(_coverage_from_json(data, ctx["target_rel"]))
            raw_parts.append("%.1f%% cov stmts=%d" % (values["coverage_pct"], values["num_statements"]))
        return values, " ".join(raw_parts)

    if family == "complexity":
        for pattern in ("radon-cc/*/output.json", "radon/*/cc.json", "complexity/*/output.json"):
            for path in root.glob(pattern):
                data = _read_json(path)
                if data:
                    scores = []
                    if isinstance(data, list):
                        for row in data:
                            if isinstance(row, dict):
                                scores.append(int(row.get("complexity", row.get("rank", 0)) or 0))
                    elif isinstance(data, dict):
                        for v in data.values():
                            if isinstance(v, dict) and "complexity" in v:
                                scores.append(int(v["complexity"]))
                    if scores:
                        values["max_cc"] = max(scores)
                        raw_parts.append("max_cc=%d" % values["max_cc"])
                        return values, " ".join(raw_parts)
        return values, ""

    if family == "security":
        for pattern in ("bandit/*/output.json", "bandit-py/*/output.json", "semgrep/*/output.json"):
            for path in root.glob(pattern):
                data = _read_json(path)
                if isinstance(data, dict):
                    n = len(data.get("results", []))
                    values["findings"] = max(int(values.get("findings", 0)), n)
        if values:
            raw_parts.append("findings=%d" % values["findings"])
        return values, " ".join(raw_parts)

    if family == "sca":
        for pattern in ("pip-audit/*/output.json", "safety/*/output.json"):
            for path in root.glob(pattern):
                data = _read_json(path)
                if isinstance(data, list):
                    values["vulns"] = len(data)
                elif isinstance(data, dict):
                    values["vulns"] = len(data.get("dependencies", []))
        if values:
            raw_parts.append("vulns=%d" % values["vulns"])
        return values, " ".join(raw_parts)

    if family == "duplication":
        for pattern in ("jscpd/*/jscpd-report.json", "jscpd/*/output.json"):
            for path in root.glob(pattern):
                data = _read_json(path)
                if isinstance(data, dict):
                    stats = (data.get("statistics") or {}).get("total") or {}
                    values["dup_pct"] = float(stats.get("percentage", 0))
                    raw_parts.append("dup=%.1f%%" % values["dup_pct"])
                    return values, " ".join(raw_parts)
        return values, ""

    if family == "lint":
        for pattern in ("flake8/*/output.json", "pylint/*/output.json"):
            for path in root.glob(pattern):
                data = _read_json(path)
                if isinstance(data, dict):
                    values["issues"] = int(data.get("issue_count", len(data.get("messages", []))))
                    raw_parts.append("issues=%d" % values["issues"])
                    return values, " ".join(raw_parts)
        return values, ""

    cov_path = root / "coverage-py" / "0" / "coverage.json"
    if cov_path.is_file():
        data = _read_json(cov_path)
        if data:
            values.update(_coverage_from_json(data, ctx["target_rel"]))
            raw_parts.append("%.1f%% cov (fallback)" % values["coverage_pct"])
    return values, " ".join(raw_parts)


def from_s3_tool_root(
    tool_root,
    technique_code,
    metric_code,
    branch_name,
    branch_type,
    version,
    commit_sha="",
    run_id="",
    tool_name="",
):
    """Normalize a downloaded S3 tool bundle into the standard schema."""
    ctx = _branch_context(tool_root, technique_code, metric_code)
    family = ctx["family"]
    primary = tool_name or ctx["primary"]
    metric_values, raw_summary = _extract_s3_metric_values(tool_root, family, ctx)

    if not metric_values and not raw_summary:
        return make_report(
            technique_code=technique_code,
            metric_code=metric_code,
            branch_name=branch_name,
            branch_type=branch_type,
            version=version,
            tool_name=primary,
            source="s3",
            status="SKIPPED",
            metric_values={},
            raw_summary="no recognizable tool output in S3 bundle",
            commit_sha=commit_sha,
            run_id=run_id,
            extra={"tool_root": str(tool_root), "family": family},
        )

    status = _status_from_metric_values(family, metric_values, branch_type)
    return make_report(
        technique_code=technique_code,
        metric_code=metric_code,
        branch_name=branch_name,
        branch_type=branch_type,
        version=version,
        tool_name=primary,
        source="s3",
        status=status,
        metric_values=metric_values,
        raw_summary=raw_summary,
        commit_sha=commit_sha,
        run_id=run_id,
        extra={"tool_root": str(tool_root), "family": family},
    )


def _taxonomy_result_for_class(html, classification):
    import re
    if not classification or not html:
        return ""
    pattern = (
        r'<div class="cls-name">%s</div>.*?<span class="rp rp-(\w+)">'
        % re.escape(classification)
    )
    m = re.search(pattern, html, re.DOTALL | re.IGNORECASE)
    return m.group(1).lower() if m else ""


def from_taxonomy_html(html_path, technique_code, metric_code, branch_name, branch_type, version,
                       commit_sha="", run_id=""):
    """Normalize taxonomy gate HTML into the standard report schema."""
    from lib.registry import metric_entry

    path = Path(html_path)
    html = path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""
    _, metric = metric_entry(technique_code, metric_code)
    cls = metric.get("taxonomy_classification", "")
    raw = _taxonomy_result_for_class(html, cls)
    if not raw:
        status = "SKIPPED"
    elif raw == "fail":
        status = "FAIL"
    elif raw == "warn":
        status = "WARN"
    else:
        status = "PASS"
    tools = (metric.get("tools") or {}).get("python", {})
    return make_report(
        technique_code=technique_code,
        metric_code=metric_code,
        branch_name=branch_name,
        branch_type=branch_type,
        version=version,
        tool_name=tools.get("primary", "taxonomy"),
        source="taxonomy",
        status=status,
        metric_values={"taxonomy_result": raw} if raw else {},
        raw_summary="taxonomy %s=%s" % (cls, raw or "missing"),
        commit_sha=commit_sha,
        run_id=run_id,
        extra={"taxonomy_classification": cls, "html_path": str(path)},
    )


def _find_s3_report_path_one(download_root, branch, commit_sha, run_id):
    """Locate downloaded S3 bundle directory for one branch name variant."""
    root = Path(download_root)
    if not root.is_dir():
        return None
    if commit_sha and run_id:
        for cell_dir in root.iterdir():
            if not cell_dir.is_dir():
                continue
            for plat_dir in cell_dir.iterdir():
                candidate = plat_dir / branch / commit_sha / run_id
                if candidate.is_dir() and any(candidate.iterdir()):
                    return str(candidate)
    for cell_dir in root.iterdir():
        if not cell_dir.is_dir():
            continue
        branch_dir = None
        for plat_dir in cell_dir.iterdir():
            cand = plat_dir / branch
            if cand.is_dir():
                branch_dir = cand
                break
        if not branch_dir:
            continue
        for commit_dir in sorted(branch_dir.iterdir(), reverse=True):
            if not commit_dir.is_dir():
                continue
            for run_dir in sorted(commit_dir.iterdir(), reverse=True):
                if run_dir.is_dir() and any(run_dir.iterdir()):
                    return str(run_dir)
    return None


def find_s3_report_path(download_root, branch, commit_sha, run_id):
    """Locate downloaded S3 bundle directory for a run (tries v2 and legacy v1 names)."""
    from lib.metrics import branch_name_aliases

    for alias in branch_name_aliases(branch):
        found = _find_s3_report_path_one(download_root, alias, commit_sha, run_id)
        if found:
            return found
    return None
