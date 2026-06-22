"""Whitebox run history and completed/pending branch partitioning."""

from __future__ import print_function

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _usable_taxonomy_meta(meta, classification_dir=None):
    from lib.taxonomy_meta import _meta_with_usable_report

    return _meta_with_usable_report(meta or {}, classification_dir=classification_dir)


def branch_run_history(branch_name, taxonomy_root="taxonomy_reports", root=None):
    """Return prior whitebox runs for *branch_name*, newest first."""
    from lib.taxonomy_meta import (
        classification_dir_for_branch,
        load_run_summary_from_meta,
        meta_from_report_folder,
        report_dir_from_meta,
        resolve_branch_taxonomy_meta,
        _report_folders,
    )

    repo_root = Path(root or ROOT)
    meta, class_dir = resolve_branch_taxonomy_meta(
        branch_name, taxonomy_root, str(repo_root),
    )
    if not class_dir or not class_dir.is_dir():
        return []

    rows = []
    seen_run_ids = set()
    for folder in _report_folders(class_dir):
        folder_meta = meta_from_report_folder(folder)
        if folder_meta.get("branch") != branch_name:
            continue
        run_id = folder_meta.get("run_id", "")
        dedupe_key = run_id or folder.name
        if dedupe_key in seen_run_ids:
            continue
        seen_run_ids.add(dedupe_key)

        report_dir = report_dir_from_meta(folder_meta, classification_dir=class_dir)
        summary = load_run_summary_from_meta(folder_meta, classification_dir=class_dir)
        gate_path = (report_dir / "taxonomy-gate.json") if report_dir else None
        gate_status = ""
        if gate_path and gate_path.is_file():
            try:
                import json

                gate_status = (
                    json.loads(gate_path.read_text(encoding="utf-8")).get("gate_status") or ""
                ).lower()
            except Exception:
                gate_status = ""

        run_status = (summary.get("status") or "").lower()
        total_tasks = summary.get("total_tasks") or 0
        completed_tasks = summary.get("completed_tasks") or 0
        failed_tasks = summary.get("failed_tasks") or 0

        rows.append({
            "branch": branch_name,
            "run_id": run_id,
            "commit_sha": folder_meta.get("commit_sha", ""),
            "run_status": run_status,
            "gate_status": gate_status,
            "gate_score": summary.get("gate_score"),
            "completed_tasks": completed_tasks,
            "total_tasks": total_tasks,
            "failed_tasks": failed_tasks,
            "html_path": folder_meta.get("html_path", ""),
            "report_folder": folder_meta.get("report_folder", folder.name),
            "timestamp": folder_meta.get("_folder_ts", ""),
        })

    rows.sort(key=lambda r: r.get("timestamp") or "", reverse=True)
    if not rows and _usable_taxonomy_meta(meta, classification_dir=class_dir):
        rows.append({
            "branch": branch_name,
            "run_id": meta.get("run_id", ""),
            "commit_sha": meta.get("commit_sha", ""),
            "run_status": "",
            "gate_status": "",
            "gate_score": None,
            "completed_tasks": 0,
            "total_tasks": 0,
            "failed_tasks": 0,
            "html_path": meta.get("html_path", ""),
            "report_folder": meta.get("report_folder", ""),
            "timestamp": meta.get("_folder_ts", ""),
        })
    return rows


def split_completed_pending(branches, taxonomy_root="taxonomy_reports", root=None):
    """Partition *branches* into (completed_with_data, pending)."""
    from lib.proofs import whitebox_completion
    from lib.taxonomy_meta import resolve_branch_taxonomy_meta

    repo_root = Path(root or ROOT)
    wb = whitebox_completion(branches, taxonomy_root=taxonomy_root, root=str(repo_root))
    completed = []
    pending = []
    for bname in branches:
        info = wb.get(bname, {})
        if info.get("status") == "COMPLETED":
            meta, class_dir = resolve_branch_taxonomy_meta(
                bname, taxonomy_root, str(repo_root),
            )
            if _usable_taxonomy_meta(meta, classification_dir=class_dir):
                completed.append(bname)
                continue
        pending.append(bname)
    return completed, pending
