#!/usr/bin/env python3
"""Validate generated branches against registry-driven asserts."""

from __future__ import print_function

import argparse
import json
import os
import sys

ROOT = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, ROOT)

from lib.validate import BranchValidationError, validate_branch, validate_build, validate_build_full_report  # noqa: E402


def _print_combined_table(rows):
    header = (
        "%-28s %-10s %-11s %-18s %-12s %-22s %-22s"
        % ("Branch", "Structural", "ToolAssert", "Tool", "RawValue", "Expected", "Actual")
    )
    print(header)
    print("-" * len(header))
    for r in rows:
        print(
            "%-28s %-10s %-11s %-18s %-12s %-22s %-22s"
            % (
                r["branch_name"][:28],
                r["structural"],
                r["tool_assert"],
                (r["tool_used"] or "")[:18],
                (r["raw_metric_value"] or "")[:12],
                (r["expected_outcome"] or "")[:22],
                (r["actual_outcome"] or "")[:22],
            )
        )


def _summarize(rows, tool_assert):
    total = len(rows)
    struct_pass = sum(1 for r in rows if r["structural"] == "PASS")
    struct_fail = sum(1 for r in rows if r["structural"] == "FAIL")
    struct_missing = sum(1 for r in rows if r["structural"] == "MISSING")
    print("\n=== Summary ===")
    print("Total branches: %d" % total)
    print("Structural PASS: %d  FAIL: %d  MISSING: %d" % (struct_pass, struct_fail, struct_missing))
    if tool_assert:
        ta_pass = sum(1 for r in rows if r["tool_assert"] == "PASS")
        ta_fail = sum(1 for r in rows if r["tool_assert"] == "FAIL")
        ta_skip = sum(1 for r in rows if r["tool_assert"] == "SKIPPED")
        print("ToolAssert PASS: %d  FAIL: %d  SKIPPED: %d" % (ta_pass, ta_fail, ta_skip))
        by_tech = {}
        for r in rows:
            if r["tool_assert"] not in ("FAIL", "SKIPPED"):
                continue
            tech = r["technique_code"]
            by_tech.setdefault(tech, {"FAIL": 0, "SKIPPED": 0})
            by_tech[tech][r["tool_assert"]] += 1
        if by_tech:
            print("\nToolAssert issues by technique:")
            for tech in sorted(by_tech):
                f = by_tech[tech]["FAIL"]
                s = by_tech[tech]["SKIPPED"]
                if f or s:
                    print("  %s: FAIL=%d SKIPPED=%d" % (tech, f, s))


def main():
    p = argparse.ArgumentParser(description="Validate generated branches")
    p.add_argument("--techniques", default="all")
    p.add_argument("--metrics", default="all")
    p.add_argument("--types", default="Bug,BugFX,TCC,CC")
    p.add_argument("--language", default="python")
    p.add_argument("--version", default="2.6")
    p.add_argument("--build-dir", default="build")
    p.add_argument("--branch", help="Single branch folder name or path")
    p.add_argument("--quick", action="store_true", help="Structural asserts only (default)")
    p.add_argument("--tool-asserts", action="store_true", help="Run structural + tool execution asserts")
    p.add_argument("--parallel", type=int, default=1, help="Parallel workers for tool asserts")
    p.add_argument("--report-json", help="Write combined report JSON to this path")
    p.add_argument("--summary-only", action="store_true", help="Print summary counts only")
    args = p.parse_args()
    types = [t.strip() for t in args.types.split(",")]
    tool_assert = args.tool_asserts and not args.quick

    if args.branch:
        path = args.branch
        if not os.path.isdir(path):
            path = os.path.join(ROOT, args.build_dir, args.branch)
        name, bt, loc = validate_branch(path, version=args.version, language=args.language)
        print("OK  %s (%s) LOC=%d" % (name, bt, loc))
        if tool_assert:
            from lib.tool_assert import tool_assert_branch

            tr = tool_assert_branch(path, language=args.language)
            print(
                "ToolAssert: %s  tool=%s  raw=%s  expected=%s  actual=%s"
                % (
                    tr["status"],
                    tr["tool_used"],
                    tr["raw_metric_value"],
                    tr["expected_outcome"],
                    tr["actual_outcome"],
                )
            )
        return 0

    if tool_assert:
        rows = validate_build_full_report(
            args.techniques,
            args.metrics,
            types,
            args.version,
            args.language,
            args.build_dir,
            ROOT,
            tool_assert=True,
            parallel=max(1, args.parallel),
        )
        if not args.summary_only:
            _print_combined_table(rows)
        _summarize(rows, tool_assert=True)
        if args.report_json:
            out_path = args.report_json
            if not os.path.isabs(out_path):
                out_path = os.path.join(ROOT, out_path)
            os.makedirs(os.path.dirname(out_path) or ROOT, exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as fh:
                json.dump(rows, fh, indent=2)
            print("\nReport written: %s" % out_path)
        failures = [r for r in rows if r["structural"] == "FAIL" or r["tool_assert"] == "FAIL"]
        return 1 if failures else 0

    # Quick / structural only
    results = validate_build(
        args.techniques, args.metrics, types, args.version, args.language, args.build_dir, ROOT)
    print("%-28s %-4s %-4s %-6s %6s  %s" % ("Branch", "Tech", "Met", "Type", "LOC", "Status"))
    print("-" * 70)
    for name, tech, metric, bt, loc, status in results:
        print("%-28s %-4s %-4s %-6s %6d  %s" % (name, tech, metric, bt, loc, status))
    print("\nAll %d branches passed structural validation." % len(results))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BranchValidationError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
