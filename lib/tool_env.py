"""Persistent, pre-validated virtual environments for local tool execution."""

from __future__ import print_function

import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import venv

from lib.tool_session import _venv_paths

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_CACHE_ROOT = os.path.join(ROOT, ".tool_env")


def _normalize_packages(packages):
    pkgs = list(dict.fromkeys(list(packages or []) + ["pyyaml"]))
    if "pytest" in " ".join(pkgs).lower() and not any("pytest>=" in p for p in pkgs):
        pkgs = [p if p != "pytest" else "pytest>=7.0.0" for p in pkgs]
    return pkgs


def _package_hash(packages):
    normalized = sorted(_normalize_packages(packages))
    digest = hashlib.sha256("\n".join(normalized).encode("utf-8")).hexdigest()
    return digest[:16]


def _manifest_path(env_dir):
    return os.path.join(env_dir, "manifest.json")


def _load_manifest(env_dir):
    path = _manifest_path(env_dir)
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (ValueError, OSError, TypeError):
        return {}


def _save_manifest(env_dir, packages, installed, failed, logs):
    data = {
        "packages_requested": sorted(_normalize_packages(packages)),
        "installed": sorted(installed),
        "failed": sorted(failed),
        "logs": logs[-50:],
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "python_exe": os.path.join(env_dir, "Scripts", "python.exe")
        if sys.platform == "win32"
        else os.path.join(env_dir, "bin", "python"),
    }
    with open(_manifest_path(env_dir), "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
    return data


def _module_for_package(pkg):
    base = pkg.split(">=")[0].split("==")[0].strip().lower()
    aliases = {
        "pip_audit": "pip_audit",
        "pip-audit": "pip_audit",
        "cosmic_ray": "cosmic_ray",
        "cosmic-ray": "cosmic_ray",
        "crosshair_tool": "crosshair",
        "crosshair-tool": "crosshair",
        "pytest_testmon": "testmon",
        "pytest-testmon": "testmon",
        "pyyaml": "yaml",
    }
    if base in aliases:
        return aliases[base]
    return base.replace("-", "_")


def _package_importable(session, pkg):
    mod = _module_for_package(pkg)
    cmd = [session["python_exe"], "-c", "import %s" % mod]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
            env=session.get("env"),
        )
        return proc.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def _create_persistent_venv(env_dir):
    os.makedirs(os.path.dirname(env_dir), exist_ok=True)
    if os.path.isdir(env_dir):
        return
    builder = venv.EnvBuilder(with_pip=True, clear=True)
    builder.create(env_dir)
    scripts_dir, python_exe = _venv_paths(env_dir)
    if not os.path.isfile(python_exe):
        shutil.rmtree(env_dir, ignore_errors=True)
        raise RuntimeError("persistent venv python not found: %s" % python_exe)


def _session_from_env_dir(env_dir):
    scripts_dir, python_exe = _venv_paths(env_dir)
    if not os.path.isfile(python_exe):
        raise RuntimeError("venv python missing: %s" % python_exe)
    env = os.environ.copy()
    path_key = "PATH"
    old_path = env.get(path_key, "")
    env[path_key] = scripts_dir + os.pathsep + old_path if old_path else scripts_dir
    env["VIRTUAL_ENV"] = env_dir
    return {
        "venv_dir": env_dir,
        "python_exe": python_exe,
        "scripts_dir": scripts_dir,
        "env": env,
        "persistent": True,
        "env_key": os.path.basename(env_dir),
    }


def _pip_install_one(session, pkg, timeout=600, retries=2):
    logs = []
    for attempt in range(1, retries + 2):
        cmd = [
            session["python_exe"],
            "-m",
            "pip",
            "install",
            "--no-input",
            "--disable-pip-version-check",
            pkg,
        ]
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
                env=session.get("env"),
            )
            log = (proc.stdout or "") + (proc.stderr or "")
            if proc.returncode == 0:
                return True, log.strip()
            logs.append("attempt %d: %s" % (attempt, log.strip() or "pip exit %d" % proc.returncode))
        except (OSError, subprocess.TimeoutExpired) as exc:
            logs.append("attempt %d: %s" % (attempt, exc))
    return False, "; ".join(logs)


def install_packages_strict(session, packages, timeout=600, retries=2):
    """Install packages into session venv with retries. Returns structured result."""
    pkgs = _normalize_packages(packages)
    installed = []
    failed = []
    logs = []
    skipped = []

    for pkg in pkgs:
        if _package_importable(session, pkg):
            skipped.append(pkg)
            continue
        ok, log = _pip_install_one(session, pkg, timeout=timeout, retries=retries)
        if ok and _package_importable(session, pkg):
            installed.append(pkg)
        else:
            failed.append(pkg)
            if log:
                logs.append("%s: %s" % (pkg, log))

    all_ok = not failed
    message_parts = []
    if installed:
        message_parts.append("installed: %s" % ", ".join(installed))
    if skipped:
        message_parts.append("already present: %s" % ", ".join(skipped))
    if failed:
        message_parts.append("failed: %s" % ", ".join(failed))
    message = "; ".join(message_parts) if message_parts else "no packages requested"

    return {
        "ok": all_ok,
        "installed": installed,
        "skipped": skipped,
        "failed": failed,
        "logs": logs,
        "message": message,
    }


def ensure_tool_env(packages, cache_root=None, timeout=600, retries=2, force_reinstall=False):
    """Create or reuse a persistent venv keyed by package-set hash."""
    cache_root = cache_root or DEFAULT_CACHE_ROOT
    env_key = _package_hash(packages)
    env_dir = os.path.join(cache_root, env_key)

    if force_reinstall and os.path.isdir(env_dir):
        shutil.rmtree(env_dir, ignore_errors=True)

    _create_persistent_venv(env_dir)
    session = _session_from_env_dir(env_dir)
    install_result = install_packages_strict(session, packages, timeout=timeout, retries=retries)
    manifest = _save_manifest(
        env_dir,
        packages,
        install_result.get("installed", []) + install_result.get("skipped", []),
        install_result.get("failed", []),
        install_result.get("logs", []),
    )
    session["manifest"] = manifest
    session["install_result"] = install_result
    session["env_key"] = env_key
    return session


def destroy_tool_env(session):
    """Remove a persistent tool environment (explicit clean only)."""
    if not session:
        return
    venv_dir = session.get("venv_dir")
    if venv_dir and os.path.isdir(venv_dir) and session.get("persistent"):
        shutil.rmtree(venv_dir, ignore_errors=True)


def env_info(session):
    """Return a small dict describing the active tool environment."""
    if not session:
        return {}
    manifest = session.get("manifest") or _load_manifest(session.get("venv_dir", ""))
    install_result = session.get("install_result") or {}
    return {
        "venv_dir": session.get("venv_dir", ""),
        "env_key": session.get("env_key", ""),
        "persistent": bool(session.get("persistent")),
        "installed": manifest.get("installed", install_result.get("installed", [])),
        "failed": manifest.get("failed", install_result.get("failed", [])),
        "message": install_result.get("message", ""),
    }
