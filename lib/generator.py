"""Registry-driven branch generator — routes SA to sa_generator, others to python_generator."""

from __future__ import print_function

import os

from lib.metrics import branch_name, sanitize_version
from lib.registry import iter_branches, parse_techniques_arg, parse_types_arg


def write_branch(root, technique_code, metric_code, branch_type, version="2.6", language="python"):
    technique_code = technique_code.upper()
    metric_code = metric_code.upper()
    version = sanitize_version(version)
    if language != "python":
        from lib.python_generator import write_branch as py_write
        return py_write(root, technique_code, metric_code, branch_type, version, language)
    from lib.python_generator import write_branch as py_write
    return py_write(root, technique_code, metric_code, branch_type, version, language)


def generate_branches(
    techniques="all",
    metrics="all",
    types=None,
    version="2.6",
    language="python",
    build_dir="build",
    repo_root=None,
    continue_on_error=True,
    progress_callback=None,
):
    """Generate branches. Returns (branch_names, errors) where errors is a list of dicts."""
    root = repo_root or os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    names = []
    errors = []
    planned = list(iter_branches(techniques, metrics, types, version))
    total = len(planned)
    for idx, (tech, metric, bt, bname) in enumerate(planned, start=1):
        out = os.path.join(root, build_dir, bname)
        if progress_callback:
            progress_callback("generate", idx, total, bname, "generating")
        try:
            write_branch(out, tech, metric, bt, version, language)
            names.append(bname)
            if progress_callback:
                progress_callback("generate", idx, total, bname, "done")
        except Exception as exc:
            errors.append({
                "branch": bname,
                "technique": tech,
                "metric": metric,
                "type": bt,
                "path": out,
                "error": str(exc),
            })
            if progress_callback:
                progress_callback("generate", idx, total, bname, "error: %s" % exc)
            if not continue_on_error:
                raise
    return names, errors


# Root-level scaffold kept on every metric branch; the previous metric's
# generated files (everything else) are removed before the new codebase is copied.
_BRANCH_KEEP = {
    ".git", "build", "lib", "notebooks", "tools", "archive", "runs",
    "config", "docs", ".gitignore", ".env.local", "taxonomy_reports",
}


def _checked_out_branches(root):
    """Branch names currently checked out in any worktree (cannot be re-checked-out)."""
    import subprocess
    out = subprocess.check_output(["git", "worktree", "list", "--porcelain"], cwd=root)
    branches = set()
    for line in out.decode("utf-8", "replace").splitlines():
        if line.startswith("branch "):
            ref = line.split(" ", 1)[1].strip()
            branches.add(ref.replace("refs/heads/", ""))
    return branches


def create_git_branches(
    techniques="all",
    metrics="all",
    types=None,
    version="2.6",
    language="python",
    repo_root=None,
    build_dir="build",
    base="main",
    progress_callback=None,
):
    """Create/refresh git branches from validated build/ output.

    Uses an isolated git worktree per branch so the live working directory
    (and any running app) is never checked out, wiped, or committed into.
    Returns (created_branches, errors).
    """
    import shutil
    import subprocess
    import tempfile

    root = repo_root or os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    names = [bname for _, _, _, bname in iter_branches(techniques, metrics, types, version)]
    total = len(names)

    live = _checked_out_branches(root)
    created = []
    errors = []
    wt_root = tempfile.mkdtemp(prefix="metric_wt_")
    try:
        for idx, bname in enumerate(names, start=1):
            if progress_callback:
                progress_callback("git", idx - 1, total, bname, "worktree")
            if bname in live:
                errors.append({"branch": bname, "error": "branch is checked out in another worktree; skipped"})
                continue
            src = os.path.join(root, build_dir, bname)
            if not os.path.isdir(src):
                errors.append({"branch": bname, "error": "missing build output: %s" % src})
                continue
            wt = os.path.join(wt_root, bname.replace("/", "_"))
            try:
                subprocess.check_call(["git", "worktree", "add", "--force", "-B", bname, wt, base], cwd=root)
            except subprocess.CalledProcessError as exc:
                errors.append({"branch": bname, "error": "worktree add failed: %s" % exc})
                continue
            try:
                for name in os.listdir(wt):
                    if name in _BRANCH_KEEP:
                        continue
                    path = os.path.join(wt, name)
                    if os.path.isdir(path):
                        shutil.rmtree(path)
                    else:
                        os.remove(path)
                for item in os.listdir(src):
                    s, d = os.path.join(src, item), os.path.join(wt, item)
                    if os.path.isdir(s):
                        shutil.copytree(s, d)
                    else:
                        shutil.copy2(s, d)
                subprocess.check_call(["git", "add", "-A"], cwd=wt)
                # commit only when the branch tip would actually change
                if subprocess.call(["git", "diff", "--cached", "--quiet"], cwd=wt) != 0:
                    subprocess.check_call(["git", "commit", "-m", "Add %s codebase" % bname], cwd=wt)
                created.append(bname)
                if progress_callback:
                    progress_callback("git", idx, total, bname, "committed")
            except (subprocess.CalledProcessError, OSError) as exc:
                errors.append({"branch": bname, "error": str(exc)})
            finally:
                subprocess.call(["git", "worktree", "remove", "--force", wt], cwd=root)
    finally:
        shutil.rmtree(wt_root, ignore_errors=True)
        subprocess.call(["git", "worktree", "prune"], cwd=root)
    return created, errors


def push_branches(branch_names, repo_root=None):
    import subprocess
    root = repo_root or os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    for name in branch_names:
        subprocess.check_call(["git", "push", "-u", "origin", name, "--force"], cwd=root)
