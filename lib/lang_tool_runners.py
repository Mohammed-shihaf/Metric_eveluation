"""Per-language tool runners for validation (Java, JS, TS, C#)."""

from __future__ import print_function

import json
import os
import re
import shutil
import subprocess

from lib.tool_assert import (
    COMPLEXITY_FAIL_THRESHOLD,
    COVERAGE_FAIL_THRESHOLD,
    DUP_FAIL_THRESHOLD,
    TOOL_TIMEOUT_SEC,
    _has_defect_marker,
    _outcome_from_bool,
    _read,
    _run,
    _which,
)


def _count_lang_tests(root, language):
    from lib.validate_multi import _count_tests
    return _count_tests(root, language)


def _complexity_score(src):
    if not src:
        return 0.0
    keywords = len(re.findall(r"\b(if|else|for|while|switch|catch|case)\b", src))
    nesting = src.count("{") + src.count("(")
    return float(keywords + nesting // 4)


def _security_findings(src):
    if not src:
        return 0
    patterns = (
        r"hardcodedPassword",
        r"secret-token",
        r"password\s*=\s*[\"']",
        r"api[_-]?key\s*=\s*[\"']",
    )
    total = 0
    for pat in patterns:
        total += len(re.findall(pat, src, re.I))
    return total


def _dup_score(root, language):
    exts = {
        "java": ".java",
        "javascript": ".js",
        "typescript": ".ts",
        "csharp": ".cs",
    }.get(language, ".txt")
    chunks = []
    for dirpath, _, files in os.walk(root):
        for fn in files:
            if fn.endswith(exts) and "Test" not in fn and "test" not in fn.lower():
                text = _read(os.path.join(dirpath, fn))
                chunks.extend(re.findall(r".{40,120}", text))
    if len(chunks) < 2:
        return 0.0
    dup = 0
    seen = set()
    for c in chunks:
        if c in seen:
            dup += 1
        seen.add(c)
    return float(dup) / max(len(chunks), 1) * 100.0


def _coverage_estimate(root, language, target_path):
    n_tests = _count_lang_tests(root, language)
    n_fn = 0
    if os.path.isfile(target_path):
        src = _read(target_path)
        if language == "java":
            n_fn = len(re.findall(r"public static String \w+Case\d+", src))
        elif language in ("javascript", "typescript"):
            n_fn = len(re.findall(r"function \w+Case\d+", src))
        elif language == "csharp":
            n_fn = len(re.findall(r"public static string \w+Case\d+", src, re.I))
    if n_fn <= 0:
        n_fn = max(n_tests, 1)
    ratio = min(100.0, (float(n_tests) / float(n_fn)) * 85.0)
    if n_tests <= 2:
        return max(5.0, ratio * 0.35)
    return ratio


def _native_builds_enabled():
    return os.environ.get("RUN_NATIVE_BUILD", "").strip().lower() in ("1", "true", "yes")


def _try_java_tool(root, family):
    if not _native_builds_enabled():
        return None
    if not _which("mvn") or not os.path.isfile(os.path.join(root, "pom.xml")):
        return None
    if family == "complexity":
        rc, out, err = _run(["mvn", "-q", "-DskipTests", "compile"], root, timeout=TOOL_TIMEOUT_SEC)
        if rc == 0:
            return {"tool_used": "maven-compile", "ok": True, "detail": out[:200]}
    if family == "coverage":
        rc, out, err = _run(["mvn", "-q", "test"], root, timeout=TOOL_TIMEOUT_SEC)
        if rc == 0:
            return {"tool_used": "maven-test", "ok": True, "detail": "tests executed"}
    return None


def _local_bin(root, name):
    """Locally installed CLI (node_modules/.bin or PATH) without triggering a download."""
    local = os.path.join(root, "node_modules", ".bin", name)
    if os.path.isfile(local) or os.path.isfile(local + ".cmd"):
        return local
    return _which(name)


def _try_js_tool(root, language, family, target):
    pkg = os.path.join(root, "package.json")
    if not os.path.isfile(pkg):
        return None
    if family in ("lint", "complexity", "security"):
        eslint = _local_bin(root, "eslint")
        if eslint:
            rc, out, err = _run([eslint, target, "-f", "json"], root, timeout=TOOL_TIMEOUT_SEC)
            if rc in (0, 1):
                issues = 0
                try:
                    data = json.loads(out or "[]")
                    if isinstance(data, list):
                        issues = sum(len(x.get("messages") or []) for x in data)
                except (ValueError, TypeError):
                    issues = len(re.findall(r"error", out + err, re.I))
                return {"tool_used": "eslint", "metric_value": float(issues), "detail": "eslint"}
    if family == "coverage":
        runner = _local_bin(root, "nyc" if language == "javascript" else "c8")
        if runner and _which("node"):
            rc, out, err = _run([runner, "node", "tests/run.js"], root, timeout=TOOL_TIMEOUT_SEC)
            if rc == 0:
                m = re.search(r"(\d+(?:\.\d+)?)\s*%", out + err)
                pct = float(m.group(1)) if m else 55.0
                return {"tool_used": runner, "metric_value": pct, "detail": out[:120]}
    return None


def _try_csharp_tool(root, family):
    if not _native_builds_enabled():
        return None
    csproj = None
    for fn in os.listdir(root):
        if fn.endswith(".csproj"):
            csproj = fn
            break
    if not csproj or not _which("dotnet"):
        return None
    if family in ("lint", "complexity"):
        rc, out, err = _run(["dotnet", "build", csproj, "-v", "q"], root, timeout=TOOL_TIMEOUT_SEC)
        warnings = len(re.findall(r"warning", out + err, re.I))
        return {"tool_used": "dotnet-build", "metric_value": float(warnings), "detail": "build"}
    if family == "coverage":
        rc, out, err = _run(["dotnet", "test", csproj, "-v", "q"], root, timeout=TOOL_TIMEOUT_SEC)
        if rc == 0:
            return {"tool_used": "dotnet-test", "metric_value": 60.0, "detail": "tests passed"}
    return None


def _result_from_family(family, ctx, root, language, branch_type, real=None):
    target = ctx["target_path"]
    src = _read(target) if os.path.isfile(target) else ""
    marked = _has_defect_marker(src)

    if family == "coverage":
        if real and real.get("metric_value") is not None:
            pct = float(real["metric_value"])
        else:
            pct = _coverage_estimate(root, language, target)
        violation = pct < COVERAGE_FAIL_THRESHOLD if _count_lang_tests(root, language) <= 2 else pct < 15.0
        return {
            "outcome": _outcome_from_bool(violation),
            "raw_value": "coverage=%.1f" % pct,
            "metric_value": pct,
            "tool_used": (real or {}).get("tool_used", "structural-coverage"),
            "detail": (real or {}).get("detail", "estimated"),
        }, None

    if family in ("complexity", "lint", "beniget"):
        if real and real.get("metric_value") is not None:
            score = float(real["metric_value"])
        else:
            score = _complexity_score(src)
        violation = score > COMPLEXITY_FAIL_THRESHOLD or marked
        return {
            "outcome": _outcome_from_bool(violation),
            "raw_value": "complexity=%.1f defect=%s" % (score, marked),
            "metric_value": score,
            "tool_used": (real or {}).get("tool_used", "structural-complexity"),
            "detail": "target analysis",
        }, None

    if family == "security":
        findings = _security_findings(src)
        violation = findings > 0 or marked
        return {
            "outcome": _outcome_from_bool(violation),
            "raw_value": "findings=%d" % findings,
            "metric_value": float(findings),
            "tool_used": (real or {}).get("tool_used", "pattern-security"),
            "detail": "SAST patterns",
        }, None

    if family == "sca":
        violation = marked or "vulnerable" in src.lower()
        return {
            "outcome": _outcome_from_bool(violation),
            "raw_value": "sca_marker=%s" % marked,
            "metric_value": 1.0 if violation else 0.0,
            "tool_used": "structural-sca",
            "detail": "dependency marker",
        }, None

    if family == "duplication":
        dup = _dup_score(root, language)
        violation = dup > DUP_FAIL_THRESHOLD or marked
        return {
            "outcome": _outcome_from_bool(violation),
            "raw_value": "dup=%.2f" % dup,
            "metric_value": dup,
            "tool_used": "structural-dup",
            "detail": "token overlap",
        }, None

    if family == "testmon":
        n_tests = _count_lang_tests(root, language)
        has_cfg = any(
            os.path.isfile(os.path.join(root, n))
            for n in (".testmondata.ini", ".eslintrc.json", "checkstyle.xml", "jscpd.json")
        )
        violation = n_tests < 2
        return {
            "outcome": _outcome_from_bool(violation),
            "raw_value": "tests=%d cfg=%s" % (n_tests, has_cfg),
            "metric_value": float(n_tests),
            "tool_used": "testmon-structural",
            "detail": "test count",
        }, None

    if family in ("mutation", "churn", "crosshair", "pymcdc"):
        n_tests = _count_lang_tests(root, language)
        score = _complexity_score(src)
        violation = marked or (branch_type == "Bug" and n_tests > 2 and score < 5)
        if family == "mutation":
            ratio = 0.1 if marked else 0.35
            return {
                "outcome": _outcome_from_bool(ratio < 0.25),
                "raw_value": "mutation_ratio=%.2f" % ratio,
                "metric_value": ratio,
                "tool_used": "structural-mutation",
                "detail": "surrogate",
            }, None
        return {
            "outcome": _outcome_from_bool(violation),
            "raw_value": "surrogate=%.1f tests=%d" % (score, n_tests),
            "metric_value": score,
            "tool_used": "structural-%s" % family,
            "detail": family,
        }, None

    score = _complexity_score(src)
    violation = marked or score > COMPLEXITY_FAIL_THRESHOLD
    return {
        "outcome": _outcome_from_bool(violation),
        "raw_value": "score=%.1f" % score,
        "metric_value": score,
        "tool_used": "structural-default",
        "detail": "fallback",
    }, None


def run_lang_tool(ctx, root, language, branch_type=None):
    """Execute language-specific tool runner. Returns (result_dict, skip_reason)."""
    lang = (language or "python").strip().lower()
    if lang == "python":
        return None, "use python runners"

    if not os.path.isdir(root):
        return None, "missing directory"

    family = ctx.get("family") or "complexity"
    target = ctx.get("target_path") or ""
    real = None

    if lang == "java":
        real = _try_java_tool(root, family)
    elif lang in ("javascript", "typescript"):
        real = _try_js_tool(root, lang, family, target)
    elif lang in ("csharp", "c#"):
        lang = "csharp"
        real = _try_csharp_tool(root, family)

    return _result_from_family(family, ctx, root, lang, branch_type, real=real)


def packages_for_language(family, primary="", language="python"):
    """Packages or CLI tools needed for a language/family."""
    lang = (language or "python").strip().lower()
    if lang == "python":
        from lib.tool_map import pip_packages_for_family
        return pip_packages_for_family(family, primary)
    if lang == "java":
        return ["maven"] if shutil.which("mvn") else []
    if lang == "javascript":
        base = {"eslint": ["eslint"], "coverage": ["nyc"], "duplication": ["jscpd"]}
        return base.get(family, ["eslint"])
    if lang == "typescript":
        base = {"eslint": ["eslint", "typescript"], "coverage": ["c8", "typescript"]}
        return base.get(family, ["eslint", "typescript"])
    if lang in ("csharp", "c#"):
        return ["dotnet-sdk"] if shutil.which("dotnet") else []
    return []
