"""Verify one branch per tool family executes with require_real_tool=True."""
from __future__ import print_function

import json
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from lib.tool_env import ensure_tool_env
from lib.tool_map import all_tool_packages

WORK = os.path.join(ROOT, ".pipeline_work", "default")

BRANCHES = {
    "crosshair": "SA_Execution-Path-Integrity_Bug_2.6",
    "mutation": "MU_Logic-Error-Sensitivity_BugFX_2.6",
    "sca": "DR_Community-Vitality-Tracking_Bug_2.6",
    "churn": "DP_Code-Churn-Score_Bug_2.6",
    "security": "SX_Access-Control-Verification_Bug_2.6",
    "beniget": "DF_All-Defs-Coverage_Bug_2.6",
    "testmon": "SA_QA-Resource-Allocation_Bug_2.6",
    "coverage": "SA_Decision-Outcome-Verification_Bug_2.6",
    "complexity": "RM_Unit-Test-Complexity_Bug_2.6",
    "lint": "LR_Violation-Density-Per-KLOC_Bug_2.6",
    "duplication": "CQ_Multi-Point-Failure-Probability_Bug_2.6",
    "pymcdc": "SA_Logical-Sub-Expression-Validation_Bug_2.6",
}

WORKER = """
import json, os, sys
sys.path.insert(0, os.environ["REPO"])
from lib.tool_assert import tool_assert_branch
res = tool_assert_branch(os.environ["BRANCH"], require_real_tool=True)
print(json.dumps({k: res.get(k) for k in ("status", "real_tool", "tool_used", "message")}))
"""


def main():
    session = ensure_tool_env(all_tool_packages())
    python = session["python_exe"]
    failures = []
    for fam, bname in BRANCHES.items():
        path = os.path.join(WORK, bname)
        if not os.path.isdir(path):
            print("%-12s MISSING %s" % (fam, bname))
            failures.append((fam, "MISSING"))
            continue
        env = os.environ.copy()
        env["REPO"] = ROOT
        env["BRANCH"] = path
        proc = subprocess.run(
            [python, "-c", WORKER],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=7200,
            env=env,
            check=False,
        )
        if proc.returncode != 0:
            print("%-12s WORKER_FAIL %s" % (fam, (proc.stderr or proc.stdout)[:200]))
            failures.append((fam, "WORKER_FAIL"))
            continue
        line = (proc.stdout or "").strip().splitlines()[-1]
        data = json.loads(line)
        ok = data["status"] not in ("UNAVAILABLE", "ERROR") and data.get("real_tool") is True
        print(
            "%-12s %-12s real=%s tool=%s"
            % (fam, data["status"], data.get("real_tool"), data.get("tool_used"))
        )
        if not ok:
            failures.append((fam, data))
    print("---")
    if failures:
        print("FAILURES:", failures)
        return 1
    print("ALL 12 FAMILIES EXECUTED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
