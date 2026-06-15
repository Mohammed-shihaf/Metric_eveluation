"""Python tool resolution from metrics registry (White Box sheet)."""

from __future__ import print_function

from lib.registry import metric_entry
from lib.tool_assert import tool_family


def python_tool(technique_code, metric_code, registry=None):
    """Return tool metadata for a metric's Python primary/secondary tools."""
    tech, metric = metric_entry(technique_code, metric_code, registry)
    tools = (metric.get("tools") or {}).get("python", {})
    primary = (tools.get("primary") or "").strip()
    secondary = (tools.get("secondary") or "").strip()
    family = tool_family(primary, tech["technique_code"])
    return {
        "technique_code": tech["technique_code"],
        "metric_code": metric["metric_code"],
        "module_key": metric["module_key"],
        "branch_slug": metric.get("branch_slug", ""),
        "l5_metric": metric["l5_metric"],
        "primary": primary,
        "secondary": secondary,
        "family": family,
        "emitted_directly": bool(metric.get("emitted_directly")),
        "derivation": metric.get("derivation", ""),
        "raw_formula": metric.get("raw_formula", ""),
        "expected_threshold": metric.get("expected_threshold", ""),
        "normalisation": metric.get("normalisation", ""),
    }


def pip_packages_for_family(family, primary=""):
    """Best-practice pip packages to run a tool family locally."""
    base = {
        "coverage": ["coverage", "pytest"],
        "crosshair": ["crosshair-tool", "coverage", "pytest"],
        "pymcdc": ["coverage", "pytest"],
        "complexity": ["radon", "lizard"],
        "lint": ["pylint", "flake8"],
        "security": ["bandit", "semgrep"],
        "sca": ["pip-audit"],
        "mutation": ["mutmut"],
        "churn": ["pydriller"],
        "duplication": ["copydetect"],
        "testmon": ["pytest", "pytest-testmon"],
        "beniget": ["beniget", "pyflakes"],
    }
    pkgs = list(base.get(family, ["pytest"]))
    p = primary.lower()
    if "cognitive" in p and "radon" not in pkgs:
        pkgs.append("radon")
    if "beniget" in p:
        pkgs.extend(["beniget", "pyflakes"])
    return list(dict.fromkeys(pkgs))
