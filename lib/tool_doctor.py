"""Preflight capability checks for all tool families."""

from __future__ import print_function

import json
import os
import subprocess
import sys

from lib.tool_assert import RUNNERS
from lib.tool_env import ROOT, ensure_tool_env
from lib.tool_map import all_tool_packages

DOCTOR_OUTPUT = os.path.join(ROOT, "proofs", "_doctor", "capability.json")


def _run_smoke(python_exe, cmd, cwd, env, timeout=60):
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
        combined = ((proc.stdout or "") + (proc.stderr or "")).strip()
        return proc.returncode == 0, combined[:500]
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, str(exc)


def _import_smoke(python_exe, module, env):
    ok, out = _run_smoke(
        python_exe,
        [python_exe, "-c", "import %s; print('ok')" % module],
        cwd=ROOT,
        env=env,
        timeout=30,
    )
    return ok, out


def _family_smoke(family, python_exe, env):
    checks = {
        "coverage": ([python_exe, "-m", "coverage", "--version"], None),
        "crosshair": ([python_exe, "-m", "crosshair", "--help"], None),
        "pymcdc": (None, "pymcdc"),
        "complexity": ([python_exe, "-m", "radon", "--version"], "radon"),
        "lint": ([python_exe, "-m", "flake8", "--version"], "flake8"),
        "security": ([python_exe, "-m", "bandit", "--version"], "bandit"),
        "sca": ([python_exe, "-m", "pip_audit", "--version"], "pip_audit"),
        "mutation": ([python_exe, "-m", "cosmic_ray.cli", "--help"], "cosmic_ray"),
        "churn": (None, "pydriller"),
        "duplication": (None, "copydetect"),
        "testmon": ([python_exe, "-m", "pytest", "--version"], "testmon"),
        "beniget": (None, "beniget"),
    }
    cmd, import_mod = checks.get(family, (None, None))
    if import_mod:
        ok, detail = _import_smoke(python_exe, import_mod, env)
        return ok, ok, detail
    if cmd:
        ok, detail = _run_smoke(python_exe, cmd, ROOT, env, timeout=60)
        return ok, ok, detail
    return False, False, "no smoke check defined"


def run_tool_doctor(packages=None, cache_root=None, persist=True):
    """Build/reuse tool env and smoke-test each family in RUNNERS."""
    packages = packages or all_tool_packages()
    session = ensure_tool_env(packages, cache_root=cache_root)
    python_exe = session["python_exe"]
    env = session.get("env")
    install_result = session.get("install_result") or {}

    families = sorted(RUNNERS.keys())
    matrix = {
        "env_key": session.get("env_key", ""),
        "venv_dir": session.get("venv_dir", ""),
        "install": {
            "ok": install_result.get("ok", True),
            "installed": install_result.get("installed", []),
            "skipped": install_result.get("skipped", []),
            "failed": install_result.get("failed", []),
            "message": install_result.get("message", ""),
        },
        "families": {},
        "all_runnable": True,
    }

    for family in families:
        installed, runnable, detail = _family_smoke(family, python_exe, env)
        if family == "security":
            semgrep_ok, semgrep_detail = _run_smoke(
                python_exe,
                ["semgrep", "--version"],
                ROOT,
                env,
                timeout=30,
            )
            detail = detail + ("; semgrep=%s" % ("ok" if semgrep_ok else semgrep_detail[:120]))
        if family == "duplication":
            jscpd_ok, jscpd_detail = _run_smoke(
                python_exe,
                ["jscpd", "--version"],
                ROOT,
                env,
                timeout=30,
            )
            detail = detail + ("; jscpd=%s" % ("ok" if jscpd_ok else "fallback-copydetect"))
        entry = {
            "installed": bool(installed),
            "runnable": bool(runnable),
            "version": detail[:300],
            "error": "" if runnable else detail[:300],
        }
        matrix["families"][family] = entry
        if not runnable:
            matrix["all_runnable"] = False

    if persist:
        os.makedirs(os.path.dirname(DOCTOR_OUTPUT), exist_ok=True)
        with open(DOCTOR_OUTPUT, "w", encoding="utf-8") as fh:
            json.dump(matrix, fh, indent=2)
        matrix["path"] = DOCTOR_OUTPUT

    matrix["session"] = session
    return matrix


def load_capability_matrix():
    if not os.path.isfile(DOCTOR_OUTPUT):
        return None
    try:
        with open(DOCTOR_OUTPUT, encoding="utf-8") as fh:
            return json.load(fh)
    except (ValueError, OSError, TypeError):
        return None
