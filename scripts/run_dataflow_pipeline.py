#!/usr/bin/env python3
"""Data Flow Testing end-to-end: generate scope, validate build, QA batch, S3 sync."""

from __future__ import print_function

import argparse
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

DEFAULT_CLASSIFICATION = "Data Flow Testing"
DEFAULT_CLASSIFICATION_DIR = os.path.join(ROOT, "taxonomy_reports", DEFAULT_CLASSIFICATION)


def _list_branches(techniques, metrics, version):
    from lib.registry import iter_branches

    return [bname for _tech, _metric, _bt, bname in iter_branches(techniques, metrics, version=version)]


def _validate_builds(build_root, branches):
    from lib.tool_assert import tool_assert_branch

    print("\n=== Build tool_assert (repo-side) ===")
    rows = []
    for branch in branches:
        path = os.path.join(build_root, branch)
        if not os.path.isdir(path):
            print("  MISSING build/%s" % branch)
            rows.append({"branch": branch, "status": "MISSING"})
            continue
        tr = tool_assert_branch(path)
        print("  %s -> %s (%s) %s" % (
            branch, tr.get("status"), tr.get("actual_outcome"), tr.get("raw_metric_value")))
        rows.append(tr)
    return rows


def _run_qa_batch(env_file, branches, dry_run=False):
    from lib.sa_qa import run_taxonomy_batch

    print("\n=== Platform QA batch (taxonomy) ===")
    rc, output_dir = run_taxonomy_batch(
        env_file=env_file,
        branches_csv=",".join(branches),
        dry_run=dry_run,
        refresh_branches=True,
        export_html=True,
        html_only=True,
    )
    print("  exit=%s output=%s" % (rc, output_dir))
    return rc, output_dir


def main():
    parser = argparse.ArgumentParser(description="Run Data Flow Testing pipeline")
    parser.add_argument("--env-file", default=os.path.join(ROOT, ".env.local"))
    parser.add_argument("--build-root", default=os.path.join(ROOT, "build"))
    parser.add_argument("--techniques", default="DF", help="Registry technique codes (csv), default DF")
    parser.add_argument("--metrics", default="all", help="Metric filter or 'all'")
    parser.add_argument("--version", default="2.6")
    parser.add_argument(
        "--classification-dir",
        default=DEFAULT_CLASSIFICATION_DIR,
    )
    parser.add_argument("--generate", action="store_true", help="Generate branches under build/")
    parser.add_argument("--git", action="store_true", help="Create local git branches from build/")
    parser.add_argument("--push", action="store_true", help="Push branches to origin (implies --git)")
    parser.add_argument("--run-qa", action="store_true", help="Run Testable QA batch (needs credentials)")
    parser.add_argument("--qa-dry-run", action="store_true", help="Catalog-only QA dry run")
    parser.add_argument("--sync", action="store_true", help="Backfill S3 downloads from taxonomy")
    parser.add_argument("--all", action="store_true", help="generate + git + run-qa + sync")
    args = parser.parse_args()

    if args.push:
        args.git = True
    if args.all:
        args.generate = True
        args.git = True
        args.run_qa = True
        args.sync = True

    from lib.sa_qa import load_env

    load_env(args.env_file)
    os.environ["REPORT_CLASSIFICATION"] = DEFAULT_CLASSIFICATION
    os.environ["S3_SYNC_BRANCH_PREFIX"] = "DF_"

    techniques = [t.strip() for t in args.techniques.split(",") if t.strip()]
    branches = _list_branches(",".join(techniques), args.metrics, args.version)
    if not branches:
        print("ERROR: no branches matched techniques=%s metrics=%s" % (args.techniques, args.metrics))
        return 1

    print("Data Flow Testing pipeline")
    print("  classification: %s" % os.environ.get("REPORT_CLASSIFICATION"))
    print("  branches (%d): %s" % (len(branches), ", ".join(branches[:4]) + (" ..." if len(branches) > 4 else "")))

    rc = 0

    if args.generate:
        from lib.generator import generate_branches
        from lib.validate import validate_build

        print("\n=== Generate branches ===")
        names, gen_errors = generate_branches(
            ",".join(techniques), args.metrics, version=args.version,
            build_dir=os.path.basename(args.build_root.rstrip("/\\")), repo_root=ROOT,
        )
        if gen_errors:
            for err in gen_errors:
                print("  ERROR %s: %s" % (err["branch"], err["error"]))
            rc = max(rc, 1)
        else:
            validate_build(
                ",".join(techniques), args.metrics, version=args.version,
                build_dir=os.path.basename(args.build_root.rstrip("/\\")), repo_root=ROOT,
            )
            print("  validated %d branches" % len(names))

    if args.git:
        from lib.generator import create_git_branches, push_branches

        print("\n=== Create git branches ===")
        create_git_branches(
            ",".join(techniques), args.metrics, version=args.version,
            repo_root=ROOT, build_dir=os.path.basename(args.build_root.rstrip("/\\")),
        )
        if args.push:
            print("\n=== Push branches ===")
            push_branches(branches, ROOT)

    _validate_builds(args.build_root, branches)

    if args.run_qa or args.qa_dry_run:
        os.environ["BRANCHES"] = ",".join(branches)
        qa_rc, _ = _run_qa_batch(args.env_file, branches, dry_run=args.qa_dry_run)
        rc = max(rc, qa_rc)

    if args.sync:
        from lib.s3_sync import backfill_missing

        print("\n=== S3 backfill ===")
        summaries = backfill_missing(args.classification_dir)
        for s in summaries:
            print("  %s: %s" % (s.get("branch"), s.get("status")))
        if any(s.get("status") not in ("OK",) and not s.get("skipped") for s in summaries):
            rc = max(rc, 1)

    if not (args.generate or args.git or args.run_qa or args.qa_dry_run or args.sync or args.all):
        parser.print_help()
        return 0
    return rc


if __name__ == "__main__":
    sys.exit(main())
