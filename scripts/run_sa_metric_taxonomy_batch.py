#!/usr/bin/env python3
"""
Run metric-scoped SA branches on Testable; one batch exports HTML to taxonomy_reports/.

Default: EPI × 4 types (Bug, BugFX, TCC, CC) in a single run, HTML-only output.

Usage:
  py -3 scripts/run_sa_metric_taxonomy_batch.py --refresh-branches
  py -3 scripts/run_sa_metric_taxonomy_batch.py --metric all
  py -3 scripts/run_sa_metric_taxonomy_batch.py --keep-intermediate
  py -3 scripts/run_sa_metric_taxonomy_batch.py --dry-run --refresh-branches
"""

from __future__ import print_function

import argparse
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

from sa_metrics import BRANCH_TYPES, SA_METRICS, all_metric_branches, branch_name  # noqa: E402


def branches_for_args(metric, branch_types, version):
    if metric == "all":
        abbrevs = [abbrev for _, abbrev, _, _, _ in SA_METRICS]
    else:
        abbrevs = [metric]
    types = list(BRANCH_TYPES) if branch_types == "all" else [t.strip() for t in branch_types.split(",")]
    out = []
    for abbrev in abbrevs:
        for bt in types:
            out.append(branch_name(abbrev, bt, version))
    return out


def verify_html(batch_dir):
    verify_script = os.path.join(ROOT, "scripts", "verify_taxonomy_html.py")
    if not os.path.isfile(verify_script):
        print("  SKIP verify (script not found)", flush=True)
        return 0
    print("\n=== Verify metric differentiation ===", flush=True)
    return subprocess.run(
        [sys.executable, verify_script, "--dir", batch_dir],
        cwd=ROOT,
    ).returncode


def latest_batch_dir(output_root):
    base = os.path.join(ROOT, output_root)
    if not os.path.isdir(base):
        return None
    batches = sorted(
        [d for d in os.listdir(base) if os.path.isdir(os.path.join(base, d))],
        reverse=True,
    )
    return os.path.join(base, batches[0]) if batches else None


def parse_args():
    metric_choices = [abbrev for _, abbrev, _, _, _ in SA_METRICS] + ["all"]
    parser = argparse.ArgumentParser(
        description="Run all 24 metric-scoped SA branches and collect taxonomy reports",
    )
    parser.add_argument("--env-file", default=os.path.join(ROOT, ".env.local"))
    parser.add_argument(
        "--metric",
        choices=metric_choices,
        default="EPI",
        help="Run one metric (EPI, DOV, ...) or all six (default: EPI)",
    )
    parser.add_argument(
        "--branch-types",
        default="all",
        help="Comma-separated: Bug,BugFX,TCC,CC or all (default)",
    )
    parser.add_argument("--version", default="2.6", help="Python version suffix (default 2.6)")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--refresh-branches", action="store_true")
    parser.add_argument("--allow-partial-branches", action="store_true")
    parser.add_argument("--skip-html", action="store_true", help="Do not export HTML after batch")
    parser.add_argument(
        "--keep-intermediate",
        action="store_true",
        help="Keep JSON/XML files (default: HTML-only in taxonomy_reports)",
    )
    parser.add_argument("--skip-verify", action="store_true", help="Do not run HTML verification")
    parser.add_argument(
        "--pair-validate",
        action="store_true",
        help="For each metric: run Bug first, verify target FAIL, then BugFX and verify target PASS",
    )
    return parser.parse_args()


def run_batch(env_file, branches_csv, dry_run, refresh, allow_partial, export_html=True, html_only=True):
    batch_script = os.path.join(ROOT, "scripts", "run_sa_taxonomy_batch.py")
    cmd = [
        sys.executable,
        batch_script,
        "--env-file", env_file,
        "--branches", branches_csv,
    ]
    if dry_run:
        cmd.append("--dry-run")
    if refresh:
        cmd.append("--refresh-branches")
    if allow_partial:
        cmd.append("--allow-partial-branches")
    if export_html:
        cmd.append("--export-html")
    else:
        cmd.append("--no-export-html")
    if html_only:
        cmd.append("--html-only")
    return subprocess.run(cmd, cwd=ROOT)


def pair_validate_metric(env_file, abbrev, version, refresh, allow_partial, skip_html, skip_verify, html_only):
    """Run Bug then BugFX for one metric; validate Bug EPI/target fails before running fix branch."""
    from sa_metrics import branch_name, ABBREV_TO_CLASSIFICATION

    bug_branch = branch_name(abbrev, "Bug", version)
    fix_branch = branch_name(abbrev, "BugFX", version)
    target_cls = ABBREV_TO_CLASSIFICATION[abbrev]

    print("\n=== Pair validation: %s ===" % abbrev, flush=True)
    print("  [1/2] %s (expect %s FAIL)" % (bug_branch, target_cls), flush=True)
    rc = run_batch(env_file, bug_branch, False, refresh, allow_partial,
                   export_html=not skip_html, html_only=html_only)
    if rc.returncode != 0:
        return rc.returncode

    batch_dir = latest_batch_dir(os.environ.get("OUTPUT_DIR", "taxonomy_reports"))
    if batch_dir:
        bug_html = glob_html(batch_dir, bug_branch)
        if bug_html:
            ok, detail = verify_one(bug_html, abbrev, "Bug")
            print(detail)
            if not ok:
                print("STOP: Bug branch did not fail target metric — fix branch code before BugFX run.", flush=True)
                return 1
        else:
            print("WARNING: no HTML for %s — check taxonomy JSON manually" % bug_branch, flush=True)

    print("  [2/2] %s (expect %s PASS/WARN)" % (fix_branch, target_cls), flush=True)
    rc = run_batch(env_file, fix_branch, False, refresh, allow_partial,
                   export_html=not skip_html, html_only=html_only)
    if rc.returncode != 0:
        return rc.returncode
    batch_dir = latest_batch_dir(os.environ.get("OUTPUT_DIR", "taxonomy_reports"))
    if batch_dir and not skip_verify:
        fix_html = glob_html(batch_dir, fix_branch)
        if fix_html:
            ok, detail = verify_one(fix_html, abbrev, "BugFX")
            print(detail)
            if not ok:
                return 1
    return 0


def glob_html(batch_dir, branch_name):
    folder = os.path.join(batch_dir, branch_name)
    if not os.path.isdir(folder):
        return None
    for fn in os.listdir(folder):
        if fn.endswith(".html"):
            return os.path.join(folder, fn)
    return None


def verify_one(html_path, abbrev, branch_type):
    from verify_taxonomy_html import verify_file
    return verify_file(html_path, abbrev, branch_type)


def main():
    args = parse_args()
    if os.path.isfile(args.env_file):
        with open(args.env_file, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line.startswith("OUTPUT_DIR="):
                    os.environ.setdefault("OUTPUT_DIR", line.split("=", 1)[1].strip())

    html_only = not args.keep_intermediate

    if args.pair_validate:
        abbrevs = [abbrev for _, abbrev, _, _, _ in SA_METRICS] if args.metric == "all" else [args.metric]
        for abbrev in abbrevs:
            rc = pair_validate_metric(
                args.env_file, abbrev, args.version,
                args.refresh_branches, args.allow_partial_branches,
                args.skip_html, args.skip_verify, html_only,
            )
            if rc != 0:
                return rc
        print("\n=== Pair validation complete ===", flush=True)
        return 0

    branches = branches_for_args(args.metric, args.branch_types, args.version)
    branches_csv = ",".join(branches)

    print("=== SA metric taxonomy batch ===", flush=True)
    print("  metrics: %s" % (args.metric if args.metric != "all" else "EPI,DOV,LSV,TLCC,TDI,QRA"))
    print("  types:   %s" % (args.branch_types if args.branch_types != "all" else "Bug,BugFX,TCC,CC"))
    print("  count:   %d branches" % len(branches), flush=True)
    for i, name in enumerate(branches, 1):
        print("    %2d. %s" % (i, name))

    print("\n=== Starting whitebox runs ===", flush=True)
    result = run_batch(
        args.env_file, branches_csv, args.dry_run,
        args.refresh_branches, args.allow_partial_branches,
        export_html=not args.skip_html,
        html_only=html_only,
    )
    if result.returncode != 0:
        return result.returncode

    if args.dry_run:
        return 0

    batch_dir = latest_batch_dir(os.environ.get("OUTPUT_DIR", "taxonomy_reports"))
    if not batch_dir:
        print("WARNING: no batch output directory found", flush=True)
        return 0

    print("\n  batch output: %s" % batch_dir, flush=True)

    if not args.skip_verify:
        verify_rc = verify_html(batch_dir)
        if verify_rc != 0:
            print("\nWARNING: verification reported issues (see above)", flush=True)

    print("\n=== Metric batch complete ===", flush=True)
    print("  reports: %s" % batch_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
