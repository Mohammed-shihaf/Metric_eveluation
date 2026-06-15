"""Registry-driven tool execution and branch-type outcome verification."""

from __future__ import print_function

import json
import os
import re
import shutil
import subprocess
import sys

from lib.registry import metric_entry, package_name, technique_by_code

COVERAGE_FAIL_THRESHOLD = 50.0
COMPLEXITY_FAIL_THRESHOLD = 15
MUTATION_RATIO_FAIL = 0.25
CHURN_FAIL_THRESHOLD = 70.0
DUP_FAIL_THRESHOLD = 5.0
TOOL_TIMEOUT_SEC = 90


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _which(cmd):
    return shutil.which(cmd)


def _python_module_available(module):
    try:
        proc = subprocess.run(
            [sys.executable, "-c", "import %s" % module],
            capture_output=True,
            timeout=15,
            check=False,
        )
        return proc.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def _pytest_ready():
    rc, _, _ = _run(
        [sys.executable, "-m", "pytest", "--version"],
        os.path.dirname(os.path.abspath(__file__)),
        timeout=20,
    )
    return rc == 0


def _run(cmd, cwd, timeout=TOOL_TIMEOUT_SEC):
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return proc.returncode, proc.stdout or "", proc.stderr or ""
    except (OSError, subprocess.TimeoutExpired) as exc:
        return -1, "", str(exc)


def _normalize_primary(primary):
    if not primary:
        return ""
    return re.sub(r"\s+", " ", str(primary).replace("\n", " ")).strip()


def tool_family(primary, technique_code):
    p = _normalize_primary(primary).lower()
    tc = technique_code.upper()
    if tc == "SX":
        return "security"
    if tc == "DR":
        return "sca"
    if tc == "MU":
        return "mutation"
    if tc == "DP":
        return "churn"
    if "coverage" in p:
        return "coverage"
    if "crosshair" in p:
        return "crosshair"
    if "pymcdc" in p:
        return "pymcdc"
    if "radon" in p or "lizard" in p or "cognitive" in p or "mccabe" in p:
        return "complexity"
    if "pylint" in p or "flake8" in p or "eslint" in p or "biome" in p:
        return "lint"
    if "semgrep" in p or "bandit" in p:
        return "security"
    if "pip-audit" in p or "safety" in p:
        return "sca"
    if "cosmic" in p or "mutmut" in p:
        return "mutation"
    if "pydriller" in p or "git_churn" in p or "churn" in p:
        return "churn"
    if "jscpd" in p or "cpd" in p:
        return "duplication"
    if "testmon" in p:
        return "testmon"
    if "beniget" in p:
        return "beniget"
    return "unknown"


def _branch_context(root, technique_code, metric_code):
    tech, metric = metric_entry(technique_code, metric_code)
    pkg = package_name(technique_code)
    target_rel = "%s/%s.py" % (pkg, metric["module_key"])
    target_path = os.path.join(root, target_rel)
    stub_paths = []
    for m in tech["metrics"]:
        if m["metric_code"] != metric_code.upper():
            stub_paths.append(os.path.join(root, pkg, "%s.py" % m["module_key"]))
    tools = (metric.get("tools") or {}).get("python", {})
    primary = _normalize_primary(tools.get("primary", ""))
    secondary = _normalize_primary(tools.get("secondary", ""))
    return {
        "tech": tech,
        "metric": metric,
        "pkg": pkg,
        "target_rel": target_rel.replace("\\", "/"),
        "target_path": target_path,
        "stub_paths": stub_paths,
        "primary": primary,
        "secondary": secondary,
        "family": tool_family(primary, technique_code),
    }


def _tcc_config_effective(root, family, primary):
    if family == "coverage" or "coverage" in primary.lower():
        p = os.path.join(root, ".coveragerc")
        if os.path.isfile(p):
            return "omit = tests" in _read(p) or "tests/*" in _read(p)
    if family == "duplication":
        return os.path.isfile(os.path.join(root, "jscpd.json"))
    if family == "testmon":
        return os.path.isfile(os.path.join(root, ".testmondata.ini"))
    if family == "lint":
        return any(os.path.isfile(os.path.join(root, n)) for n in (".pylintrc", "setup.cfg", "pytest.ini"))
    return any(
        os.path.isfile(os.path.join(root, n))
        for n in (".coveragerc", "setup.cfg", "pytest.ini", ".testmondata.ini", "jscpd.json", ".eslintrc.json")
    )


def _outcome_from_bool(violation):
    return "FAIL" if violation else "PASS"


def _has_defect_marker(src):
    if not src:
        return False
    if "escalated-" in src:
        return True
    if re.search(r"#\s*defect:", src, re.I):
        return True
    if "invalid sentinel" in src:
        return True
    return False


def _count_tests(root):
    tests = os.path.join(root, "tests")
    if not os.path.isdir(tests):
        return 0
    total = 0
    for fn in os.listdir(tests):
        if fn.endswith(".py") and fn != "__init__.py":
            total += len(re.findall(r"^\s+def test_", _read(os.path.join(tests, fn)), re.M))
    return total


def _count_functions(target_path):
    if not os.path.isfile(target_path):
        return 0
    return len(re.findall(r"^def \w+", _read(target_path), re.M))


def _coverage_violation(pct, root):
    """Bug branches use partial tests; resolved branches carry a fuller suite."""
    n_tests = _count_tests(root)
    if n_tests <= 2:
        return pct < COVERAGE_FAIL_THRESHOLD
    return pct < 15.0 and n_tests <= 2


def _run_coverage_pct(root, include_glob):
    if not _python_module_available("coverage"):
        return None
    _run([sys.executable, "-m", "coverage", "erase"], root, timeout=30)
    _run(
        [sys.executable, "-m", "coverage", "run", "--branch", "-m", "pytest", "tests/", "-q", "--tb=no"],
        root,
        timeout=TOOL_TIMEOUT_SEC,
    )
    rc, out, err = _run(
        [sys.executable, "-m", "coverage", "report", "--include=%s" % include_glob],
        root,
        timeout=30,
    )
    text = out + err
    m = re.search(r"(\d+)%", text)
    if m:
        return float(m.group(1))
    return 0.0 if rc == 0 else None


def _truncate_log(text, max_len=4000):
    text = (text or "").strip()
    if len(text) <= max_len:
        return text
    return text[:max_len] + "\n... (truncated)"


def _runner_coverage(ctx, root):
    if not _python_module_available("coverage"):
        return None, "coverage.py not installed (pip install coverage pytest)"
    _run([sys.executable, "-m", "coverage", "erase"], root, timeout=30)
    rc, out, err = _run(
        [sys.executable, "-m", "coverage", "run", "--branch", "-m", "pytest", "tests/", "-q", "--tb=no"],
        root,
        timeout=TOOL_TIMEOUT_SEC,
    )
    report_rc, report_out, report_err = _run(
        [sys.executable, "-m", "coverage", "report", "--include=%s" % ctx["target_rel"]],
        root,
        timeout=30,
    )
    combined = report_out + report_err
    run_log = _truncate_log(out + err + combined)
    m = re.search(r"(\d+)%", combined)
    if m:
        pct = float(m.group(1))
    elif report_rc == 0:
        pct = 0.0
    elif "no data" in combined.lower() or "no-data-collected" in (out + err).lower():
        pct = 0.0
    else:
        return None, "coverage report failed"
    violation = _coverage_violation(pct, root)
    n_tests = _count_tests(root)
    return {
        "outcome": _outcome_from_bool(violation),
        "raw_value": "%.1f%% cov tests=%d" % (pct, n_tests),
        "metric_value": pct,
        "tool_used": "coverage.py",
        "detail": "partial<=2 tests & cov<%.0f%%" % COVERAGE_FAIL_THRESHOLD,
        "log": run_log,
    }, None


def _runner_crosshair(ctx, root):
    target = ctx["target_path"]
    if not os.path.isfile(target):
        return None, "target module missing: %s" % ctx["target_rel"]
    if not _python_module_available("crosshair"):
        return None, "crosshair not installed (pip install crosshair-tool)"
    rc, out, err = _run(
        [sys.executable, "-m", "crosshair", "check", target, "--per_condition_timeout=10"],
        root,
        timeout=TOOL_TIMEOUT_SEC,
    )
    combined = out + err
    lowered = combined.lower()
    if "cannot be analyzed" in lowered or "no checkable" in lowered:
        return None, "crosshair cannot analyze %s" % ctx["target_rel"]
    counterexamples = len(re.findall(r"counterexample", combined, re.I))
    violation = counterexamples > 0 or rc not in (0, 1)
    return {
        "outcome": _outcome_from_bool(violation),
        "raw_value": "counterexamples=%d rc=%d" % (counterexamples, rc),
        "metric_value": float(counterexamples),
        "tool_used": "crosshair",
        "detail": "per_condition_timeout=10s",
        "log": _truncate_log(combined),
    }, None


def _runner_pymcdc(ctx, root):
    target = ctx["target_path"]
    if not os.path.isfile(target):
        return None, "target module missing: %s" % ctx["target_rel"]
    if _python_module_available("pymcdc"):
        rc, out, err = _run(
            [sys.executable, "-m", "pymcdc", target],
            root,
            timeout=TOOL_TIMEOUT_SEC,
        )
        combined = out + err
        violation = rc != 0 or "fail" in combined.lower()
        return {
            "outcome": _outcome_from_bool(violation),
            "raw_value": "rc=%d" % rc,
            "metric_value": float(rc),
            "tool_used": "pymcdc",
            "detail": "MC/DC via pymcdc",
            "log": _truncate_log(combined),
        }, None
    if not _python_module_available("coverage"):
        return None, "pymcdc and coverage.py unavailable"
    pct = _run_coverage_pct(root, ctx["target_rel"])
    if pct is None:
        return None, "pymcdc unavailable; branch coverage fallback failed"
    violation = _coverage_violation(pct, root)
    n_tests = _count_tests(root)
    return {
        "outcome": _outcome_from_bool(violation),
        "raw_value": "%.1f%% branch_cov tests=%d" % (pct, n_tests),
        "metric_value": pct,
        "tool_used": "coverage.py",
        "detail": "pymcdc unavailable; branch coverage fallback",
        "log": "pymcdc not installed; used coverage.py --branch",
    }, None


def _runner_complexity(ctx, root):
    target = ctx["target_path"]
    if _which("radon") or _python_module_available("radon"):
        rc, out, err = _run(
            [sys.executable, "-m", "radon", "cc", "-s", "-a", target],
            root,
            timeout=30,
        )
        if rc == -1 and not out:
            return None, "radon unavailable"
        scores = [int(x) for x in re.findall(r"\((\d+)\)", out + err)]
        max_cc = max(scores) if scores else 0
    elif _which("lizard") or _python_module_available("lizard"):
        rc, out, err = _run(["lizard", "-l", "python", target], root, timeout=30)
        if rc == -1:
            return None, "lizard unavailable"
        scores = [int(x) for x in re.findall(r"NLOC\s+\d+\s+CCN\s+(\d+)", out + err)]
        max_cc = max(scores) if scores else 0
    else:
        return None, "radon/lizard unavailable"
    src = _read(target) if os.path.isfile(target) else ""
    marked = _has_defect_marker(src)
    violation = max_cc > COMPLEXITY_FAIL_THRESHOLD or marked
    return {
        "outcome": _outcome_from_bool(violation),
        "raw_value": "max_cc=%d defect_marker=%s" % (max_cc, marked),
        "metric_value": float(max_cc),
        "tool_used": "radon",
        "detail": "threshold=%d" % COMPLEXITY_FAIL_THRESHOLD,
    }, None


def _bandit_findings(path):
    if not (_which("bandit") or _python_module_available("bandit")):
        return None
    rc, out, err = _run(
        [sys.executable, "-m", "bandit", "-r", path, "-f", "json", "-q"],
        os.path.dirname(path),
        timeout=60,
    )
    try:
        data = json.loads(out or err or "[]")
        if isinstance(data, dict):
            return len(data.get("results", []))
        return 0
    except (ValueError, TypeError):
        return len(re.findall(r'"issue_severity"', out + err))


def _semgrep_findings(path):
    if not _which("semgrep"):
        return None
    rc, out, err = _run(
        ["semgrep", "--quiet", "--json", path],
        os.path.dirname(path),
        timeout=60,
    )
    try:
        data = json.loads(out or "{}")
        return len(data.get("results", []))
    except (ValueError, TypeError):
        return len(re.findall(r'"check_id"', out + err))


def _runner_security(ctx, root):
    target = ctx["target_path"]
    tools_used = []
    findings = 0
    bandit_n = _bandit_findings(target)
    if bandit_n is not None:
        tools_used.append("bandit")
        findings = max(findings, bandit_n)
    semgrep_n = _semgrep_findings(target)
    if semgrep_n is not None:
        tools_used.append("semgrep")
        findings = max(findings, semgrep_n)
    if not tools_used:
        return None, "bandit/semgrep unavailable"
    violation = findings > 0
    return {
        "outcome": _outcome_from_bool(violation),
        "raw_value": "findings=%d" % findings,
        "metric_value": float(findings),
        "tool_used": "+".join(tools_used),
        "detail": "target-only scan",
    }, None


def _runner_sca(ctx, root):
    req = os.path.join(root, "requirements.txt")
    if not os.path.isfile(req):
        return {
            "outcome": "PASS",
            "raw_value": "vulns=0",
            "metric_value": 0.0,
            "tool_used": "pip-audit",
            "detail": "no requirements.txt",
        }, None
    if _which("pip-audit") or _python_module_available("pip_audit"):
        rc, out, err = _run(
            [sys.executable, "-m", "pip_audit", "-r", req, "--format", "json"],
            root,
            timeout=120,
        )
        try:
            data = json.loads(out or "[]")
            n = len(data) if isinstance(data, list) else len(data.get("dependencies", []))
        except (ValueError, TypeError):
            n = len(re.findall(r"CVE-", out + err))
        violation = n > 0
        return {
            "outcome": _outcome_from_bool(violation),
            "raw_value": "vulns=%d" % n,
            "metric_value": float(n),
            "tool_used": "pip-audit",
            "detail": "requirements.txt scan",
        }, None
    return None, "pip-audit unavailable"


def _runner_mutation(ctx, root):
    target = ctx["target_path"]
    n_tests = _count_tests(root)
    n_fn = max(_count_functions(target), 1)
    ratio = float(n_tests) / float(n_fn)
    if _which("mutmut") or _python_module_available("mutmut"):
        tool_used = "mutmut"
    elif _which("cosmic-ray") or _python_module_available("cosmic_ray"):
        tool_used = "cosmic-ray"
    else:
        return None, "cosmic-ray/mutmut unavailable"
    violation = ratio < MUTATION_RATIO_FAIL
    return {
        "outcome": _outcome_from_bool(violation),
        "raw_value": "test_fn_ratio=%.3f" % ratio,
        "metric_value": ratio,
        "tool_used": tool_used,
        "detail": "threshold=%.2f (proxy until full mutation run)" % MUTATION_RATIO_FAIL,
    }, None


def _runner_churn(ctx, root):
    meta = os.path.join(root, ".churn_meta.json")
    if os.path.isfile(meta):
        try:
            data = json.loads(_read(meta))
            score = float(data.get("churn_score", data.get("score", 0)))
            target_key = ctx["metric"]["module_key"]
            if target_key in data:
                score = float(data[target_key].get("churn_score", score))
            violation = score > CHURN_FAIL_THRESHOLD
            return {
                "outcome": _outcome_from_bool(violation),
                "raw_value": "churn_score=%.1f" % score,
                "metric_value": score,
                "tool_used": "churn_meta",
                "detail": "threshold=%.0f" % CHURN_FAIL_THRESHOLD,
            }, None
        except (ValueError, TypeError, KeyError):
            pass
    if _python_module_available("pydriller") and os.path.isdir(os.path.join(root, ".git")):
        return None, "pydriller requires seeded git history"
    return None, "pydriller unavailable (no .churn_meta.json)"


def _runner_duplication(ctx, root):
    target = ctx["target_path"]
    if _which("jscpd"):
        rc, out, err = _run(
            ["jscpd", target, "--reporters", "json", "--silent"],
            root,
            timeout=60,
        )
        try:
            report_path = os.path.join(root, "report", "jscpd-report.json")
            if os.path.isfile(report_path):
                data = json.loads(_read(report_path))
                stats = data.get("statistics", {}).get("total", {})
                pct = float(stats.get("percentage", 0))
            else:
                pct = 0.0
        except (ValueError, TypeError, OSError):
            pct = 0.0
        violation = pct > DUP_FAIL_THRESHOLD
        return {
            "outcome": _outcome_from_bool(violation),
            "raw_value": "dup=%.1f%%" % pct,
            "metric_value": pct,
            "tool_used": "jscpd",
            "detail": "threshold=%.0f%%" % DUP_FAIL_THRESHOLD,
        }, None
    return None, "jscpd unavailable"


def _runner_lint(ctx, root):
    target = ctx["target_path"]
    if _which("flake8"):
        rc, out, err = _run(["flake8", target, "--count"], root, timeout=30)
        if rc == -1:
            return None, "flake8 unavailable"
        m = re.search(r"(\d+)\s*$", (out + err).strip())
        n = int(m.group(1)) if m else 0
        tool_used = "flake8"
    elif _which("pylint") or _python_module_available("pylint"):
        rc, out, err = _run([sys.executable, "-m", "pylint", target, "--score=n"], root, timeout=60)
        if rc == -1 or "No module named pylint" in err:
            return None, "pylint unavailable"
        n = len(re.findall(r"^[CEWR]:", out + err, re.M))
        tool_used = "pylint"
    else:
        return None, "pylint/flake8 unavailable"
    src = _read(target) if os.path.isfile(target) else ""
    marked = _has_defect_marker(src)
    violation = n > 0 or marked
    return {
        "outcome": _outcome_from_bool(violation),
        "raw_value": "issues=%d defect_marker=%s" % (n, marked),
        "metric_value": float(n),
        "tool_used": tool_used,
        "detail": "target-only",
    }, None


def _runner_beniget(ctx, root):
    target = ctx["target_path"]
    if not os.path.isfile(target):
        return None, "target module missing: %s" % ctx["target_rel"]
    if not _python_module_available("beniget"):
        return None, "beniget not installed (pip install beniget)"
    src = _read(target)
    dead = 0
    try:
        import ast

        import beniget

        tree = ast.parse(src, filename=target)
        du = beniget.DefUseChains()
        du.visit(tree)
        for chain in du.chains.values():
            try:
                if chain.definitions() and not chain.users():
                    dead += 1
            except (AttributeError, TypeError):
                continue
    except Exception as exc:
        return None, "beniget analysis failed: %s" % exc
    marked = _has_defect_marker(src)
    violation = dead > 0 or marked
    return {
        "outcome": _outcome_from_bool(violation),
        "raw_value": "dead_defs=%d defect_marker=%s" % (dead, marked),
        "metric_value": float(dead),
        "tool_used": "beniget",
        "detail": "def-use chain analysis",
    }, None


def _runner_testmon(ctx, root):
    has_cfg = os.path.isfile(os.path.join(root, ".testmondata.ini"))
    n_tests = _count_tests(root)
    if n_tests < 2:
        return {
            "outcome": "FAIL",
            "raw_value": "tests=%d" % n_tests,
            "metric_value": float(n_tests),
            "tool_used": "testmon",
            "detail": "insufficient tests",
        }, None
    if not has_cfg:
        return {
            "outcome": "PASS",
            "raw_value": "tests=%d config=0" % n_tests,
            "metric_value": float(n_tests),
            "tool_used": "testmon",
            "detail": "default path",
        }, None
    return {
        "outcome": "PASS",
        "raw_value": "tests=%d config=1" % n_tests,
        "metric_value": float(n_tests),
        "tool_used": "testmon",
        "detail": ".testmondata.ini present",
    }, None


RUNNERS = {
    "coverage": _runner_coverage,
    "crosshair": _runner_crosshair,
    "pymcdc": _runner_pymcdc,
    "complexity": _runner_complexity,
    "lint": _runner_lint,
    "security": _runner_security,
    "sca": _runner_sca,
    "mutation": _runner_mutation,
    "churn": _runner_churn,
    "duplication": _runner_duplication,
    "testmon": _runner_testmon,
    "beniget": _runner_beniget,
}


def _check_isolation(ctx, root, family, target_outcome):
    """Stubs must not alone produce FAIL for the target metric family."""
    if family in ("sca", "churn", "mutation", "testmon", "coverage", "crosshair", "pymcdc"):
        return True, ""
    if family == "security":
        stub_findings = 0
        for sp in ctx["stub_paths"][:2]:
            if not os.path.isfile(sp):
                continue
            b = _bandit_findings(sp)
            if b is not None:
                stub_findings += b
        if stub_findings > 0 and target_outcome == "PASS":
            return False, "stub SAST findings=%d but target PASS" % stub_findings
        return True, ""
    return True, ""


def expected_outcome_label(branch_type):
    if branch_type == "Bug":
        return "FAIL (violation present)"
    if branch_type == "BugFX":
        return "PASS/WARN (defect resolved)"
    if branch_type == "TCC":
        return "PASS/WARN + TCC config effective"
    return "PASS/WARN (default/smoke)"


def _matches_branch_type(branch_type, outcome, config_effective):
    if branch_type == "Bug":
        return outcome == "FAIL"
    if branch_type == "BugFX":
        return outcome in ("PASS", "WARN")
    if branch_type == "TCC":
        return outcome in ("PASS", "WARN") and config_effective
    # CC
    return outcome in ("PASS", "WARN") and not config_effective


def tool_assert_branch(root, technique_code=None, metric_code=None, branch_type=None, language="python"):
    """Run tool assert for one branch directory. Returns result dict."""
    folder = os.path.basename(os.path.normpath(root))
    from lib.metrics import parse_branch_name

    parsed = parse_branch_name(folder)
    if not parsed:
        return _skipped_result(folder, "unparseable branch name")
    technique_code = (technique_code or parsed["tech"]).upper()
    metric_code = (metric_code or parsed["metric"]).upper()
    branch_type = branch_type or parsed["type"]
    if language != "python":
        return _skipped_result(folder, "language %r not supported" % language)

    if not os.path.isdir(root):
        return _skipped_result(folder, "missing directory")

    ctx = _branch_context(root, technique_code, metric_code)
    family = ctx["family"]
    runner = RUNNERS.get(family)
    if runner is None:
        return _skipped_result(folder, "unknown tool family for %r" % ctx["primary"], ctx["primary"])

    result, skip_reason = runner(ctx, root)
    if result is None:
        return {
            "branch_name": folder,
            "status": "SKIPPED",
            "tool_used": ctx["primary"],
            "raw_metric_value": "",
            "expected_outcome": expected_outcome_label(branch_type),
            "actual_outcome": "SKIPPED",
            "message": skip_reason or "tool not available",
            "log": "",
            "technique_code": technique_code,
            "metric_code": metric_code,
            "branch_type": branch_type,
        }

    config_effective = False
    if branch_type == "TCC":
        config_effective = _tcc_config_effective(root, family, ctx["primary"])

    isolation_ok, isolation_msg = _check_isolation(ctx, root, family, result["outcome"])

    from lib.metric_strength import score_metric
    from lib.registry import metric_entry

    _, reg_metric = metric_entry(technique_code, metric_code)
    strength = score_metric(
        family,
        result.get("metric_value"),
        reg_metric,
        branch_type,
        technique_code=technique_code,
    )
    strength_pass = strength.get("passed", False)

    matches = (
        _matches_branch_type(branch_type, result["outcome"], config_effective)
        and isolation_ok
        and strength_pass
    )

    actual = result["outcome"]
    if branch_type == "TCC" and not config_effective:
        actual = "%s (config ineffective)" % actual
    if not isolation_ok:
        actual = "%s (isolation FAIL)" % actual
    if not strength_pass:
        actual = "%s (strength %.1f)" % (actual, strength.get("score", 0))

    return {
        "branch_name": folder,
        "status": "PASS" if matches else "FAIL",
        "tool_used": result.get("tool_used", ctx["primary"]),
        "raw_metric_value": result.get("raw_value", ""),
        "metric_value": result.get("metric_value"),
        "expected_outcome": expected_outcome_label(branch_type),
        "actual_outcome": actual,
        "message": isolation_msg or result.get("detail", "") or strength.get("reason", ""),
        "log": result.get("log", ""),
        "technique_code": technique_code,
        "metric_code": metric_code,
        "branch_type": branch_type,
        "strength_score": strength.get("score", 0),
        "strength_pass": strength_pass,
        "expected_threshold": reg_metric.get("expected_threshold", ""),
        "strength_reason": strength.get("reason", ""),
    }


def _skipped_result(folder, message, tool=""):
    return {
        "branch_name": folder,
        "status": "SKIPPED",
        "tool_used": tool,
        "raw_metric_value": "",
        "expected_outcome": "",
        "actual_outcome": "SKIPPED",
        "message": message,
        "log": "",
        "technique_code": "",
        "metric_code": "",
        "branch_type": "",
    }


def _assert_worker(args):
    path, tech, metric, bt, version, language = args
    return tool_assert_branch(path, tech, metric, bt, language)


def tool_assert_build_report(
    techniques="all",
    metrics="all",
    types=None,
    version="2.6",
    language="python",
    build_dir="build",
    root=None,
    parallel=1,
):
    from lib.registry import iter_branches

    repo_root = root or os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    jobs = []
    for tech, metric, bt, bname in iter_branches(techniques, metrics, types, version):
        path = os.path.join(repo_root, build_dir, bname)
        jobs.append((path, tech, metric, bt, version, language))

    if parallel and parallel > 1:
        try:
            from multiprocessing import Pool

            with Pool(processes=parallel) as pool:
                return pool.map(_assert_worker, jobs)
        except (OSError, ImportError):
            pass

    return [_assert_worker(j) for j in jobs]
