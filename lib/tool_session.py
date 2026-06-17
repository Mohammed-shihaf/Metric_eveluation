"""Throwaway and persistent virtual-environment sessions for local tool runs."""

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
        "persistent": False,
    }


def install_packages(session, packages, timeout=600, retries=1):
    """Install pip packages into the session venv.

    Returns a structured dict:
      {ok, installed, skipped, failed, logs, message}
    """
    from lib.tool_env import install_packages_strict

    return install_packages_strict(session, packages, timeout=timeout, retries=retries)


def install_packages_legacy(session, packages, timeout=600):
    """Backward-compatible wrapper returning (ok, message)."""
    result = install_packages(session, packages, timeout=timeout)
    return result.get("ok", False), result.get("message", "")


def destroy_session(session):
    """Remove the venv directory and all installed tools."""
    if not session:
        return
    if session.get("persistent"):
        return
    venv_dir = session.get("venv_dir")
    if venv_dir and os.path.isdir(venv_dir):
        shutil.rmtree(venv_dir, ignore_errors=True)
