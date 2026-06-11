#!/usr/bin/env python3
"""Create all metric-scoped SA git branches (Bug, BugFX, TCC, CC × 6 metrics)."""

from __future__ import print_function

import os
import shutil
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

from sa_metrics import all_metric_branches  # noqa: E402

KEEP = {".git", "build", "scripts", ".gitignore"}


def run(cmd, cwd=ROOT):
    print("+", " ".join(cmd))
    subprocess.check_call(cmd, cwd=cwd)


def clean_worktree():
    for name in os.listdir(ROOT):
        if name in KEEP:
            continue
        path = os.path.join(ROOT, name)
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)


def deploy_branch(branch):
    clean_worktree()
    src = os.path.join(ROOT, "build", branch)
    if not os.path.isdir(src):
        raise RuntimeError("Missing build output: %s (run generate_sa_metric_codebase.py first)" % src)
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(ROOT, item)
        if os.path.isdir(s):
            shutil.copytree(s, d)
        else:
            shutil.copy2(s, d)
    add_paths = ["sa", "tests", "README.md", "main.py", "requirements.txt", "versions.txt"]
    for optional in (".coveragerc", ".testmondata.ini", "pytest.ini", "setup.cfg"):
        if os.path.exists(os.path.join(ROOT, optional)):
            add_paths.append(optional)
    run(["git", "add", "-A"] + add_paths)
    run(["git", "commit", "-m", "Add metric-scoped SA %s Python 2.6 codebase" % branch])


def main():
    branches = all_metric_branches()
    for branch in branches:
        run(["git", "checkout", "-B", branch, "main"])
        deploy_branch(branch)
    run(["git", "checkout", "main"])
    print("Created %d branches" % len(branches))


if __name__ == "__main__":
    main()
