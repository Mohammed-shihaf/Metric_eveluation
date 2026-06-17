"""Per-language tool resolution from registry + ecosystem defaults."""

from __future__ import print_function

from lib.registry import metric_entry
from lib.tool_assert import tool_family

SUPPORTED_UI_LANGUAGES = ("python", "java", "javascript", "typescript", "csharp")

# Primary tool when registry has no explicit entry for a language/family.
LANGUAGE_FAMILY_PRIMARY = {
    "python": {
        "coverage": "Coverage.py",
        "crosshair": "Crosshair",
        "pymcdc": "Pymcdc",
        "complexity": "Radon/Lizard",
        "lint": "flake8",
        "security": "bandit",
        "sca": "pip-audit",
        "mutation": "mutmut",
        "churn": "pydriller",
        "duplication": "jscpd",
        "testmon": "testmon",
        "beniget": "beniget",
    },
    "java": {
        "coverage": "JaCoCo",
        "complexity": "PMD",
        "lint": "Checkstyle",
        "security": "SpotBugs",
        "sca": "OWASP Dependency-Check",
        "mutation": "PIT",
        "churn": "git-churn",
        "duplication": "CPD",
        "testmon": "JUnit",
        "crosshair": "Crosshair",
        "pymcdc": "JaCoCo",
        "beniget": "SpotBugs",
    },
    "javascript": {
        "coverage": "nyc",
        "complexity": "eslint",
        "lint": "eslint",
        "security": "eslint",
        "sca": "npm audit",
        "mutation": "Stryker",
        "churn": "git-churn",
        "duplication": "jscpd",
        "testmon": "jest",
        "crosshair": "jest",
        "pymcdc": "nyc",
        "beniget": "eslint",
    },
    "typescript": {
        "coverage": "c8",
        "complexity": "eslint",
        "lint": "eslint",
        "security": "eslint",
        "sca": "npm audit",
        "mutation": "Stryker",
        "churn": "git-churn",
        "duplication": "jscpd",
        "testmon": "jest",
        "crosshair": "jest",
        "pymcdc": "c8",
        "beniget": "eslint",
    },
    "csharp": {
        "coverage": "coverlet",
        "complexity": "dotnet-format",
        "lint": "dotnet-format",
        "security": "SecurityCodeScan",
        "sca": "dotnet list package --vulnerable",
        "mutation": "Stryker.NET",
        "churn": "git-churn",
        "duplication": "dotnet-cpd",
        "testmon": "xUnit",
        "crosshair": "xUnit",
        "pymcdc": "coverlet",
        "beniget": "dotnet-format",
    },
}


def get_metric_tools(technique_code, metric_code, language="python", registry=None):
    """Resolve primary/secondary tools for a metric in the requested language.

    The canonical tool *family* is always derived from the Python primary (the
    family is identical across ecosystems); only the concrete tool *name* is
    swapped for the language's equivalent. This keeps validation runners and
    scoring keyed off a recognized family even though e.g. "JaCoCo" or "nyc"
    would not be classified by tool_family() directly.
    """
    lang = (language or "python").strip().lower()
    tech, metric = metric_entry(technique_code, metric_code, registry)
    tools_block = metric.get("tools") or {}
    lang_tools = tools_block.get(lang) or {}
    py_tools = tools_block.get("python") or {}
    py_primary = (py_tools.get("primary") or "").strip()

    # Family is canonical: from the Python primary (recognized by tool_family).
    family = tool_family(py_primary, tech["technique_code"]) if py_primary else "unknown"

    primary = (lang_tools.get("primary") or "").strip()
    secondary = (lang_tools.get("secondary") or "").strip()
    if not primary:
        if lang == "python":
            primary = py_primary
        else:
            defaults = LANGUAGE_FAMILY_PRIMARY.get(lang) or LANGUAGE_FAMILY_PRIMARY["python"]
            primary = defaults.get(family, py_primary or defaults.get("complexity", "tool"))
        if not secondary:
            secondary = (py_tools.get("secondary") or "").strip()
    if not primary:
        defaults = LANGUAGE_FAMILY_PRIMARY.get(lang) or LANGUAGE_FAMILY_PRIMARY["python"]
        primary = defaults.get("complexity", "tool")
    if family == "unknown":
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
        "language": lang,
        "emitted_directly": bool(metric.get("emitted_directly")),
        "derivation": metric.get("derivation", ""),
        "raw_formula": metric.get("raw_formula", ""),
        "expected_threshold": metric.get("expected_threshold", ""),
        "normalisation": metric.get("normalisation", ""),
    }


def metric_tool(technique_code, metric_code, language="python", registry=None):
    """Alias used by validation and local runners."""
    return get_metric_tools(technique_code, metric_code, language, registry)
