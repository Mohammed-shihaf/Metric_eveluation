"""Extract run metadata from taxonomy reports and manifest."""

from __future__ import print_function

import json
import re
from pathlib import Path

from lib.metrics import branch_name_from_report_folder

_HTML_FIELDS = (
    ("branch", r"Branch name</th><td>([^<]+)"),
    ("commit_sha", r"Commit ID</th><td>([^<]+)"),
    ("run_id", r"Run ID</th><td>([^<]+)"),
    ("repo", r"Repo name</th><td>([^<]+)"),
)


def parse_taxonomy_html(html_path):
    """Return dict with branch, commit_sha, run_id, repo, html_path."""
    path = Path(html_path)
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8", errors="replace")
    meta = {"html_path": str(path)}
    for key, pattern in _HTML_FIELDS:
        m = re.search(pattern, text)
        if m:
            meta[key] = m.group(1).strip()
    folder = path.parent.name
    if "branch" not in meta:
        meta["branch"] = branch_name_from_report_folder(folder)
    if "run_id" not in meta:
        m = re.search(r"taxonomy-gate-([0-9a-f-]+)\.html", path.name, re.I)
        if m:
            meta["run_id"] = m.group(1)
    return meta


def _html_files(classification_dir):
    root = Path(classification_dir)
    if not root.is_dir():
        return []
    files = []
    for folder in sorted(root.iterdir()):
        if not folder.is_dir():
            continue
        for html in folder.glob("taxonomy-gate*.html"):
            files.append(html)
    return files


def latest_taxonomy_by_branch(classification_dir):
    """Map branch -> latest metadata dict from taxonomy HTML folders."""
    by_branch = {}
    for html_path in _html_files(classification_dir):
        meta = parse_taxonomy_html(html_path)
        branch = meta.get("branch")
        if not branch:
            continue
        folder = html_path.parent.name
        ts = folder.rsplit("_", 1)[-1] if "_" in folder else ""
        prev = by_branch.get(branch)
        if prev is None or ts >= prev.get("_folder_ts", ""):
            meta["_folder_ts"] = ts
            meta["report_folder"] = folder
            by_branch[branch] = meta
    return by_branch


def load_manifest_runs(classification_dir):
    manifest_path = Path(classification_dir) / "manifest.json"
    if not manifest_path.is_file():
        return []
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    return data.get("runs", [])
