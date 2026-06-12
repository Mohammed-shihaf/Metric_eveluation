"""Save taxonomy HTML to main branch under registry-driven paths."""

from __future__ import print_function

import os
import subprocess

from lib.metrics import report_file_path, report_group_label


def save_html_on_main(repo_root, branch_name, html_content, collected_at=None):
    """taxonomy_reports/<L2>/<BRANCH>/<BRANCH>_<timestamp>.html"""
    from lib.metrics import infer_from_branch_name, report_timestamp_notebook
    from lib.registry import metric_entry

    tech, metric, _, _ = infer_from_branch_name(branch_name)
    if not tech:
        raise ValueError("cannot parse branch name: %s" % branch_name)
    group = report_group_label(tech)
    ts = collected_at or report_timestamp_notebook()
    out_path = report_file_path(group, branch_name, ts)
    full = os.path.join(repo_root, out_path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as fh:
        fh.write(html_content)
    return full, out_path


def git_commit_report(repo_root, rel_path, branch_name):
    subprocess.check_call(["git", "checkout", "main"], cwd=repo_root)
    subprocess.check_call(["git", "add", rel_path], cwd=repo_root)
    msg = "Add taxonomy report for %s" % branch_name
    subprocess.check_call(["git", "commit", "-m", msg], cwd=repo_root)
    rev = subprocess.check_output(
        ["git", "rev-parse", "--short", "HEAD"], cwd=repo_root).decode().strip()
    return rev
