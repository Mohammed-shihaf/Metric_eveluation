"""Throwaway virtual-environment sessions for isolated local tool runs."""

from __future__ import print_function

import os
import shutil
import subprocess
import sys
import tempfile
import venv


def _venv_paths(venv_dir):
    if sys.platform == "win32":
        scripts = os.path.join(venv_dir, "Scripts")
        python_exe = os.path.join(scripts, "python.exe")
    else:
        scripts = os.path.join(venv_dir, "bin")
        python_exe = os.path.join(scripts, "python")
    return scripts, python_exe


def create_session(workdir=None):
    """Create a temporary venv. Returns session dict or raises on failure."""
    base = workdir or tempfile.gettempdir()
    venv_dir = tempfile.mkdtemp(prefix="tas_session_", dir=base)
    builder = venv.EnvBuilder(with_pip=True, clear=True)
    builder.create(venv_dir)
    scripts_dir, python_exe = _venv_paths(venv_dir)
    if not os.path.isfile(python_exe):
        shutil.rmtree(venv_dir, ignore_errors=True)
        raise RuntimeError("venv python not found: %s" % python_exe)
    env = os.environ.copy()
    path_key = "PATH"
    old_path = env.get(path_key, "")
    env[path_key] = scripts_dir + os.pathsep + old_path if old_path else scripts_dir
    env["VIRTUAL_ENV"] = venv_dir
    return {
        "venv_dir": venv_dir,
        "python_exe": python_exe,
        "scripts_dir": scripts_dir,
        "env": env,
    }


def install_packages(session, packages, timeout=600):
    """Install pip packages into the session venv. Returns (ok, log)."""
    pkgs = list(dict.fromkeys(list(packages or []) + ["pyyaml"]))
    if "pytest" in " ".join(pkgs).lower() and not any("pytest>=" in p for p in pkgs):
        # ensure modern pytest when coverage family needs it
        if "pytest" in pkgs:
            pkgs = [p if p != "pytest" else "pytest>=7.0.0" for p in pkgs]
    cmd = [session["python_exe"], "-m", "pip", "install", "--quiet"] + pkgs
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
        if proc.returncode != 0:
            return False, log.strip() or "pip install failed (exit %d)" % proc.returncode
        return True, "installed: %s" % ", ".join(pkgs)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, str(exc)


def destroy_session(session):
    """Remove the venv directory and all installed tools."""
    if not session:
        return
    venv_dir = session.get("venv_dir")
    if venv_dir and os.path.isdir(venv_dir):
        shutil.rmtree(venv_dir, ignore_errors=True)
