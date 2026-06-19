#!/usr/bin/env python3
"""Relocate misfiled taxonomy report folders to per-technique classification dirs."""

from __future__ import print_function

import argparse
import json
import os
import shutil
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from lib.metrics import (  # noqa: E402
    branch_name_from_report_folder,
    classification_label_for_branch,
    report_output_dir,
)
from lib.taxonomy_meta import parse_taxonomy_html  # noqa: E402


def _is_report_folder(name):
    """True for {branch}_{timestamp} folders (not classification dir names)."""
    return bool(name) and "_" in name and not name.endswith(".json")


def _iter_report_folders(taxonomy_root):
    root = os.path.join(ROOT, taxonomy_root)
    if not os.path.isdir(root):
        return
    for class_name in sorted(os.listdir(root)):
        class_dir = os.path.join(root, class_name)
        if not os.path.isdir(class_dir):
            continue
        for folder_name in sorted(os.listdir(class_dir)):
            folder_path = os.path.join(class_dir, folder_name)
            if not os.path.isdir(folder_path):
                continue
            if not _is_report_folder(folder_name):
                continue
            yield class_name, folder_name, folder_path


def _run_meta_from_folder(folder_path, folder_name):
    run_id_path = os.path.join(folder_path, "run_id.txt")
    run_id = ""
    if os.path.isfile(run_id_path):
        with open(run_id_path, encoding="utf-8") as fh:
            run_id = fh.read().strip()
    status = ""
    summary_path = os.path.join(folder_path, "run_summary.json")
    if os.path.isfile(summary_path):
        with open(summary_path, encoding="utf-8") as fh:
            summary = json.load(fh)
        status = summary.get("status", "")
    gate_score = None
    for html in os.listdir(folder_path):
        if html.startswith("taxonomy-gate") and html.endswith(".html"):
            meta = parse_taxonomy_html(os.path.join(folder_path, html))
            run_id = run_id or meta.get("run_id", "")
            break
    json_path = os.path.join(folder_path, "taxonomy-gate.json")
    if os.path.isfile(json_path):
        with open(json_path, encoding="utf-8") as fh:
            tax_json = json.load(fh)
        from lib.sa_qa import extract_gate_score

        gate_score = extract_gate_score(tax_json)
    branch = branch_name_from_report_folder(folder_name)
    entry = {
        "branch": branch,
        "report_folder": folder_name,
        "run_id": run_id,
        "status": status,
    }
    if gate_score is not None:
        entry["gate_score"] = gate_score
    return entry


def _rebuild_manifest(class_dir, classification):
    runs = []
    if not os.path.isdir(class_dir):
        return
    for folder_name in sorted(os.listdir(class_dir)):
        folder_path = os.path.join(class_dir, folder_name)
        if not os.path.isdir(folder_path) or not _is_report_folder(folder_name):
            continue
        entry = _run_meta_from_folder(folder_path, folder_name)
        if entry.get("run_id"):
            runs.append(entry)
    manifest_path = os.path.join(class_dir, "manifest.json")
    manifest = {}
    if os.path.isfile(manifest_path):
        with open(manifest_path, encoding="utf-8") as fh:
            manifest = json.load(fh)
    manifest["classification"] = classification
    manifest["runs"] = runs
    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
    return len(runs)


def repair_taxonomy_reports(taxonomy_root="taxonomy_reports", dry_run=False):
    moves = []
    for current_class, folder_name, folder_path in list(_iter_report_folders(taxonomy_root)):
        branch = branch_name_from_report_folder(folder_name)
        target_class = classification_label_for_branch(branch)
        if target_class == current_class:
            continue
        target_dir = os.path.join(
            ROOT, report_output_dir(taxonomy_root, target_class),
        )
        dest_path = os.path.join(target_dir, folder_name)
        moves.append((folder_path, dest_path, branch, current_class, target_class))

    print("Found %d misfiled report folder(s)." % len(moves))
    for src, dest, branch, src_class, dst_class in moves:
        print("  %s: %s -> %s" % (branch, src_class, dst_class))
        if dry_run:
            continue
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        if os.path.exists(dest):
            print("    WARNING: destination exists, skipping: %s" % dest)
            continue
        shutil.move(src, dest)

    if dry_run:
        return len(moves)

    touched = set()
    for _src, dest, _branch, _src_class, dst_class in moves:
        touched.add(dst_class)
    for current_class, _folder_name, _folder_path in _iter_report_folders(taxonomy_root):
        touched.add(current_class)

    for classification in sorted(touched):
        class_dir = os.path.join(ROOT, report_output_dir(taxonomy_root, classification))
        count = _rebuild_manifest(class_dir, classification)
        print("  rebuilt manifest: %s (%d runs)" % (classification, count))

    return len(moves)


def main():
    parser = argparse.ArgumentParser(
        description="Move taxonomy report folders to correct technique classification dirs",
    )
    parser.add_argument(
        "--taxonomy-root",
        default=os.environ.get("OUTPUT_DIR", "taxonomy_reports"),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned moves without applying them",
    )
    args = parser.parse_args()
    count = repair_taxonomy_reports(args.taxonomy_root, dry_run=args.dry_run)
    if args.dry_run:
        print("Dry run complete (%d move(s) planned)." % count)
    else:
        print("Repair complete (%d move(s) applied)." % count)
    return 0


if __name__ == "__main__":
    sys.exit(main())
