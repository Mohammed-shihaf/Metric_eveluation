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
    else:
        syn = []

    if syn:
        return {"ok": False, "loc": loc, "messages": messages + syn}
    if lang == "python":
        messages.append("py_compile OK")
    elif syn is not None and lang == "javascript":
        messages.append("node --check OK")

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
                timeout=60,
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
                timeout=600,
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
