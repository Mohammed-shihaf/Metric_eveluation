#!/usr/bin/env python3
"""Resumable all-tools sweep: generate full matrix, run real tools, classify failures."""

from __future__ import print_function

import argparse
import json
import os
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from lib.branch_diagnostics import build_diagnostics  # noqa: E402
from lib.branch_pipeline import pipeline_work_dir  # noqa: E402
from lib.lang_generators import write_branch  # noqa: E402
from lib.proofs import collect_local_batch  # noqa: E402
from lib.registry import iter_branches  # noqa: E402

SWEEP_DIR = os.path.join(ROOT, "proofs", "_sweep")
CHECKPOINT_PATH = os.path.join(SWEEP_DIR, "checkpoint.json")

# One metric per tool family for fast iteration (12 metrics x 4 types = 48 branches).
FAMILY_SUBSET = [
    ("SA", "DOV"),   # coverage
    ("SA", "EPI"),   # crosshair
    ("SA", "LSV"),   # pymcdc
    ("SA", "TDI"),   # complexity
    ("SA", "QRA"),   # testmon
    ("MU", "LES"),   # mutation
    ("LR", "VDK"),   # lint
    ("SX", "BPC"),   # security
    ("DR", "HRM"),   # sca
    ("DP", "CCS"),   # churn
    ("CQ", "MPFP"),  # duplication
    ("DF", "DECO"),  # beniget
]


def _load_checkpoint():
    if not os.path.isfile(CHECKPOINT_PATH):
        return {"generated": [], "executed": [], "updated_at": ""}
    try:
        with open(CHECKPOINT_PATH, encoding="utf-8") as fh:
            return json.load(fh)
    except (ValueError, OSError, TypeError):
        return {"generated": [], "executed": [], "updated_at": ""}


def _save_checkpoint(checkpoint):
    os.makedirs(SWEEP_DIR, exist_ok=True)
    checkpoint["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with open(CHECKPOINT_PATH, "w", encoding="utf-8") as fh:
        json.dump(checkpoint, fh, indent=2)


def _branch_list(techniques, metrics, types, version, family_subset=False):
    branches = []
    if family_subset:
        type_list = [t.strip() for t in types.split(",") if t.strip()] if isinstance(types, str) else list(types)
        from lib.metrics import branch_name
        for tech, metric in FAMILY_SUBSET:
            for bt in type_list:
                bname = branch_name(tech, metric, bt, version)
                branches.append({
                    "branch_name": bname,
                    "technique_code": tech,
                    "metric_code": metric,
                    "branch_type": bt,
                    "version": version,
                })
        return branches
    for tech, metric, bt, bname in iter_branches(techniques, metrics, types, version):
        branches.append({
            "branch_name": bname,
            "technique_code": tech,
            "metric_code": metric,
            "branch_type": bt,
            "version": version,
        })
    return branches


def _sort_for_execution(branches):
    """Run mutation (MU) branches last."""
    fast = [b for b in branches if b["technique_code"] != "MU"]
    slow = [b for b in branches if b["technique_code"] == "MU"]
    return fast + slow


def _report_exists(bname):
    parts = bname.split("_", 1)
    tech = parts[0] if parts else "?"
    path = os.path.join(ROOT, "proofs", tech, bname, "local_report.json")
    return os.path.isfile(path)


def _progress(phase, idx, total, branch, msg):
    print("[%s %d/%d] %s — %s" % (phase, idx, total, branch or "-", msg), flush=True)


def phase_generate(branches, work_root, force=False, checkpoint=None, strength=0):
    checkpoint = checkpoint or _load_checkpoint()
    generated = set(checkpoint.get("generated") or [])
    total = len(branches)
    created = 0
    skipped = 0

    for idx, row in enumerate(branches, start=1):
        bname = row["branch_name"]
        branch_dir = os.path.join(work_root, bname)
        if os.path.isdir(branch_dir) and not force and bname in generated:
            skipped += 1
            _progress("generate", idx, total, bname, "skip (exists)")
            continue
        try:
            write_branch(
                branch_dir,
                row["technique_code"],
                row["metric_code"],
                row["branch_type"],
                row["version"],
                "python",
                strength=strength,
            )
            generated.add(bname)
            created += 1
            _progress("generate", idx, total, bname, "written")
        except Exception as exc:
            _progress("generate", idx, total, bname, "ERROR: %s" % exc)

    checkpoint["generated"] = sorted(generated)
    _save_checkpoint(checkpoint)
    print("Generate done: created=%d skipped=%d total=%d" % (created, skipped, total))
    return checkpoint


def phase_run_tools(branches, work_root, chunk_size=10, skip_existing=False, checkpoint=None):
    checkpoint = checkpoint or _load_checkpoint()
    executed = set(checkpoint.get("executed") or [])
    ordered = _sort_for_execution(branches)
    pending = []
    for row in ordered:
        bname = row["branch_name"]
        if skip_existing and _report_exists(bname):
            executed.add(bname)
            continue
        if bname in executed and skip_existing:
            continue
        pending.append(bname)

    total = len(pending)
    if not pending:
        print("Run tools: nothing pending (all reports exist or executed)")
        checkpoint["executed"] = sorted(executed)
        _save_checkpoint(checkpoint)
        return checkpoint

    print("Run tools: %d branches in chunks of %d (MU last)" % (total, chunk_size))
    for start in range(0, total, chunk_size):
        chunk = pending[start:start + chunk_size]
        chunk_idx = start // chunk_size + 1
        chunk_total = (total + chunk_size - 1) // chunk_size
        print("--- chunk %d/%d (%d branches) ---" % (chunk_idx, chunk_total, len(chunk)))
        try:
            results = collect_local_batch(
                chunk,
                root=ROOT,
                require_whitebox=False,
                isolated=True,
                local_root=work_root,
            )
            for r in results:
                executed.add(r.get("branch_name", ""))
                _progress(
                    "tools",
                    len(executed),
                    len(branches),
                    r.get("branch_name"),
                    "%s real=%s tool=%s" % (
                        r.get("status"),
                        r.get("real_tool"),
                        r.get("executed_tool"),
                    ),
                )
        except Exception as exc:
            print("Chunk failed:", exc)
        checkpoint["executed"] = sorted(executed)
        _save_checkpoint(checkpoint)

    print("Run tools done: executed=%d" % len(executed))
    return checkpoint


def phase_classify(branch_names=None):
    print("Classifying reports...")
    result = build_diagnostics(proofs_root=os.path.join(ROOT, "proofs"), branch_names=branch_names)
    paths = result.get("paths") or {}
    agg = result.get("aggregates") or {}
    print("Diagnostics written:")
    for key, path in paths.items():
        print("  %s: %s" % (key, path))
    print("Summary: total=%d correct=%d (%.1f%%)" % (
        agg.get("total", 0),
        agg.get("correct", 0),
        agg.get("correct_pct", 0),
    ))
    print("By category:", agg.get("by_category"))
    return result


def main():
    p = argparse.ArgumentParser(description="All-tools sweep with branch-generation diagnostics")
    p.add_argument("--techniques", default="all")
    p.add_argument("--metrics", default="all")
    p.add_argument("--types", default="Bug,BugFX,TCC,CC")
    p.add_argument("--version", default="2.6")
    p.add_argument("--work-root", default="", help="pipeline work dir (default: .pipeline_work/default)")
    p.add_argument("--chunk-size", type=int, default=10)
    p.add_argument("--strength", type=int, default=0, help="generation strength passed to write_branch")
    p.add_argument("--force", action="store_true", help="regenerate even if branch dir exists")
    p.add_argument("--skip-existing", action="store_true", help="skip tool run when local_report.json exists")
    p.add_argument("--resume", action="store_true", help="resume from checkpoint (default behavior)")
    p.add_argument("--only-generate", action="store_true")
    p.add_argument("--only-run", action="store_true")
    p.add_argument("--only-classify", action="store_true")
    p.add_argument("--no-generate", action="store_true")
    p.add_argument("--no-run", action="store_true")
    p.add_argument("--family-subset", action="store_true",
                   help="run one metric per tool family (48 branches) for fast iteration")
    args = p.parse_args()

    types = [t.strip() for t in args.types.split(",") if t.strip()]
    work_root = args.work_root or pipeline_work_dir(ROOT, app_user=None)
    os.makedirs(work_root, exist_ok=True)

    branches = _branch_list(args.techniques, args.metrics, types, args.version,
                            family_subset=args.family_subset)
    branch_names = [b["branch_name"] for b in branches]
    print("Sweep scope: %d branches | work_root=%s" % (len(branches), work_root), flush=True)

    checkpoint = _load_checkpoint() if args.resume else {"generated": [], "executed": []}

    do_generate = not args.no_generate and not args.only_run and not args.only_classify
    do_run = not args.no_run and not args.only_generate and not args.only_classify
    do_classify = not args.only_generate and not args.only_run

    if args.only_generate:
        do_generate, do_run, do_classify = True, False, False
    elif args.only_run:
        do_generate, do_run, do_classify = False, True, False
    elif args.only_classify:
        do_generate, do_run, do_classify = False, False, True

    if do_generate:
        checkpoint = phase_generate(
            branches, work_root, force=args.force, checkpoint=checkpoint, strength=args.strength,
        )
    if do_run:
        checkpoint = phase_run_tools(
            branches,
            work_root,
            chunk_size=args.chunk_size,
            skip_existing=args.skip_existing or args.resume,
            checkpoint=checkpoint,
        )
    if do_classify:
        phase_classify(branch_names=branch_names)

    return 0


if __name__ == "__main__":
    sys.exit(main())
