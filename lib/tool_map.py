"""Python tool resolution from metrics registry (White Box sheet)."""

from __future__ import print_function

import re

from lib.registry import metric_entry
from lib.registry_tools import get_metric_tools
from lib.tool_assert import tool_family


def python_tool(technique_code, metric_code, registry=None):
    """Return tool metadata for a metric's Python primary/secondary tools."""
    return get_metric_tools(technique_code, metric_code, "python", registry)


def metric_tool(technique_code, metric_code, language="python", registry=None):
    """Return tool metadata for a metric in the requested language."""
    return get_metric_tools(technique_code, metric_code, language, registry)


def _normalize_primary_key(primary):
    return re.sub(r"\s+", " ", (primary or "").strip().lower())


# Registry primary tool name -> pip packages (Excel / metrics_registry.yaml).
PRIMARY_PIP_PACKAGES = {
    "coverage.py": ["coverage", "pytest"],
    "pip-audit": ["pip-audit"],
    "radon/lizard": ["radon", "lizard"],
    "cognitive-ast": ["radon"],
    "pylint": ["pylint", "flake8"],
    "semgrep oss + bandit": ["bandit", "semgrep"],
    "cosmic-ray": ["cosmic-ray", "mutmut"],
    "mutmut": ["mutmut"],
    "pydriller": ["pydriller"],
    "crosshair": ["crosshair-tool", "coverage", "pytest"],
    "pymcdc": ["pymcdc", "coverage", "pytest"],
    "testmon": ["pytest", "pytest-testmon"],
    "beniget": ["beniget", "pyflakes"],
    "jscpd": ["copydetect"],
    "coverage.py + beniget": ["coverage", "pytest", "beniget", "pyflakes"],
}


def pip_packages_for_primary(primary, family="", technique_code=""):
    """Resolve pip packages for a registry primary tool name."""
    key = _normalize_primary_key(primary)
    if key in PRIMARY_PIP_PACKAGES:
        return list(PRIMARY_PIP_PACKAGES[key])
    if "+" in key:
        merged = []
        for part in re.split(r"\s*\+\s*", key):
            merged.extend(pip_packages_for_primary(part, family, technique_code))
        return list(dict.fromkeys(merged))
    if "coverage" in key:
        return ["coverage", "pytest"]
    if "bandit" in key or "semgrep" in key:
        return pip_packages_for_primary("semgrep oss + bandit", family, technique_code)
    if "radon" in key or "lizard" in key or "cognitive" in key:
        return pip_packages_for_primary("radon/lizard", family, technique_code)
    if "pip-audit" in key or "safety" in key:
        return ["pip-audit"]
    if "crosshair" in key:
        return pip_packages_for_primary("crosshair", family, technique_code)
    if "cosmic" in key:
        return ["cosmic-ray"]
    if "mutmut" in key:
        return ["mutmut"]
    if "pydriller" in key or "churn" in key:
        return ["pydriller"]
    if "beniget" in key:
        return pip_packages_for_primary("beniget", family, technique_code)
    if "jscpd" in key or "cpd" in key:
        return ["copydetect"]
    if "testmon" in key:
        return pip_packages_for_primary("testmon", family, technique_code)
    if "pymcdc" in key:
        return pip_packages_for_primary("pymcdc", family, technique_code)
    return pip_packages_for_family(family or tool_family(primary, technique_code), primary)


def pip_packages_for_family(family, primary=""):
    """Best-practice pip packages to run a tool family locally."""
    base = {
        "coverage": ["coverage", "pytest"],
        "crosshair": ["crosshair-tool", "coverage", "pytest"],
        "pymcdc": ["pymcdc", "coverage", "pytest"],
        "complexity": ["radon", "lizard"],
        "lint": ["pylint", "flake8"],
        "security": ["bandit", "semgrep"],
        "sca": ["pip-audit"],
        "mutation": ["cosmic-ray", "mutmut"],
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


def all_tool_packages():
    """Union of pip packages required to run every Python tool family."""
    families = [
        "coverage", "crosshair", "pymcdc", "complexity", "lint", "security",
        "sca", "mutation", "churn", "duplication", "testmon", "beniget",
    ]
    packages = []
    for family in families:
        packages.extend(pip_packages_for_family(family))
    for primary_pkgs in PRIMARY_PIP_PACKAGES.values():
        packages.extend(primary_pkgs)
    return list(dict.fromkeys(packages))
