"""Registry-driven strength scoring: real tool measurement vs expected_threshold."""

from __future__ import print_function

import re

from lib.tool_assert import (
    CHURN_FAIL_THRESHOLD,
    COMPLEXITY_FAIL_THRESHOLD,
    COVERAGE_FAIL_THRESHOLD,
    DUP_FAIL_THRESHOLD,
    MUTATION_RATIO_FAIL,
    tool_family,
)

FAMILY_DEFAULTS = {
    "coverage": {"op": ">=", "value": COVERAGE_FAIL_THRESHOLD, "higher_is_better": True},
    "complexity": {"op": "<=", "value": COMPLEXITY_FAIL_THRESHOLD, "higher_is_better": False},
    "security": {"op": "==", "value": 0.0, "higher_is_better": False},
    "sca": {"op": "==", "value": 0.0, "higher_is_better": False},
    "mutation": {"op": ">=", "value": MUTATION_RATIO_FAIL, "higher_is_better": True},
    "churn": {"op": "<=", "value": CHURN_FAIL_THRESHOLD, "higher_is_better": False},
    "duplication": {"op": "<=", "value": DUP_FAIL_THRESHOLD, "higher_is_better": False},
    "lint": {"op": "==", "value": 0.0, "higher_is_better": False},
    "crosshair": {"op": "==", "value": 0.0, "higher_is_better": False},
    "pymcdc": {"op": ">=", "value": COVERAGE_FAIL_THRESHOLD, "higher_is_better": True},
    "testmon": {"op": ">=", "value": 2.0, "higher_is_better": True},
    "beniget": {"op": "==", "value": 0.0, "higher_is_better": False},
}


def _first_number(text):
    if not text:
        return None
    m = re.search(r"(-?\d+(?:\.\d+)?)", str(text).replace(",", ""))
    if not m:
        return None
    return float(m.group(1))


def _registry_threshold_applicable(expected_threshold, family):
    text = (expected_threshold or "").lower()
    if not text.strip():
        return False
    if family == "coverage":
        if any(k in text for k in ("mi", "module", "maintainability", "refactor", "debt")):
            return False
    if family == "complexity":
        if any(k in text for k in ("coverage", "cov ", "mutation", "vuln")):
            return False
    return True


def parse_threshold(expected_threshold, family):
    if not _registry_threshold_applicable(expected_threshold, family):
        expected_threshold = ""
    text = (expected_threshold or "").strip().lower()
    default = FAMILY_DEFAULTS.get(family, {"op": "<=", "value": 10.0, "higher_is_better": False})
    if not text:
        return default["op"], default["value"], default["higher_is_better"]

    num = _first_number(text)
    if num is None:
        return default["op"], default["value"], default["higher_is_better"]

    if "<=" in text or "lower is better" in text or "per function" in text:
        return "<=", num, False
    if ">=" in text or "green zone" in text or "gate at" in text:
        return ">=", num, True
    if "0 " in text or text.startswith("0") or "no " in text or "zero" in text:
        return "==", 0.0, False
    if "<" in text:
        return "<", num, False
    if ">" in text:
        return ">", num, True
    return default["op"], num, default["higher_is_better"]


def _metric_in_violation(family, value, op, gate):
    """True when the measured value indicates a defect for this tool family."""
    if family == "coverage":
        return value < COVERAGE_FAIL_THRESHOLD
    if family == "complexity":
        return value > COMPLEXITY_FAIL_THRESHOLD
    if family in ("security", "sca", "lint", "beniget", "crosshair"):
        return value > gate
    if family in ("churn", "duplication"):
        return value > gate
    if family == "mutation":
        return value < gate
    if family == "testmon":
        return value < gate
    if family == "pymcdc":
        return value < COVERAGE_FAIL_THRESHOLD
    if op in ("<=", "<"):
        return value > gate
    if op in (">=", ">"):
        return value < gate
    return abs(value - gate) > 0.001


def _zone_label(branch_type, in_violation):
    if branch_type == "Bug":
        return "violation" if in_violation else "healthy"
    return "healthy" if not in_violation else "violation"


def score_metric(family, metric_value, registry_metric, branch_type, technique_code=None):
    if metric_value is None:
        return {
            "score": 0.0,
            "passed": False,
            "threshold_used": "",
            "expected_zone": "violation" if branch_type == "Bug" else "healthy",
            "actual_zone": "unknown",
            "reason": "no metric_value measured",
        }

    primary = ""
    if registry_metric:
        primary = ((registry_metric.get("tools") or {}).get("python") or {}).get("primary") or ""
    if not family and primary:
        family = tool_family(primary, technique_code or "")

    expected = (registry_metric or {}).get("expected_threshold", "")
    op, gate, _higher = parse_threshold(expected, family or "unknown")

    if family == "coverage":
        if branch_type == "Bug":
            op, gate = "<", COVERAGE_FAIL_THRESHOLD
        else:
            op, gate = ">=", 5.0
    elif family == "complexity" and not _registry_threshold_applicable(expected, family):
        op, gate = "<=", COMPLEXITY_FAIL_THRESHOLD

    value = float(metric_value)
    in_violation = _metric_in_violation(family or "unknown", value, op, gate)

    if branch_type == "Bug":
        passed = in_violation
        expected_zone = "violation"
    else:
        if family == "coverage":
            passed = value >= 5.0
            in_violation = value < 5.0
        else:
            passed = not in_violation
        expected_zone = "healthy"

    actual_zone = _zone_label(branch_type, in_violation)
    span = max(abs(gate), 1.0)
    margin = abs(value - gate)

    if passed:
        score = max(55.0, min(100.0, 55.0 + (margin / span) * 45.0))
    else:
        score = max(0.0, min(54.0, 54.0 - margin * 4.0))

    threshold_used = "%s %s" % (op, gate)
    if expected and _registry_threshold_applicable(expected, family or ""):
        threshold_used = "%s (registry: %s)" % (threshold_used, expected[:60])

    reason = "value=%.3f -> %s zone (need %s); gate %s" % (
        value, actual_zone, expected_zone, threshold_used.split(" (")[0],
    )

    return {
        "score": round(score, 1),
        "passed": passed,
        "threshold_used": threshold_used,
        "expected_zone": expected_zone,
        "actual_zone": actual_zone,
        "reason": reason,
    }
