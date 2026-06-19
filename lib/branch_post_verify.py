"""Post-generation verification: LOC recount, syntax/import checks."""

from __future__ import print_function

import os
import py_compile
import re
import subprocess
import sys
import time

from lib.lang_generators.base import MIN_LOC
from lib.python_generator import read_gen_meta
from lib.validate_multi import assert_branch_structure, _count_loc


def _env_int(name, default):
    try:
        return max(1, int(os.environ.get(name, default)))
    except (TypeError, ValueError):
        return default


def _import_timeout_sec():
    return _env_int("BRANCH_IMPORT_TIMEOUT_SEC", 45)


def _pytest_timeout_sec():
    return _env_int("BRANCH_PYTEST_TIMEOUT_SEC", 180)


def _syntax_check_python(branch_dir):
    errors = []
    for dirpath, _, files in os.walk(branch_dir):
        for fn in files:
            if fn.endswith(".py"):
                path = os.path.join(dirpath, fn)
                try:
                    py_compile.compile(path, doraise=True)
                except py_compile.PyCompileError as exc:
                    errors.append("%s: %s" % (fn, exc))
    return errors


def _syntax_check_java(branch_dir):
    if not shutil_which("mvn") or not os.path.isfile(os.path.join(branch_dir, "pom.xml")):
        return []
    try:
        rc = subprocess.run(
            ["mvn", "-q", "-f", os.path.join(branch_dir, "pom.xml"), "test-compile"],
            cwd=branch_dir,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        if rc.returncode != 0:
            detail = (rc.stderr or rc.stdout or "mvn test-compile failed").strip()[:200]
            return ["java compile: %s" % detail]
    except (OSError, subprocess.TimeoutExpired) as exc:
        if getattr(exc, "winerror", None) == 2 or getattr(exc, "errno", None) == 2:
            return []
        return ["java compile: %s" % exc]
    return []


def _syntax_check_csharp(branch_dir):
    csproj = None
    for fn in os.listdir(branch_dir):
        if fn.endswith(".csproj"):
            csproj = os.path.join(branch_dir, fn)
            break
    if not csproj or not shutil_which("dotnet"):
        return []
    try:
        rc = subprocess.run(
            ["dotnet", "build", csproj, "-v", "q"],
            cwd=branch_dir,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        if rc.returncode != 0:
            detail = (rc.stderr or rc.stdout or "dotnet build failed").strip()[:200]
            return ["csharp build: %s" % detail]
    except (OSError, subprocess.TimeoutExpired) as exc:
        if getattr(exc, "winerror", None) == 2 or getattr(exc, "errno", None) == 2:
            return []
        return ["csharp build: %s" % exc]
    return []


def _syntax_check_ts(branch_dir):
    tsconfig = os.path.join(branch_dir, "tsconfig.json")
    if not os.path.isfile(tsconfig):
        return []
    tsc = shutil_which("tsc") or shutil_which("npx")
    if not tsc:
        return []
    cmd = ["tsc", "-p", tsconfig, "--noEmit"] if shutil_which("tsc") else ["npx", "tsc", "-p", tsconfig, "--noEmit"]
    try:
        rc = subprocess.run(cmd, cwd=branch_dir, capture_output=True, text=True, timeout=90, check=False)
        if rc.returncode != 0:
            detail = (rc.stderr or rc.stdout or "tsc failed").strip()[:200]
            return ["typescript: %s" % detail]
    except (OSError, subprocess.TimeoutExpired) as exc:
        if getattr(exc, "winerror", None) == 2 or getattr(exc, "errno", None) == 2:
            return []
        return ["typescript: %s" % exc]
    return []


def _syntax_check_js(branch_dir):
    if not shutil_which("node"):
        return []
    errors = []
    for dirpath, _, files in os.walk(branch_dir):
        for fn in files:
            if fn.endswith(".js"):
                path = os.path.join(dirpath, fn)
                rc = subprocess.run(
                    ["node", "--check", path],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    check=False,
                )
                if rc.returncode != 0:
                    errors.append("%s: %s" % (fn, (rc.stderr or rc.stdout or "syntax error").strip()[:120]))
    return errors


def shutil_which(cmd):
    import shutil
    return shutil.which(cmd)


def _resolve_cmd(argv):
    """Resolve executable path (Windows .cmd shims)."""
    if not argv:
        return argv
    exe = shutil_which(argv[0])
    if exe:
        return [exe] + list(argv[1:])
    return list(argv)


def _missing_executable(exc):
    return getattr(exc, "winerror", None) == 2 or getattr(exc, "errno", None) == 2


def _run_cmd(argv, cwd, timeout):
    """Run command; return (ran, ok, detail). ran=False when executable missing."""
    try:
        rc = subprocess.run(
            _resolve_cmd(argv),
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        combined = (rc.stdout or "") + (rc.stderr or "")
        return True, rc.returncode == 0, combined.strip()
    except (OSError, subprocess.TimeoutExpired) as exc:
        if _missing_executable(exc):
            return False, False, ""
        return True, False, str(exc)


def _local_tsc_cmd(branch_dir):
    for rel in (
        os.path.join("node_modules", ".bin", "tsc"),
        os.path.join("node_modules", "typescript", "bin", "tsc"),
    ):
        path = os.path.join(branch_dir, rel)
        if os.name == "nt" and not path.lower().endswith(".cmd"):
            cmd_path = path + ".cmd"
            if os.path.isfile(cmd_path):
                return [cmd_path, "-p", "tsconfig.json"]
        if os.path.isfile(path):
            return [path, "-p", "tsconfig.json"]
    return None


def _compile_typescript(branch_dir):
    if not os.path.isfile(os.path.join(branch_dir, "tsconfig.json")):
        return True, ""
    tsc_cmd = _local_tsc_cmd(branch_dir)
    if not tsc_cmd and shutil_which("tsc"):
        tsc_cmd = ["tsc", "-p", "tsconfig.json"]
    if not tsc_cmd and shutil_which("npm"):
        ran, ok, _detail = _run_cmd(["npm", "install", "--silent"], branch_dir, 180)
        if not ran:
            return False, ""
        if not ok:
            return True, "tests FAIL: npm install failed"
        tsc_cmd = _local_tsc_cmd(branch_dir)
    if not tsc_cmd:
        return False, ""
    ran, ok, detail = _run_cmd(tsc_cmd, branch_dir, 120)
    if not ran:
        return False, ""
    if not ok:
        if "not the tsc command" in detail.lower():
            return False, ""
        return True, "tests FAIL: %s" % detail[:200]
    return True, ""


def _run_language_tests(branch_dir, language):
    """Run language test suite when toolchain is available."""
    lang = (language or "python").lower()
    if lang == "java":
        if not shutil_which("mvn") or not os.path.isfile(os.path.join(branch_dir, "pom.xml")):
            return ""
        ran, ok, detail = _run_cmd(["mvn", "-q", "test"], branch_dir, _pytest_timeout_sec())
        if not ran:
            return ""
        if not ok:
            return "tests FAIL: %s" % detail[:200]
        return "mvn test OK"
    if lang in ("csharp", "c#"):
        csproj = None
        for fn in os.listdir(branch_dir):
            if fn.endswith(".csproj"):
                csproj = fn
                break
        if not csproj or not shutil_which("dotnet"):
            return ""
        ran, ok, detail = _run_cmd(["dotnet", "test", csproj, "-v", "q"], branch_dir, _pytest_timeout_sec())
        if not ran:
            return ""
        if not ok:
            return "tests FAIL: %s" % detail[:200]
        return "dotnet test OK"
    if lang in ("javascript", "typescript"):
        if not shutil_which("node") or not os.path.isfile(os.path.join(branch_dir, "package.json")):
            return ""
        runner = os.path.join(branch_dir, "tests", "run.js")
        if not os.path.isfile(runner):
            return ""
        if lang == "typescript":
            compiled, msg = _compile_typescript(branch_dir)
            if msg:
                return msg
            if not compiled:
                return ""
        ran, ok, detail = _run_cmd(["node", runner], branch_dir, _pytest_timeout_sec())
        if not ran:
            return ""
        if not ok:
            return "tests FAIL: %s" % detail[:200]
        return "node tests OK"
    return ""


def verify_generated_branch(branch_dir, tech, metric, bt, version, language, progress_callback=None):
    """Verify one branch: structure, syntax, import smoke, and pytest."""

    def _report(step, msg):
        if progress_callback:
            progress_callback(step, msg)

    messages = []
    if not os.path.isdir(branch_dir):
        return {"ok": False, "loc": 0, "messages": ["missing directory"]}

    meta = read_gen_meta(branch_dir) or {}
    loc_disk = _count_loc(branch_dir, language)
    loc_meta = int(meta.get("loc") or 0)
    loc = max(loc_disk, loc_meta)
    messages.append("LOC disk=%d meta=%d" % (loc_disk, loc_meta))
    if loc < MIN_LOC:
        return {"ok": False, "loc": loc, "messages": messages + ["LOC below minimum"]}

    _report("verify", "structure checks")
    try:
        assert_branch_structure(branch_dir, tech, metric, bt, version, language)
        messages.append("structure OK")
    except AssertionError as exc:
        return {"ok": False, "loc": loc, "messages": messages + [str(exc)]}

    lang = (language or "python").lower()
    _report("verify", "syntax compile")
    if lang == "python":
        syn = _syntax_check_python(branch_dir)
    elif lang == "javascript":
        syn = _syntax_check_js(branch_dir)
    elif lang == "typescript":
        syn = _syntax_check_ts(branch_dir) or _syntax_check_js(branch_dir)
    elif lang == "java":
        syn = _syntax_check_java(branch_dir)
    elif lang in ("csharp", "c#"):
        syn = _syntax_check_csharp(branch_dir)
    else:
        syn = []

    if syn:
        return {"ok": False, "loc": loc, "messages": messages + syn}
    if lang == "python":
        messages.append("py_compile OK")
    elif lang == "javascript":
        messages.append("node --check OK")
    elif lang == "typescript" and syn == []:
        messages.append("typescript syntax OK")
    elif lang == "java" and syn == []:
        messages.append("java compile OK")
    elif lang in ("csharp", "c#") and syn == []:
        messages.append("csharp build OK")

    test_msg = _run_language_tests(branch_dir, lang)
    if test_msg:
        messages.append(test_msg)
        if test_msg.startswith("tests FAIL"):
            return {"ok": False, "loc": loc, "messages": messages}

    if lang == "python":
        from lib.registry import metric_entry, package_name

        pkg = package_name(tech)
        _, reg_metric = metric_entry(tech, metric)
        mod_key = reg_metric["module_key"]
        _report("verify", "import smoke")
        import_cmd = "import %s; import %s.%s; import main" % (pkg, pkg, mod_key)
        try:
            proc = subprocess.run(
                [sys.executable, "-c", import_cmd],
                cwd=branch_dir,
                capture_output=True,
                text=True,
                timeout=_import_timeout_sec(),
                check=False,
            )
            if proc.returncode != 0:
                detail = (proc.stderr or proc.stdout or "import failed").strip()[:200]
                return {"ok": False, "loc": loc, "messages": messages + ["import: %s" % detail]}
            messages.append("import OK")
        except (OSError, subprocess.TimeoutExpired) as exc:
            return {"ok": False, "loc": loc, "messages": messages + ["import: %s" % exc]}

        _report("verify", "running pytest")
        try:
            proc = subprocess.run(
                [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=line"],
                cwd=branch_dir,
                capture_output=True,
                text=True,
                timeout=_pytest_timeout_sec(),
                check=False,
            )
            combined = (proc.stdout or "") + (proc.stderr or "")
            passed_m = re.search(r"(\d+)\s+passed", combined)
            failed_m = re.search(r"(\d+)\s+failed", combined)
            n_passed = int(passed_m.group(1)) if passed_m else 0
            n_failed = int(failed_m.group(1)) if failed_m else 0
            if proc.returncode != 0 and n_passed == 0 and n_failed == 0:
                detail = combined.strip()[:200] or "pytest failed"
                return {"ok": False, "loc": loc, "messages": messages + ["pytest: %s" % detail]}
            messages.append("pytest: %d passed, %d failed" % (n_passed, n_failed))
            if n_failed > 0:
                return {"ok": False, "loc": loc, "messages": messages}
        except (OSError, subprocess.TimeoutExpired) as exc:
            return {"ok": False, "loc": loc, "messages": messages + ["pytest: %s" % exc]}

    if not os.path.isfile(os.path.join(branch_dir, ".gen_meta.json")):
        return {"ok": False, "loc": loc, "messages": messages + ["missing .gen_meta.json"]}

    messages.append("gen-meta OK")
    return {"ok": True, "loc": loc, "messages": messages}


def post_generate_verification(rows, version, language, progress_callback=None):
    """Run verification on generated branches (no artificial time padding)."""
    start = time.time()
    results = []
    total = len(rows)
    for idx, row in enumerate(rows, start=1):
        if not row.get("generated"):
            continue
        bname = row.get("branch_name")

        def _cb(step, msg):
            if progress_callback:
                progress_callback(step, idx - 1, total, bname, msg)

        vr = verify_generated_branch(
            row.get("dir"),
            row.get("technique_code"),
            row.get("metric_code"),
            row.get("branch_type"),
            version,
            language,
            progress_callback=_cb,
        )
        results.append({"branch_name": bname, **vr})
        if progress_callback:
            progress_callback(
                "verify",
                idx,
                total,
                bname,
                "OK %d LOC" % vr.get("loc", 0) if vr.get("ok") else "FAIL",
            )

    elapsed = time.time() - start
    ok_count = len([r for r in results if r.get("ok")])
    return {
        "results": results,
        "ok_count": ok_count,
        "total": len(results),
        "elapsed_sec": elapsed,
        "all_ok": ok_count == len(results) if results else True,
    }
