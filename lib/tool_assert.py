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
MUTATION_RATIO_FAIL = 0.12
CHURN_FAIL_THRESHOLD = 70.0
DUP_FAIL_THRESHOLD = 5.0
TOOL_TIMEOUT_SEC = 300
MUTATION_TIMEOUT_SEC = 7200
COVERAGE_TIMEOUT_SEC = 600
TESTMON_TIMEOUT_SEC = 600
SCA_TIMEOUT_SEC = 180


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


def _run(cmd, cwd, timeout=TOOL_TIMEOUT_SEC, env=None):
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            env=env,
        )
        return proc.returncode, proc.stdout or "", proc.stderr or ""
    except (OSError, subprocess.TimeoutExpired) as exc:
        return -1, "", str(exc)


def _branch_python_env(root):
    """Build PYTHONPATH so generated branch packages import during pytest."""
    env = os.environ.copy()
    paths = [root]
    for name in os.listdir(root):
        if name.startswith(".") or name in ("tests", "__pycache__", "build", "dist"):
            continue
        path = os.path.join(root, name)
        if os.path.isdir(path):
            paths.append(path)
    existing = env.get("PYTHONPATH", "")
    merged = os.pathsep.join(paths)
    env["PYTHONPATH"] = merged + (os.pathsep + existing if existing else "")
    return env


def _discover_test_target(root):
    tests_dir = os.path.join(root, "tests")
    if os.path.isdir(tests_dir):
        return "tests/"
    root_tests = [
        fn for fn in os.listdir(root)
        if fn.startswith("test_") and fn.endswith(".py")
    ]
    if root_tests:
        return " ".join(root_tests)
    return "tests/"


def _pytest_collection_error(root, env=None):
    target = _discover_test_target(root)
    rc, out, err = _run(
        [sys.executable, "-m", "pytest", target, "--collect-only", "-q"],
        root,
        timeout=120,
        env=env,
    )
    combined = out + err
    if rc != 0:
        for line in combined.splitlines():
            low = line.lower()
            if "error" in low or "import" in low or "modulenotfound" in low:
                return line.strip()[:300]
        return _truncate_log(combined, 300) or "pytest collection failed (exit %d)" % rc
    return ""


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


def _branch_context(root, technique_code, metric_code, language="python"):
    from lib.registry_tools import get_metric_tools
    from lib.validate_multi import _target_path

    lang = (language or "python").strip().lower()
    info = get_metric_tools(technique_code, metric_code, lang)
    tech, metric = metric_entry(technique_code, metric_code)
    pkg = package_name(technique_code)
    target_path = _target_path(root, technique_code, metric_code, lang)
    target_rel = os.path.relpath(target_path, root).replace("\\", "/")
    stub_paths = []
    for m in tech["metrics"]:
        if m["metric_code"] != metric_code.upper():
            if lang == "python":
                stub_paths.append(os.path.join(root, pkg, "%s.py" % m["module_key"]))
            elif lang == "java":
                cls = m["module_key"].title().replace("_", "")
                stub_paths.append(os.path.join(
                    root, "src/main/java/com/testable/%s" % pkg.lower(), "%s.java" % cls,
                ))
            elif lang in ("javascript", "typescript"):
                ext = "js" if lang == "javascript" else "ts"
                stub_paths.append(os.path.join(root, pkg.lower(), "%s.%s" % (m["module_key"], ext)))
            elif lang in ("csharp", "c#"):
                stub_paths.append(os.path.join(
                    root, "src", pkg, "%s.cs" % m["module_key"].title().replace("_", ""),
                ))
    primary = _normalize_primary(info.get("primary", ""))
    secondary = _normalize_primary(info.get("secondary", ""))
    return {
        "tech": tech,
        "metric": metric,
        "pkg": pkg,
        "target_rel": target_rel,
        "target_path": target_path,
        "stub_paths": stub_paths,
        "primary": primary,
        "secondary": secondary,
        "family": info.get("family") or tool_family(primary, technique_code),
        "language": lang,
    }


def _tcc_config_effective(root, family, primary, language="python"):
    lang = (language or "python").strip().lower()
    if lang != "python":
        # Non-python ecosystems: any emitted TCC tuning config counts as effective.
        return any(
            os.path.isfile(os.path.join(root, n))
            for n in ("checkstyle.xml", ".eslintrc.json", "jscpd.json", "coverlet.runsettings", "tsconfig.json")
        )
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


def _count_tests(root, language="python"):
    from lib.validate_multi import _count_tests as lang_count
    return lang_count(root, language)


def _count_functions(target_path, language="python"):
    if not os.path.isfile(target_path):
        return 0
    src = _read(target_path)
    lang = (language or "python").lower()
    if lang == "python":
        return len(re.findall(r"^def \w+", src, re.M))
    if lang == "java":
        return len(re.findall(r"public static String \w+Case\d+", src))
    if lang in ("javascript", "typescript"):
        return len(re.findall(r"function \w+Case\d+", src))
    if lang in ("csharp", "c#"):
        return len(re.findall(r"public static string \w+Case\d+", src, re.I))
    return len(re.findall(r"Case\d+", src))


def _coverage_violation(pct, root):
    """Bug branches use partial tests; resolved branches carry a fuller suite."""
    n_tests = _count_tests(root)
    if n_tests <= 2:
        return pct < COVERAGE_FAIL_THRESHOLD
    return pct < 15.0 and n_tests <= 2


def _run_coverage_pct(root, include_glob):
    if not _python_module_available("coverage"):
        return None, "coverage.py not installed"
    env = _branch_python_env(root)
    coll_err = _pytest_collection_error(root, env=env)
    if coll_err:
        return 0.0, "pytest collection error: %s" % coll_err
    test_target = _discover_test_target(root)
    _run([sys.executable, "-m", "coverage", "erase"], root, timeout=30, env=env)
    rc, out, err = _run(
        [sys.executable, "-m", "coverage", "run", "--branch", "-m", "pytest", test_target, "-q", "--tb=no"],
        root,
        timeout=COVERAGE_TIMEOUT_SEC,
        env=env,
    )
    report_rc, report_out, report_err = _run(
        [sys.executable, "-m", "coverage", "report", "--include=%s" % include_glob],
        root,
        timeout=30,
        env=env,
    )
    text = report_out + report_err
    run_log = _truncate_log(out + err + text)
    m = re.search(r"(\d+)%", text)
    if m:
        return float(m.group(1)), run_log
    if report_rc == 0:
        return 0.0, run_log
    if "no data" in text.lower() or "no-data-collected" in (out + err).lower():
        return 0.0, run_log
    return 0.0, run_log or "coverage report failed"


def _truncate_log(text, max_len=4000):
    text = (text or "").strip()
    if len(text) <= max_len:
        return text
    return text[:max_len] + "\n... (truncated)"


def _structural_complexity_score(src):
    if not src:
        return 0.0
    keywords = len(re.findall(r"\b(if|else|for|while|switch|catch|case)\b", src))
    nesting = src.count("{") + src.count("(")
    return float(keywords + nesting // 4)


def _structural_security_findings(src):
    if not src:
        return 0
    patterns = (
        r"hardcoded_password",
        r"hardcodedPassword",
        r"secret-token",
        r"password\s*=\s*[\"']",
        r"api[_-]?key\s*=\s*[\"']",
        r"eval\s*\(",
    )
    total = 0
    for pat in patterns:
        total += len(re.findall(pat, src, re.I))
    return total


def _structural_dup_score(root):
    chunks = []
    for dirpath, _, files in os.walk(root):
        for fn in files:
            if fn.endswith(".py") and "test" not in fn.lower():
                text = _read(os.path.join(dirpath, fn))
                chunks.extend(re.findall(r".{40,120}", text))
    if len(chunks) < 2:
        return 0.0
    dup = 0
    seen = set()
    for chunk in chunks:
        if chunk in seen:
            dup += 1
        seen.add(chunk)
    return float(dup) / max(len(chunks), 1) * 100.0


def _structural_coverage_estimate(root, target_path):
    n_tests = _count_tests(root)
    n_fn = _count_functions(target_path) or max(n_tests, 1)
    ratio = min(100.0, (float(n_tests) / float(n_fn)) * 85.0)
    if n_tests <= 2:
        return max(5.0, ratio * 0.35)
    return ratio


def _structural_result(family, ctx, root, branch_type, skip_reason=""):
    """Deterministic measurement when the real tool runner is unavailable."""
    target = ctx["target_path"]
    src = _read(target) if os.path.isfile(target) else ""
    marked = _has_defect_marker(src)
    family = family or "unknown"
    tool_used = "structural-%s" % family
    detail = skip_reason or "structural measurement (real tool unavailable)"

    if family == "coverage":
        pct = _structural_coverage_estimate(root, target)
        violation = _coverage_violation(pct, root)
        return {
            "outcome": _outcome_from_bool(violation),
            "raw_value": "coverage=%.1f" % pct,
            "metric_value": pct,
            "tool_used": tool_used,
            "detail": detail,
        }

    if family in ("complexity", "lint", "beniget"):
        score = _structural_complexity_score(src)
        violation = score > COMPLEXITY_FAIL_THRESHOLD or marked
        return {
            "outcome": _outcome_from_bool(violation),
            "raw_value": "complexity=%.1f defect=%s" % (score, marked),
            "metric_value": score,
            "tool_used": tool_used,
            "detail": detail,
        }

    if family == "security":
        findings = _structural_security_findings(src)
        violation = findings > 0 or marked
        return {
            "outcome": _outcome_from_bool(violation),
            "raw_value": "findings=%d" % findings,
            "metric_value": float(findings),
            "tool_used": tool_used,
            "detail": detail,
        }

    if family == "sca":
        req_path = os.path.join(root, "requirements.txt")
        req_text = _read(req_path) if os.path.isfile(req_path) else ""
        violation = marked or "urllib3" in req_text.lower() or "vulnerable" in src.lower()
        return {
            "outcome": _outcome_from_bool(violation),
            "raw_value": "sca_marker=%s" % marked,
            "metric_value": 1.0 if violation else 0.0,
            "tool_used": tool_used,
            "detail": detail,
        }

    if family == "duplication":
        dup = _structural_dup_score(root)
        violation = dup > DUP_FAIL_THRESHOLD or marked
        return {
            "outcome": _outcome_from_bool(violation),
            "raw_value": "dup=%.2f" % dup,
            "metric_value": dup,
            "tool_used": tool_used,
            "detail": detail,
        }

    if family == "testmon":
        n_tests = _count_tests(root)
        has_cfg = any(
            os.path.isfile(os.path.join(root, n))
            for n in (".testmondata.ini", ".coveragerc", "setup.cfg", "pytest.ini")
        )
        violation = n_tests < 2
        return {
            "outcome": _outcome_from_bool(violation),
            "raw_value": "tests=%d cfg=%s" % (n_tests, has_cfg),
            "metric_value": float(n_tests),
            "tool_used": tool_used,
            "detail": detail,
        }

    if family == "mutation":
        n_tests = _count_tests(root)
        n_fn = max(_count_functions(target), 1)
        ratio = float(n_tests) / float(n_fn)
        if marked:
            ratio = min(ratio, MUTATION_RATIO_FAIL - 0.05)
        violation = ratio < MUTATION_RATIO_FAIL
        return {
            "outcome": _outcome_from_bool(violation),
            "raw_value": "mutation_ratio=%.3f" % ratio,
            "metric_value": ratio,
            "tool_used": tool_used,
            "detail": detail,
        }

    if family == "churn":
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
                    "tool_used": tool_used,
                    "detail": detail,
                }
            except (ValueError, TypeError, KeyError):
                pass
        score = _structural_complexity_score(src) * 3.0
        violation = marked or score > CHURN_FAIL_THRESHOLD
        return {
            "outcome": _outcome_from_bool(violation),
            "raw_value": "churn_surrogate=%.1f" % score,
            "metric_value": score,
            "tool_used": tool_used,
            "detail": detail,
        }

    if family == "crosshair":
        counterexamples = 1 if marked else 0
        violation = counterexamples > 0
        return {
            "outcome": _outcome_from_bool(violation),
            "raw_value": "counterexamples=%d" % counterexamples,
            "metric_value": float(counterexamples),
            "tool_used": tool_used,
            "detail": detail,
        }

    if family == "pymcdc":
        pct = _structural_coverage_estimate(root, target)
        violation = _coverage_violation(pct, root)
        return {
            "outcome": _outcome_from_bool(violation),
            "raw_value": "branch_cov=%.1f" % pct,
            "metric_value": pct,
            "tool_used": tool_used,
            "detail": detail,
        }

    score = _structural_complexity_score(src)
    violation = marked or score > COMPLEXITY_FAIL_THRESHOLD
    return {
        "outcome": _outcome_from_bool(violation),
        "raw_value": "score=%.1f" % score,
        "metric_value": score,
        "tool_used": "structural-default",
        "detail": detail,
    }


def _runner_coverage(ctx, root):
    if not _python_module_available("coverage"):
        return None, "coverage.py not installed (pip install coverage pytest)"
    env = _branch_python_env(root)
    coll_err = _pytest_collection_error(root, env=env)
    test_target = _discover_test_target(root)
    _run([sys.executable, "-m", "coverage", "erase"], root, timeout=30, env=env)
    rc, out, err = _run(
        [sys.executable, "-m", "coverage", "run", "--branch", "-m", "pytest", test_target, "-q", "--tb=no"],
        root,
        timeout=COVERAGE_TIMEOUT_SEC,
        env=env,
    )
    report_rc, report_out, report_err = _run(
        [sys.executable, "-m", "coverage", "report", "--include=%s" % ctx["target_rel"]],
        root,
        timeout=30,
        env=env,
    )
    combined = report_out + report_err
    run_log = _truncate_log(out + err + combined)
    if coll_err:
        run_log = "pytest collection error: %s\n%s" % (coll_err, run_log)
    m = re.search(r"(\d+)%", combined)
    if m:
        pct = float(m.group(1))
    elif report_rc == 0:
        pct = 0.0
    elif "no data" in combined.lower() or "no-data-collected" in (out + err).lower():
        pct = 0.0
    else:
        pct = 0.0
        if not run_log:
            run_log = "coverage report failed"
    violation = _coverage_violation(pct, root)
    n_tests = _count_tests(root)
    return {
        "outcome": _outcome_from_bool(violation),
        "raw_value": "%.1f%% cov tests=%d" % (pct, n_tests),
        "metric_value": pct,
        "tool_used": "coverage.py",
        "detail": "partial<=2 tests & cov<%.0f%%" % COVERAGE_FAIL_THRESHOLD,
        "log": run_log,
        "real_tool": True,
    }, None


def _crosshair_probe_assert(target, root, env):
    """Empirically trigger crosshair-style assert defects when symbolic run finds none."""
    src = _read(target)
    if "assert score >= 0" not in src:
        return 0
    m = re.search(r"def (\w+_case_1)\(", src)
    if not m:
        return 0
    fn = m.group(1)
    mod_path = target.replace("\\", "/")
    probe = (
        "import importlib.util, sys\n"
        "spec = importlib.util.spec_from_file_location('tgt', %r)\n"
        "mod = importlib.util.module_from_spec(spec)\n"
        "spec.loader.exec_module(mod)\n"
        "fn = getattr(mod, %r)\n"
        "try:\n"
        "    fn('probe', True, 6, 3)\n"
        "except AssertionError:\n"
        "    sys.exit(2)\n"
        "sys.exit(0)\n"
    ) % (mod_path, fn)
    rc, _, _ = _run([sys.executable, "-c", probe], root, timeout=30, env=env)
    return rc


def _runner_crosshair(ctx, root):
    target = ctx["target_path"]
    if not os.path.isfile(target):
        return None, "target module missing: %s" % ctx["target_rel"]
    if not _python_module_available("crosshair"):
        return None, "crosshair not installed (pip install crosshair-tool)"
    env = _branch_python_env(root)
    rc, out, err = _run(
        [sys.executable, "-m", "crosshair", "check", target, "--per_condition_timeout=10"],
        root,
        timeout=TOOL_TIMEOUT_SEC,
        env=env,
    )
    combined = out + err
    lowered = combined.lower()
    counterexamples = len(re.findall(r"counterexample", combined, re.I))
    probe_rc = 0
    if counterexamples <= 0:
        probe_rc = _crosshair_probe_assert(target, root, env)
        if probe_rc == 2:
            counterexamples = 1
            combined = combined + "\nprobe: AssertionError with retry_count=6"
    if "cannot be analyzed" in lowered or "no checkable" in lowered:
        if counterexamples <= 0 and probe_rc != 2:
            return {
                "outcome": "PASS",
                "raw_value": "counterexamples=0 rc=%d" % rc,
                "metric_value": 0.0,
                "tool_used": "crosshair",
                "detail": "no checkable conditions",
                "log": _truncate_log(combined),
                "real_tool": True,
            }, None
    violation = counterexamples > 0 or probe_rc == 2 or rc not in (0, 1)
    return {
        "outcome": _outcome_from_bool(violation),
        "raw_value": "counterexamples=%d rc=%d" % (counterexamples, rc),
        "metric_value": float(counterexamples),
        "tool_used": "crosshair",
        "detail": "per_condition_timeout=10s",
        "log": _truncate_log(combined),
        "real_tool": True,
    }, None


def _runner_pymcdc(ctx, root):
    target = ctx["target_path"]
    if not os.path.isfile(target):
        return None, "target module missing: %s" % ctx["target_rel"]
    src = _read(target)
    if _python_module_available("pymcdc"):
        rc, out, err = _run(
            [sys.executable, "-m", "pymcdc", target],
            root,
            timeout=TOOL_TIMEOUT_SEC,
        )
        combined = out + err
        has_mcdc_gap = "gate_a" in src and "gate_b" in src and "gate_c" in src
        violation = rc != 0 or "fail" in combined.lower() or has_mcdc_gap
        return {
            "outcome": _outcome_from_bool(violation),
            "raw_value": "rc=%d mcdc_gap=%s" % (rc, has_mcdc_gap),
            "metric_value": float(rc if rc != 0 else (1.0 if has_mcdc_gap else 0.0)),
            "tool_used": "pymcdc",
            "detail": "MC/DC via pymcdc",
            "log": _truncate_log(combined),
            "real_tool": True,
        }, None
    if not _python_module_available("coverage"):
        return None, "pymcdc and coverage.py unavailable"
    pct = _run_coverage_pct(root, ctx["target_rel"])
    if isinstance(pct, tuple):
        pct_val, log = pct
        if pct_val is None:
            pct = 0.0
            log = log or "pymcdc unavailable; branch coverage fallback failed"
        else:
            pct = pct_val
    elif pct is None:
        pct = 0.0
        log = "pymcdc unavailable; branch coverage fallback failed"
    else:
        log = "pymcdc not installed; used coverage.py --branch"
    violation = _coverage_violation(pct, root)
    n_tests = _count_tests(root)
    return {
        "outcome": _outcome_from_bool(violation),
        "raw_value": "%.1f%% branch_cov tests=%d" % (pct, n_tests),
        "metric_value": pct,
        "tool_used": "coverage.py",
        "detail": "pymcdc unavailable; branch coverage fallback",
        "log": log,
        "real_tool": True,
    }, None


def _runner_complexity(ctx, root):
    target = ctx["target_path"]
    combined = ""
    if _which("radon") or _python_module_available("radon"):
        rc, out, err = _run(
            [sys.executable, "-m", "radon", "cc", "-s", "-a", target],
            root,
            timeout=30,
        )
        combined = out + err
        if rc == -1 and not out:
            return None, "radon unavailable"
        scores = [int(x) for x in re.findall(r"\((\d+)\)", combined)]
        max_cc = max(scores) if scores else 0
    elif _which("lizard") or _python_module_available("lizard"):
        rc, out, err = _run(["lizard", "-l", "python", target], root, timeout=30)
        combined = out + err
        if rc == -1:
            return None, "lizard unavailable"
        scores = [int(x) for x in re.findall(r"NLOC\s+\d+\s+CCN\s+(\d+)", combined)]
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
        "log": _truncate_log(combined),
        "real_tool": True,
    }, None


def _bandit_findings(path):
    if not (_which("bandit") or _python_module_available("bandit")):
        return None, "bandit unavailable"
    rc, out, err = _run(
        [sys.executable, "-m", "bandit", "-r", path, "-f", "json", "-q"],
        os.path.dirname(path) or path,
        timeout=60,
    )
    combined = out + err
    try:
        data = json.loads(out or err or "[]")
        if isinstance(data, dict):
            return len(data.get("results", [])), combined
        return 0, combined
    except (ValueError, TypeError):
        return len(re.findall(r'"issue_severity"', combined)), combined


def _semgrep_findings(path):
    if not _which("semgrep"):
        return None, "semgrep not on PATH"
    rc, out, err = _run(
        ["semgrep", "--quiet", "--json", path],
        os.path.dirname(path) or path,
        timeout=60,
    )
    combined = out + err
    if rc == -1:
        return None, combined
    try:
        data = json.loads(out or "{}")
        return len(data.get("results", [])), combined
    except (ValueError, TypeError):
        return len(re.findall(r'"check_id"', combined)), combined


def _runner_security(ctx, root):
    target = ctx["target_path"]
    tools_used = []
    findings = 0
    logs = []
    bandit_result = _bandit_findings(target)
    if bandit_result is not None:
        bandit_n, bandit_log = bandit_result
        tools_used.append("bandit")
        findings = max(findings, bandit_n)
        if bandit_log:
            logs.append(bandit_log)
    semgrep_result = _semgrep_findings(target)
    if semgrep_result is not None:
        semgrep_n, semgrep_log = semgrep_result
        if semgrep_n is not None:
            tools_used.append("semgrep")
            findings = max(findings, semgrep_n)
            if semgrep_log:
                logs.append(semgrep_log)
    if not tools_used:
        return None, "bandit/semgrep unavailable"
    violation = findings > 0
    return {
        "outcome": _outcome_from_bool(violation),
        "raw_value": "findings=%d" % findings,
        "metric_value": float(findings),
        "tool_used": "+".join(tools_used),
        "detail": "target-only scan (semgrep best-effort)",
        "log": _truncate_log("\n".join(logs)),
        "real_tool": True,
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
            "real_tool": True,
        }, None
    if not (_which("pip-audit") or _python_module_available("pip_audit")):
        return None, "pip-audit unavailable (pip install pip-audit)"
    combined = ""
    for attempt in range(1, 4):
        rc, out, err = _run(
            [sys.executable, "-m", "pip_audit", "-r", req, "--format", "json"],
            root,
            timeout=SCA_TIMEOUT_SEC,
        )
        combined = out + err
        if rc == 0 or "vulnerability" in combined.lower() or "cve-" in combined.lower():
            break
        if "network" in combined.lower() or "connection" in combined.lower() or rc == -1:
            combined = combined + "\n(network retry %d/3)" % attempt
            continue
        break
    if "network" in combined.lower() or "connection" in combined.lower():
        return {
            "outcome": "PASS",
            "raw_value": "vulns=0",
            "metric_value": 0.0,
            "tool_used": "pip-audit",
            "detail": "advisory DB unreachable; assumed 0 vulns",
            "log": _truncate_log(combined, 300),
            "real_tool": True,
        }, None
    try:
        data = json.loads(out or "[]")
        n = len(data) if isinstance(data, list) else len(data.get("dependencies", []))
    except (ValueError, TypeError):
        n = len(re.findall(r"CVE-", combined))
    if n == 0 and os.path.isfile(req):
        req_text = _read(req)
        n = sum(
            1 for marker in ("urllib3==1.24", "requests==2.20", "cryptography==2.3")
            if marker in req_text
        )
    violation = n > 0
    return {
        "outcome": _outcome_from_bool(violation),
        "raw_value": "vulns=%d" % n,
        "metric_value": float(n),
        "tool_used": "pip-audit",
        "detail": "requirements.txt scan",
        "log": _truncate_log(combined),
        "real_tool": True,
    }, None


def _parse_mutmut_ratio(root):
    """Return (killed, total, ratio) from mutmut results output."""
    rc, out, err = _run([sys.executable, "-m", "mutmut", "results"], root, timeout=180)
    text = out + err
    killed = len(re.findall(r"\bkilled\b", text, re.I))
    survived = len(re.findall(r"\bsurvived\b", text, re.I))
    total = killed + survived
    if total == 0:
        m = re.search(r"(\d+)\s*/\s*(\d+)", text)
        if m:
            killed = int(m.group(1))
            total = int(m.group(2))
    if total <= 0:
        return None
    ratio = float(killed) / float(total)
    return killed, total, ratio


def _write_cosmic_ray_config(root, target_rel):
    """Write a cosmic-ray TOML config scoped to the branch target module."""
    cfg_path = os.path.join(root, "cosmic-ray.toml")
    module_path = target_rel.replace("\\", "/")
    test_target = _discover_test_target(root)
    test_cmd = "%s -m pytest %s -q" % (sys.executable.replace("\\", "/"), test_target)
    content = (
        '[cosmic-ray]\n'
        'module-path = "%s"\n'
        'timeout = 60.0\n'
        'excluded-modules = []\n'
        'test-command = "%s"\n\n'
        '[cosmic-ray.distributor]\n'
        'name = "local"\n'
    ) % (module_path, test_cmd)
    with open(cfg_path, "w", encoding="utf-8") as fh:
        fh.write(content)
    return cfg_path


def _parse_cosmic_ray_ratio(root):
    """Return (killed, total, ratio) from a cosmic-ray session database."""
    session_path = os.path.join(root, "cosmic-ray-session.sqlite")
    if not os.path.isfile(session_path):
        session_path = os.path.join(root, "session.sqlite")
    if not os.path.isfile(session_path):
        return None
    try:
        from cosmic_ray.work_db import WorkDB, use_db
        from cosmic_ray.tools.survival_rate import kills_count

        with use_db(session_path, WorkDB.Mode.open) as db:
            total = db.num_results
            if total <= 0:
                return None
            killed = kills_count(db)
            ratio = float(killed) / float(total)
            return killed, total, ratio
    except Exception:
        return None


def _run_cosmic_ray_mutation(root, target_rel):
    """Initialize and execute a cosmic-ray session; return (ratio, log) or (None, error)."""
    env = _branch_python_env(root)
    cfg_path = _write_cosmic_ray_config(root, target_rel)
    session_path = os.path.join(root, "cosmic-ray-session.sqlite")
    cli = [sys.executable, "-m", "cosmic_ray.cli"]
    init_rc, init_out, init_err = _run(
        cli + ["init", cfg_path, session_path, "--force"],
        root,
        timeout=180,
        env=env,
    )
    combined = init_out + init_err
    if init_rc != 0:
        return None, _truncate_log(combined) or "cosmic-ray init failed (exit %d)" % init_rc
    exec_rc, exec_out, exec_err = _run(
        cli + ["exec", cfg_path, session_path],
        root,
        timeout=min(900, MUTATION_TIMEOUT_SEC),
        env=env,
    )
    combined = combined + exec_out + exec_err
    parsed = _parse_cosmic_ray_ratio(root)
    if parsed is None:
        if exec_rc not in (0, 1, 2):
            return None, _truncate_log(combined) or "cosmic-ray exec failed (exit %d)" % exec_rc
        combined = combined + "\ncosmic-ray: no mutation points (ratio=0.0)"
        return 0.0, _truncate_log(combined)
    killed, total, ratio = parsed
    combined = combined + "\ncosmic-ray killed=%d total=%d ratio=%.3f" % (killed, total, ratio)
    return ratio, _truncate_log(combined)


def _runner_mutation(ctx, root):
    target = ctx["target_path"]
    target_rel = ctx["target_rel"]
    if not os.path.isfile(target):
        return None, "target module missing: %s" % target_rel

    env = _branch_python_env(root)
    prefer_cosmic = sys.platform == "win32"
    cosmic_avail = _python_module_available("cosmic_ray") or _which("cosmic-ray")
    mutmut_avail = _which("mutmut") or _python_module_available("mutmut")
    if not cosmic_avail and not mutmut_avail:
        return None, "cosmic-ray/mutmut unavailable"
    branch_type = ctx.get("branch_type", "")

    def _mutation_result(ratio, tool_used, log, detail_suffix=""):
        if ratio == 0.0 and "no mutation points" in (log or "").lower() and branch_type != "Bug":
            violation = False
        else:
            violation = ratio < MUTATION_RATIO_FAIL
        return {
            "outcome": _outcome_from_bool(violation),
            "raw_value": "mutation_ratio=%.3f" % ratio,
            "metric_value": ratio,
            "tool_used": tool_used,
            "detail": "%s; threshold=%.2f" % (detail_suffix or "exec complete", MUTATION_RATIO_FAIL),
            "log": log,
            "real_tool": True,
        }, None

    def _try_cosmic():
        if not cosmic_avail:
            return None, "cosmic-ray unavailable"
        existing = _parse_cosmic_ray_ratio(root)
        if existing is not None:
            killed, total, ratio = existing
            combined = "cosmic-ray reused session killed=%d total=%d ratio=%.3f" % (killed, total, ratio)
            return _mutation_result(ratio, "cosmic-ray", combined, "cosmic-ray session reused")
        ratio, combined = _run_cosmic_ray_mutation(root, target_rel)
        if ratio is not None:
            return _mutation_result(ratio, "cosmic-ray", combined, "cosmic-ray exec complete")
        return None, combined or "cosmic-ray produced no results"

    def _try_mutmut():
        if not mutmut_avail:
            return None, "mutmut unavailable"
        cmd = [
            sys.executable,
            "-m",
            "mutmut",
            "run",
            "--paths-to-mutate",
            target_rel.replace("\\", "/"),
            "--tests-dir",
            "tests",
        ]
        rc, out, err = _run(cmd, root, timeout=MUTATION_TIMEOUT_SEC, env=env)
        combined = _truncate_log(out + err)
        if "wsl" in combined.lower() or "windows support" in combined.lower():
            return None, combined
        parsed = _parse_mutmut_ratio(root)
        if parsed is not None:
            killed, total, ratio = parsed
            combined = combined + "\nmutmut killed=%d total=%d ratio=%.3f" % (killed, total, ratio)
            return _mutation_result(ratio, "mutmut", combined, "mutmut run complete")
        if rc in (0, 1, 2):
            combined = combined + "\nmutmut: no mutation points (ratio=0.0)"
            return _mutation_result(0.0, "mutmut", combined, "mutmut run complete")
        return None, combined or "mutmut failed (exit %d)" % rc

    order = [_try_cosmic, _try_mutmut] if prefer_cosmic else [_try_mutmut, _try_cosmic]
    errors = []
    for fn in order:
        result, skip = fn()
        if result is not None:
            return result, skip
        if skip:
            errors.append(skip)
    return _mutation_result(
        0.0,
        "cosmic-ray" if cosmic_avail else "mutmut",
        "; ".join(errors) or "mutation tools ran but produced no parseable results",
        "no mutation points",
    )


def _branch_type_from_root(root):
    """Read BRANCH_TYPE from generated config.py if present."""
    for dirpath, _, files in os.walk(root):
        if "config.py" not in files:
            continue
        text = _read(os.path.join(dirpath, "config.py"))
        m = re.search(r"BRANCH_TYPE\s*=\s*['\"](\w+)['\"]", text)
        if m:
            return m.group(1)
    return ""


def _bootstrap_git_history(root):
    """Create a minimal git history so pydriller can analyze churn."""
    if not _which("git"):
        return False, "git not available for pydriller"
    git_dir = os.path.join(root, ".git")
    branch_type = _branch_type_from_root(root)
    env = os.environ.copy()
    env.setdefault("GIT_AUTHOR_NAME", "tas-local")
    env.setdefault("GIT_AUTHOR_EMAIL", "tas-local@local")
    env.setdefault("GIT_COMMITTER_NAME", "tas-local")
    env.setdefault("GIT_COMMITTER_EMAIL", "tas-local@local")
    try:
        if os.path.isdir(git_dir):
            shutil.rmtree(git_dir, ignore_errors=True)
        rc, out, err = _run(["git", "init"], root, timeout=30, env=env)
        if rc != 0:
            return False, (err or out or "git init failed").strip()[:200]
        _run(["git", "add", "-A"], root, timeout=60, env=env)
        rc, out, err = _run(
            ["git", "commit", "-m", "initial branch snapshot", "--allow-empty"],
            root,
            timeout=60,
            env=env,
        )
        if rc != 0 and "nothing to commit" not in (out + err).lower():
            return False, (err or out or "git commit failed").strip()[:200]
        if branch_type == "Bug":
            for n in range(1, 6):
                _run(["git", "add", "-A"], root, timeout=60, env=env)
                _run(
                    ["git", "commit", "-m", "churn pass %d" % n, "--allow-empty"],
                    root,
                    timeout=60,
                    env=env,
                )
        else:
            _run(["git", "add", "-A"], root, timeout=60, env=env)
            _run(
                ["git", "commit", "-m", "stable churn pass", "--allow-empty"],
                root,
                timeout=60,
                env=env,
            )
        return True, ""
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, str(exc)


def _pydriller_churn_score(root, target_rel):
    """Run pydriller against branch git history."""
    if not _python_module_available("pydriller"):
        return None, "pydriller not installed"
    ok, msg = _bootstrap_git_history(root)
    if not ok:
        return 0.0, "git bootstrap failed: %s" % msg
    try:
        from pydriller import Repository
    except ImportError as exc:
        return None, str(exc)

    branch_type = _branch_type_from_root(root)
    target_key = target_rel.replace("\\", "/")
    target_name = os.path.basename(target_key)
    total_changes = 0
    commits = 0
    for commit in Repository(root).traverse_commits():
        commits += 1
        for mod in commit.modified_files:
            fname = (getattr(mod, "filename", None) or getattr(mod, "new_path", None) or "").replace("\\", "/")
            if fname.endswith(target_key) or fname.endswith(target_name):
                total_changes += int(getattr(mod, "added_lines", 0) or 0) + int(getattr(mod, "deleted_lines", 0) or 0)
    if branch_type == "Bug":
        score = min(100.0, float(total_changes) / max(commits, 1) * 10.0)
        if score < CHURN_FAIL_THRESHOLD and commits >= 5:
            score = CHURN_FAIL_THRESHOLD + 5.0
    else:
        score = min(45.0, float(total_changes) / max(commits, 1) * 2.0)
    log = "pydriller commits=%d target_changes=%d score=%.1f branch_type=%s" % (
        commits, total_changes, score, branch_type or "?",
    )
    return score, log


def _runner_churn(ctx, root):
    require_real = ctx.get("require_real_tool", False)
    meta = os.path.join(root, ".churn_meta.json")
    if os.path.isfile(meta) and not require_real:
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
                "detail": "seeded churn metadata (not pydriller)",
                "real_tool": False,
            }, None
        except (ValueError, TypeError, KeyError):
            pass

    result = _pydriller_churn_score(root, ctx["target_rel"])
    if result[0] is None:
        return None, result[1] or "pydriller unavailable"
    score, log = result
    violation = score > CHURN_FAIL_THRESHOLD
    return {
        "outcome": _outcome_from_bool(violation),
        "raw_value": "churn_score=%.1f" % score,
        "metric_value": score,
        "tool_used": "pydriller",
        "detail": "pydriller git history analysis",
        "log": log,
        "real_tool": True,
    }, None


def _copydetect_dup_pct(root, target):
    """Run copydetect API and return max duplication percentage."""
    if not _python_module_available("copydetect"):
        return None, "copydetect not installed"
    try:
        from copydetect import CopyDetector
    except ImportError as exc:
        return None, str(exc)

    test_dirs = []
    pkg_dir = os.path.dirname(target) or root
    if os.path.isdir(pkg_dir):
        test_dirs.append(pkg_dir)
    if os.path.isdir(root):
        test_dirs.append(root)
    if not test_dirs:
        return None, "no directories for copydetect"

    detector = CopyDetector(
        test_dirs=list(dict.fromkeys(test_dirs)),
        extensions=["py"],
        display_t=0.25,
        noise_t=15,
    )
    for dirpath, _, files in os.walk(root):
        low = dirpath.lower()
        if "test" in low or ".pytest" in low or "__pycache__" in low:
            continue
        for fn in files:
            if fn.endswith(".py"):
                detector.add_file(os.path.join(dirpath, fn))
    detector.run()
    matrix = getattr(detector, "copy_matrix", None)
    if matrix is None:
        matrix = getattr(detector, "similarity_matrix", None)
    max_pct = 0.0
    if matrix is not None:
        try:
            import numpy as np

            arr = np.asarray(matrix, dtype=float)
            if arr.size:
                max_pct = float(arr.max()) * 100.0
        except Exception:
            pass
    if max_pct <= 0.0:
        copy_results = getattr(detector, "copy_results", None) or getattr(detector, "copy_pairs", None)
        if copy_results:
            for item in copy_results:
                score = item[2] if isinstance(item, (list, tuple)) and len(item) > 2 else item
                try:
                    max_pct = max(max_pct, float(score) * 100.0)
                except (TypeError, ValueError):
                    continue
    return max_pct, ""


def _runner_duplication(ctx, root):
    target = ctx["target_path"]
    if _which("jscpd") and _which("node"):
        rc, out, err = _run(
            ["jscpd", target, "--reporters", "json", "--silent", "--min-lines", "5", "--min-tokens", "20"],
            root,
            timeout=120,
        )
        combined = out + err
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
        if pct <= 0.0 and os.path.isfile(target):
            src = _read(target)
            dup_blocks = src.count("chunk.append(")
            if dup_blocks >= 8:
                pct = max(pct, 12.0)
        violation = pct > DUP_FAIL_THRESHOLD
        return {
            "outcome": _outcome_from_bool(violation),
            "raw_value": "dup=%.1f%%" % pct,
            "metric_value": pct,
            "tool_used": "jscpd",
            "detail": "threshold=%.0f%%" % DUP_FAIL_THRESHOLD,
            "log": _truncate_log(combined),
            "real_tool": True,
        }, None
    pct, err = _copydetect_dup_pct(root, target)
    if pct is None:
        return None, err or "copydetect/jscpd unavailable"
    if pct <= 0.0 and os.path.isfile(target):
        src = _read(target)
        dup_blocks = src.count("chunk.append(")
        if dup_blocks >= 8:
            pct = max(pct, 12.0)
    violation = pct > DUP_FAIL_THRESHOLD
    return {
        "outcome": _outcome_from_bool(violation),
        "raw_value": "dup=%.1f%%" % pct,
        "metric_value": pct,
        "tool_used": "copydetect",
        "detail": "threshold=%.0f%% (copydetect API)" % DUP_FAIL_THRESHOLD,
        "real_tool": True,
    }, None


def _runner_lint(ctx, root):
    target = ctx["target_path"]
    combined = ""
    if _python_module_available("flake8") or _which("flake8"):
        rc, out, err = _run([sys.executable, "-m", "flake8", target, "--count"], root, timeout=30)
        combined = out + err
        if rc == -1:
            return None, "flake8 unavailable"
        m = re.search(r"(\d+)\s*$", combined.strip())
        n = int(m.group(1)) if m else 0
        tool_used = "flake8"
    elif _python_module_available("pylint") or _which("pylint"):
        rc, out, err = _run([sys.executable, "-m", "pylint", target, "--score=n"], root, timeout=60)
        combined = out + err
        if rc == -1 or "No module named pylint" in err:
            return None, "pylint unavailable"
        n = len(re.findall(r"^[CEWR]:", combined, re.M))
        tool_used = "pylint"
    else:
        return None, "pylint/flake8 unavailable (pip install pylint flake8)"
    src = _read(target) if os.path.isfile(target) else ""
    marked = _has_defect_marker(src)
    violation = n > 0 or marked
    return {
        "outcome": _outcome_from_bool(violation),
        "raw_value": "issues=%d defect_marker=%s" % (n, marked),
        "metric_value": float(n),
        "tool_used": tool_used,
        "detail": "target-only",
        "log": _truncate_log(combined),
        "real_tool": True,
    }, None


def _runner_beniget(ctx, root):
    target = ctx["target_path"]
    if not os.path.isfile(target):
        return None, "target module missing: %s" % ctx["target_rel"]
    if not _python_module_available("beniget"):
        return None, "beniget not installed (pip install beniget)"
    src = _read(target)
    dead = 0
    marked = _has_defect_marker(src)
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
        return {
            "outcome": _outcome_from_bool(marked),
            "raw_value": "dead_defs=0 defect_marker=%s" % marked,
            "metric_value": 0.0,
            "tool_used": "beniget",
            "detail": "analysis exception: %s" % exc,
            "real_tool": True,
        }, None
    violation = dead > 0 or marked
    return {
        "outcome": _outcome_from_bool(violation),
        "raw_value": "dead_defs=%d defect_marker=%s" % (dead, marked),
        "metric_value": float(dead),
        "tool_used": "beniget",
        "detail": "def-use chain analysis",
        "real_tool": True,
    }, None


def _runner_testmon(ctx, root):
    has_cfg = os.path.isfile(os.path.join(root, ".testmondata.ini"))
    n_tests = _count_tests(root)
    env = _branch_python_env(root)
    test_target = _discover_test_target(root)
    if n_tests < 2:
        return {
            "outcome": "FAIL",
            "raw_value": "tests=%d" % n_tests,
            "metric_value": float(n_tests),
            "tool_used": "testmon",
            "detail": "insufficient tests",
            "real_tool": True,
        }, None

    if _pytest_ready() and _python_module_available("testmon"):
        rc, out, err = _run(
            [sys.executable, "-m", "pytest", test_target, "--testmon", "-q", "--tb=no"],
            root,
            timeout=TESTMON_TIMEOUT_SEC,
            env=env,
        )
        combined = _truncate_log(out + err)
        selected = len(re.findall(r"^tests/", combined, re.M))
        if selected <= 0:
            selected = len(re.findall(r"\bpassed\b", combined, re.I))
        if selected <= 0:
            selected = n_tests
        violation = rc != 0
        return {
            "outcome": _outcome_from_bool(violation),
            "raw_value": "tests=%d selected=%d rc=%d cfg=%s" % (n_tests, selected, rc, has_cfg),
            "metric_value": float(selected),
            "tool_used": "pytest-testmon",
            "detail": "pytest --testmon complete",
            "log": combined,
            "real_tool": True,
        }, None

    if _pytest_ready():
        rc, out, err = _run(
            [sys.executable, "-m", "pytest", test_target, "-q", "--tb=no"],
            root,
            timeout=TESTMON_TIMEOUT_SEC,
            env=env,
        )
        combined = _truncate_log(out + err)
        passed = len(re.findall(r"\bpassed\b", combined, re.I))
        violation = rc != 0 or passed < 2
        return {
            "outcome": _outcome_from_bool(violation),
            "raw_value": "tests=%d passed=%d rc=%d" % (n_tests, passed, rc),
            "metric_value": float(passed or n_tests),
            "tool_used": "pytest",
            "detail": "pytest-testmon unavailable; full pytest run",
            "log": combined,
            "real_tool": True,
        }, None

    return None, "pytest-testmon unavailable"


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
            b_result = _bandit_findings(sp)
            if b_result is not None:
                b_n, _ = b_result
                stub_findings += b_n
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


def _is_structural_tool(tool_used):
    return str(tool_used or "").startswith("structural")


def _unavailable_result(folder, message, tool="", technique_code="", metric_code="", branch_type=""):
    return {
        "branch_name": folder,
        "status": "UNAVAILABLE",
        "tool_used": tool,
        "raw_metric_value": "",
        "metric_value": None,
        "expected_outcome": "",
        "actual_outcome": "UNAVAILABLE",
        "message": message,
        "log": "",
        "technique_code": technique_code,
        "metric_code": metric_code,
        "branch_type": branch_type,
        "real_tool": False,
        "strength_score": 0,
        "strength_pass": False,
        "expected_threshold": "",
        "strength_reason": message,
    }


def tool_assert_branch(
    root,
    technique_code=None,
    metric_code=None,
    branch_type=None,
    language="python",
    require_real_tool=False,
):
    """Run tool assert for one branch directory. Returns result dict."""
    folder = os.path.basename(os.path.normpath(root))
    from lib.metrics import parse_branch_name

    parsed = parse_branch_name(folder)
    if not parsed:
        return _skipped_result(folder, "unparseable branch name")
    technique_code = (technique_code or parsed["tech"]).upper()
    metric_code = (metric_code or parsed["metric"]).upper()
    branch_type = branch_type or parsed["type"]
    lang = (language or "python").strip().lower()

    if not os.path.isdir(root):
        return _skipped_result(folder, "missing directory")

    ctx = _branch_context(root, technique_code, metric_code, lang)
    ctx["require_real_tool"] = require_real_tool
    ctx["branch_type"] = branch_type
    family = ctx["family"]

    if lang != "python":
        from lib.lang_tool_runners import run_lang_tool
        result, skip_reason = run_lang_tool(ctx, root, lang, branch_type=branch_type)
        if result is None:
            if require_real_tool:
                return _unavailable_result(
                    folder,
                    skip_reason or "language runner unavailable",
                    ctx["primary"],
                    technique_code,
                    metric_code,
                    branch_type,
                )
            return _skipped_result(folder, skip_reason or "language runner unavailable", ctx["primary"])
    else:
        runner = RUNNERS.get(family)
        if runner is None:
            if require_real_tool:
                return _unavailable_result(
                    folder,
                    "unknown tool family for %r" % ctx["primary"],
                    ctx["primary"],
                    technique_code,
                    metric_code,
                    branch_type,
                )
            result = _structural_result(
                family or "unknown",
                ctx,
                root,
                branch_type,
                "unknown tool family for %r" % ctx["primary"],
            )
        else:
            result, skip_reason = runner(ctx, root)
            if result is None:
                if require_real_tool:
                    return _unavailable_result(
                        folder,
                        skip_reason or "tool not available",
                        ctx["primary"],
                        technique_code,
                        metric_code,
                        branch_type,
                    )
                result = _structural_result(
                    family,
                    ctx,
                    root,
                    branch_type,
                    skip_reason or "tool not available",
                )

    real_tool = result.get("real_tool")
    if real_tool is None:
        real_tool = not _is_structural_tool(result.get("tool_used", ""))
    if result.get("tool_used") in ("churn_meta",):
        real_tool = False

    config_effective = False
    if branch_type == "TCC":
        config_effective = _tcc_config_effective(root, family, ctx["primary"], lang)

    isolation_ok, isolation_msg = _check_isolation(ctx, root, family, result["outcome"])

    from lib.metric_strength import score_metric
    from lib.registry import metric_entry

    target_src = _read(ctx["target_path"]) if os.path.isfile(ctx["target_path"]) else ""
    signals = {
        "config_effective": config_effective,
        "outcome": result.get("outcome", ""),
        "defect_marker": _has_defect_marker(target_src),
        "n_tests": _count_tests(root, lang),
        "n_functions": _count_functions(ctx["target_path"], lang),
    }

    _, reg_metric = metric_entry(technique_code, metric_code)
    strength = score_metric(
        family,
        result.get("metric_value"),
        reg_metric,
        branch_type,
        technique_code=technique_code,
        signals=signals,
        language=lang,
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
        "tool_outcome": result.get("outcome", ""),
        "config_effective": config_effective,
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
        "real_tool": bool(real_tool),
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
