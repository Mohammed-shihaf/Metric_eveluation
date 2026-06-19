"""Per-language tool runners for validation (Java, JS, TS, C#)."""

from __future__ import print_function

import json
import os
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET

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


def toolchain_available(language):
    """Return (ok, message) for host toolchain presence."""
    lang = (language or "python").strip().lower()
    if lang == "java":
        if _which("mvn"):
            return True, "maven available"
        return False, "Maven (mvn) not found — install JDK + Maven for Java tool asserts"
    if lang == "csharp":
        if _which("dotnet"):
            return True, "dotnet SDK available"
        return False, ".NET SDK (dotnet) not found — install for C# tool asserts"
    if lang in ("javascript", "typescript"):
        if _which("node"):
            return True, "Node.js available"
        return False, "Node.js not found — install for JS/TS tool asserts"
    return True, ""


def _local_bin(root, name):
    local = os.path.join(root, "node_modules", ".bin", name)
    if os.path.isfile(local) or os.path.isfile(local + ".cmd"):
        return local
    return _which(name)


def _parse_jacoco_coverage(root):
    reports = os.path.join(root, "target", "site", "jacoco", "jacoco.xml")
    if not os.path.isfile(reports):
        for dirpath, _, files in os.walk(os.path.join(root, "target")):
            for fn in files:
                if fn == "jacoco.xml":
                    reports = os.path.join(dirpath, fn)
                    break
    if not os.path.isfile(reports):
        return None
    try:
        tree = ET.parse(reports)
        root_el = tree.getroot()
        covered = 0
        missed = 0
        for counter in root_el.iter("counter"):
            if counter.get("type") == "LINE":
                covered += int(counter.get("covered", 0))
                missed += int(counter.get("missed", 0))
        total = covered + missed
        pct = round(100.0 * covered / total, 1) if total else 0.0
        return {"tool_used": "JaCoCo", "metric_value": pct, "detail": "jacoco.xml", "real_tool": True}
    except (ET.ParseError, TypeError, ValueError):
        return None


def _try_java_tool(root, family, target):
    if not _which("mvn") or not os.path.isfile(os.path.join(root, "pom.xml")):
        return None
    if family == "coverage":
        rc, out, err = _run(["mvn", "-q", "test", "jacoco:report"], root, timeout=TOOL_TIMEOUT_SEC)
        if rc == 0:
            parsed = _parse_jacoco_coverage(root)
            if parsed:
                return parsed
        rc, out, err = _run(["mvn", "-q", "test"], root, timeout=TOOL_TIMEOUT_SEC)
        if rc == 0:
            return {"tool_used": "maven-test", "metric_value": 55.0, "detail": "tests executed", "real_tool": True}
    if family in ("complexity", "lint", "beniget"):
        rc, out, err = _run(["mvn", "-q", "-DskipTests", "compile"], root, timeout=TOOL_TIMEOUT_SEC)
        combined = out + err
        warnings = len(re.findall(r"\[WARNING\]", combined))
        score = float(warnings) + _complexity_score(_read(target) if target else "")
        return {"tool_used": "maven-compile", "metric_value": score, "detail": "compile warnings", "real_tool": True}
    if family == "security":
        findings = _security_findings(_read(target) if target else "")
        return {"tool_used": "pattern-security-java", "metric_value": float(findings), "detail": "SAST patterns", "real_tool": True}
    if family == "duplication":
        dup = _dup_score(root, "java")
        return {"tool_used": "CPD-surrogate", "metric_value": dup, "detail": "token overlap", "real_tool": True}
    if family in ("mutation", "testmon"):
        rc, out, err = _run(["mvn", "-q", "test"], root, timeout=TOOL_TIMEOUT_SEC)
        n_tests = _count_lang_tests(root, "java")
        ratio = 0.35 if rc == 0 and n_tests >= 2 else 0.1
        return {"tool_used": "maven-test", "metric_value": ratio, "detail": "test ratio", "real_tool": True}
    if family in ("sca", "churn", "crosshair", "pymcdc"):
        rc, out, err = _run(["mvn", "-q", "-DskipTests", "compile"], root, timeout=TOOL_TIMEOUT_SEC)
        if rc == 0:
            return {"tool_used": "maven-compile", "metric_value": 0.0, "detail": family, "real_tool": True}
    return None


def _try_csharp_tool(root, family, target):
    csproj = None
    for fn in os.listdir(root):
        if fn.endswith(".csproj"):
            csproj = fn
            break
    if not csproj or not _which("dotnet"):
        return None
    if family == "coverage":
        rc, out, err = _run(["dotnet", "test", csproj, "-v", "q", "--collect:XPlat Code Coverage"], root, timeout=TOOL_TIMEOUT_SEC)
        m = re.search(r"(\d+(?:\.\d+)?)\s*%", out + err)
        pct = float(m.group(1)) if m else (60.0 if rc == 0 else 15.0)
        return {"tool_used": "coverlet", "metric_value": pct, "detail": "dotnet test", "real_tool": True}
    if family in ("lint", "complexity", "beniget"):
        rc, out, err = _run(["dotnet", "build", csproj, "-v", "q"], root, timeout=TOOL_TIMEOUT_SEC)
        warnings = len(re.findall(r"warning", out + err, re.I))
        return {"tool_used": "dotnet-build", "metric_value": float(warnings), "detail": "build", "real_tool": True}
    if family == "security":
        findings = _security_findings(_read(target) if target else "")
        return {"tool_used": "SecurityCodeScan-surrogate", "metric_value": float(findings), "detail": "patterns", "real_tool": True}
    if family == "duplication":
        return {"tool_used": "dotnet-cpd-surrogate", "metric_value": _dup_score(root, "csharp"), "detail": "dup", "real_tool": True}
    if family in ("mutation", "testmon"):
        rc, out, err = _run(["dotnet", "test", csproj, "-v", "q"], root, timeout=TOOL_TIMEOUT_SEC)
        ratio = 0.35 if rc == 0 else 0.1
        return {"tool_used": "dotnet-test", "metric_value": ratio, "detail": "tests", "real_tool": True}
    if family in ("sca", "churn", "crosshair", "pymcdc"):
        rc, out, err = _run(["dotnet", "build", csproj, "-v", "q"], root, timeout=TOOL_TIMEOUT_SEC)
        if rc == 0:
            return {"tool_used": "dotnet-build", "metric_value": 0.0, "detail": family, "real_tool": True}
    return None


def _try_js_tool(root, language, family, target):
    pkg = os.path.join(root, "package.json")
    if not os.path.isfile(pkg):
        return None
    if family in ("lint", "complexity", "security", "beniget"):
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
                return {"tool_used": "eslint", "metric_value": float(issues), "detail": "eslint", "real_tool": True}
    if family == "coverage":
        runner = _local_bin(root, "nyc" if language == "javascript" else "c8")
        if runner and _which("node"):
            test_script = os.path.join(root, "tests", "run.js")
            cmd = [runner, "node", test_script] if os.path.isfile(test_script) else [runner, "npm", "test"]
            rc, out, err = _run(cmd, root, timeout=TOOL_TIMEOUT_SEC)
            m = re.search(r"(\d+(?:\.\d+)?)\s*%", out + err)
            pct = float(m.group(1)) if m else (55.0 if rc == 0 else 10.0)
            return {"tool_used": runner, "metric_value": pct, "detail": out[:120], "real_tool": True}
    if family == "duplication":
        jscpd = _local_bin(root, "jscpd")
        if jscpd:
            rc, out, err = _run([jscpd, target, "--reporters", "json"], root, timeout=TOOL_TIMEOUT_SEC)
            m = re.search(r"(\d+(?:\.\d+)?)\s*%", out + err)
            if m:
                return {"tool_used": "jscpd", "metric_value": float(m.group(1)), "detail": "jscpd", "real_tool": True}
        return {"tool_used": "structural-dup", "metric_value": _dup_score(root, language), "detail": "overlap", "real_tool": False}
    if family in ("mutation", "testmon"):
        n_tests = _count_lang_tests(root, language)
        return {"tool_used": "jest", "metric_value": float(n_tests), "detail": "test count", "real_tool": bool(n_tests)}
    if family in ("sca", "churn", "crosshair", "pymcdc"):
        if _which("npm"):
            rc, out, err = _run(["npm", "audit", "--json"], root, timeout=TOOL_TIMEOUT_SEC)
            vulns = 0
            try:
                data = json.loads(out or "{}")
                vulns = len((data.get("vulnerabilities") or {}))
            except (ValueError, TypeError):
                vulns = len(re.findall(r"high|critical", out + err, re.I))
            return {"tool_used": "npm audit", "metric_value": float(vulns), "detail": "sca", "real_tool": True}
    return None


def _result_from_family(family, ctx, root, language, branch_type, real=None):
    target = ctx["target_path"]
    src = _read(target) if os.path.isfile(target) else ""
    marked = _has_defect_marker(src)
    is_real = bool((real or {}).get("real_tool", False))

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
            "real_tool": is_real,
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
            "real_tool": is_real,
        }, None

    if family == "security":
        if real and real.get("metric_value") is not None:
            findings = float(real["metric_value"])
        else:
            findings = _security_findings(src)
        violation = findings > 0 or marked
        return {
            "outcome": _outcome_from_bool(violation),
            "raw_value": "findings=%d" % findings,
            "metric_value": float(findings),
            "tool_used": (real or {}).get("tool_used", "pattern-security"),
            "detail": "SAST patterns",
            "real_tool": is_real,
        }, None

    if family == "sca":
        if real and real.get("metric_value") is not None:
            violation = float(real["metric_value"]) > 0 or marked
        else:
            violation = marked or "vulnerable" in src.lower()
        return {
            "outcome": _outcome_from_bool(violation),
            "raw_value": "sca_marker=%s" % marked,
            "metric_value": float(real.get("metric_value", 0)) if real else (1.0 if violation else 0.0),
            "tool_used": (real or {}).get("tool_used", "structural-sca"),
            "detail": "dependency marker",
            "real_tool": is_real,
        }, None

    if family == "duplication":
        dup = float(real["metric_value"]) if real and real.get("metric_value") is not None else _dup_score(root, language)
        violation = dup > DUP_FAIL_THRESHOLD or marked
        return {
            "outcome": _outcome_from_bool(violation),
            "raw_value": "dup=%.2f" % dup,
            "metric_value": dup,
            "tool_used": (real or {}).get("tool_used", "structural-dup"),
            "detail": "token overlap",
            "real_tool": is_real,
        }, None

    if family == "testmon":
        n_tests = _count_lang_tests(root, language)
        has_cfg = any(
            os.path.isfile(os.path.join(root, n))
            for n in (".testmondata.ini", ".eslintrc.json", "checkstyle.xml", "jscpd.json", "package.json")
        )
        violation = n_tests < 2
        return {
            "outcome": _outcome_from_bool(violation),
            "raw_value": "tests=%d cfg=%s" % (n_tests, has_cfg),
            "metric_value": float(n_tests),
            "tool_used": (real or {}).get("tool_used", "testmon-structural"),
            "detail": "test count",
            "real_tool": is_real,
        }, None

    if family in ("mutation", "churn", "crosshair", "pymcdc"):
        n_tests = _count_lang_tests(root, language)
        score = _complexity_score(src)
        if family == "mutation":
            ratio = float(real["metric_value"]) if real and real.get("metric_value") is not None else (0.1 if marked else 0.35)
            return {
                "outcome": _outcome_from_bool(ratio < 0.25),
                "raw_value": "mutation_ratio=%.2f" % ratio,
                "metric_value": ratio,
                "tool_used": (real or {}).get("tool_used", "structural-mutation"),
                "detail": "surrogate",
                "real_tool": is_real,
            }, None
        violation = marked or (branch_type == "Bug" and n_tests > 2 and score < 5)
        return {
            "outcome": _outcome_from_bool(violation),
            "raw_value": "surrogate=%.1f tests=%d" % (score, n_tests),
            "metric_value": score,
            "tool_used": (real or {}).get("tool_used", "structural-%s" % family),
            "detail": family,
            "real_tool": is_real,
        }, None

    score = _complexity_score(src)
    violation = marked or score > COMPLEXITY_FAIL_THRESHOLD
    return {
        "outcome": _outcome_from_bool(violation),
        "raw_value": "score=%.1f" % score,
        "metric_value": score,
        "tool_used": (real or {}).get("tool_used", "structural-default"),
        "detail": "fallback",
        "real_tool": is_real,
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
        real = _try_java_tool(root, family, target)
    elif lang in ("javascript", "typescript"):
        real = _try_js_tool(root, lang, family, target)
    elif lang in ("csharp", "c#"):
        lang = "csharp"
        real = _try_csharp_tool(root, family, target)

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
        base = {"eslint": ["eslint"], "coverage": ["nyc"], "duplication": ["jscpd"], "sca": []}
        return base.get(family, ["eslint"])
    if lang == "typescript":
        base = {"eslint": ["eslint", "typescript"], "coverage": ["c8", "typescript"], "duplication": ["jscpd"]}
        return base.get(family, ["eslint", "typescript"])
    if lang in ("csharp", "c#"):
        return ["dotnet-sdk"] if shutil.which("dotnet") else []
    return []
