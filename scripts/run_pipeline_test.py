#!/usr/bin/env python3
"""CLI smoke test for pipeline modules (local + compare; sonar if Docker up)."""

from __future__ import print_function

import argparse
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from lib.compare import compare_four_reports  # noqa: E402
from lib.proofs import (  # noqa: E402
    collect_comparison_proof,
    collect_local_batch,
    collect_sonar_batch,
    compare_readiness,
)
from lib.report_schema import load_report, make_report, save_report  # noqa: E402
from lib.sonar_runner import _docker_available, sonar_server_status  # noqa: E402


def _fail(msg):
    print("FAIL:", msg)
    return 1


def main():
    p = argparse.ArgumentParser(description="Pipeline smoke test")
    p.add_argument("--branch", default="SA_Decision-Outcome-Verification_TCC_2.6")
    p.add_argument("--skip-sonar", action="store_true")
    args = p.parse_args()
    branch = args.branch
    errors = []

    print("=== compare_four_reports ===")
    local = make_report("SA", "DOV", branch, "TCC", "2.6", "coverage.py", "local", "FAIL",
                          {"coverage_pct": 4.0}, "4.0%")
    sonar = make_report("SA", "DOV", branch, "TCC", "2.6", "SonarQube", "sonar", "FAIL",
                        {"coverage_pct": 4.0}, "4.0%")
    tax = make_report("SA", "DOV", branch, "TCC", "2.6", "taxonomy", "taxonomy", "PASS", {}, "pass")
    s3 = make_report("SA", "DOV", branch, "TCC", "2.6", "Coverage.py", "s3", "SKIPPED", {}, "skipped")
    cmp = compare_four_reports(tax, s3, local, sonar)
    if cmp.get("verdict") not in ("MATCH", "PARTIAL", "MISMATCH"):
        errors.append("compare_four_reports bad verdict")
    else:
        print("OK verdict=%s" % cmp["verdict"])

    print("=== local batch ===")
    lr = collect_local_batch([branch], root=ROOT, require_whitebox=False)
    if lr[0].get("status") not in ("PASS", "FAIL", "WARN", "SKIPPED"):
        errors.append("local batch: %s" % lr[0])
    else:
        print("OK local status=%s" % lr[0].get("status"))

    print("=== sonar ===")
    docker_ok, docker_msg = _docker_available()
    print("docker:", docker_ok, docker_msg[:120] if docker_msg else "")
    if not args.skip_sonar and docker_ok:
        sr = collect_sonar_batch([branch], root=ROOT, require_whitebox=False)
        if sr[0].get("status") in ("ERROR",) and sr[0].get("error"):
            errors.append("sonar: %s" % sr[0].get("error"))
        else:
            print("OK sonar status=%s" % sr[0].get("status"))
    else:
        print("SKIP sonar (docker unavailable or --skip-sonar)")

    print("=== readiness + compare ===")
    ready = compare_readiness([branch], root=ROOT)[0]
    print("ready:", ready.get("ready"), "missing:", ready.get("missing"))
    if ready.get("ready"):
        c = collect_comparison_proof(branch, root=ROOT)
        print("OK comparison verdict=%s" % c.get("verdict"))
    else:
        print("SKIP comparison (not all reports present)")

    print("=== sonar_server_status ===")
    print(sonar_server_status(root=ROOT))

    if errors:
        for e in errors:
            print("ERROR:", e)
        return 1
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
