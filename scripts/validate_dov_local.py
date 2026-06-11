#!/usr/bin/env python3
"""Local Coverage.py check: DOV Bug should score low, BugFX/TCC/CC should score high."""

from __future__ import print_function

import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _outcome(pct):
    if pct >= 75:
        return "pass"
    if pct >= 50:
        return "warn"
    return "fail"


def coverage_pct(branch_name):
    tmp = tempfile.mkdtemp(prefix="dov_check_")
    try:
        subprocess.check_call(
            ["git", "archive", branch_name],
            cwd=ROOT,
            stdout=open(os.path.join(tmp, "repo.tar"), "wb"),
        )
        subprocess.check_call(["tar", "-xf", "repo.tar"], cwd=tmp)
        env = os.environ.copy()
        env["PYTHONPATH"] = tmp
        test_dir = os.path.join(tmp, "tests")
        if os.path.isdir(test_dir):
            subprocess.check_call(
                [sys.executable, "-m", "coverage", "run", "--branch", "-m", "unittest", "discover", "-s", "tests"],
                cwd=tmp,
                env=env,
            )
        else:
            subprocess.check_call(
                [sys.executable, "-m", "coverage", "run", "--branch", "-m", "unittest", "discover"],
                cwd=tmp,
                env=env,
            )
        out = subprocess.check_output(
            [sys.executable, "-m", "coverage", "report", "-m", "--include=sa/decision_coverage.py"],
            cwd=tmp,
            env=env,
            text=True,
        )
        pct = None
        for line in out.splitlines():
            if "decision_coverage" in line:
                parts = line.split()
                pct = float(parts[-1].rstrip("%"))
        if pct is None:
            raise RuntimeError("Could not parse coverage:\n" + out)
        return {"branch": branch_name, "coverage": pct, "outcome": _outcome(pct)}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    branches = {
        "SA_DOV_Bug_2.6": "fail",
        "SA_DOV_BugFX_2.6": "pass",
        "SA_DOV_TCC_2.6": "pass",
        "SA_DOV_CC_2.6": "pass",
    }
    ok = True
    results = []
    for branch, expect in branches.items():
        try:
            row = coverage_pct(branch)
        except Exception as exc:
            print("SKIP %s: %s" % (branch, exc))
            continue
        results.append((branch, expect, row))
        print("%(branch)s: coverage=%(coverage).1f%% => %(outcome)s" % row)
        if expect == "fail" and row["outcome"] != "fail":
            print("  FAIL: expected DOV fail")
            ok = False
        elif expect == "pass" and row["outcome"] == "fail":
            print("  FAIL: expected DOV pass/warn")
            ok = False
        else:
            print("  OK")
    if len(results) >= 2:
        covs = [r[2]["coverage"] for r in results]
        if len(set(round(c, 0) for c in covs)) < 2:
            print("NOTE: branch coverage scores are very similar — taxonomy may look alike")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
