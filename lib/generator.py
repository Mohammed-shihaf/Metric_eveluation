"""Registry-driven branch generator — routes SA to sa_generator, others to python_generator."""

from __future__ import print_function

import os

from lib.metrics import branch_name, sanitize_version
from lib.registry import iter_branches, parse_techniques_arg, parse_types_arg


def write_branch(root, technique_code, metric_code, branch_type, version="2.6", language="python"):
    technique_code = technique_code.upper()
    metric_code = metric_code.upper()
    version = sanitize_version(version)
    if technique_code == "SA" and language == "python":
        from lib.sa_generator import write_branch as sa_write
        return sa_write(root, metric_code, branch_type, version, language)
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
):
    """Generate branches. Returns (branch_names, errors) where errors is a list of dicts."""
    root = repo_root or os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    names = []
    errors = []
    for tech, metric, bt, bname in iter_branches(techniques, metrics, types, version):
        out = os.path.join(root, build_dir, bname)
        try:
            write_branch(out, tech, metric, bt, version, language)
            names.append(bname)
        except Exception as exc:
            errors.append({
                "branch": bname,
                "technique": tech,
                "metric": metric,
                "type": bt,
                "path": out,
                "error": str(exc),
            })
            if not continue_on_error:
                raise
    return names, errors


def create_git_branches(
    techniques="all",
    metrics="all",
    types=None,
    version="2.6",
    language="python",
    repo_root=None,
    build_dir="build",
):
    from lib.sa_generator import create_git_branches as _create
    # generalized: loop all branch names
    names = []
    for tech, metric, bt, bname in iter_branches(techniques, metrics, types, version):
        names.append(bname)
    root = repo_root or os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    import subprocess
    import shutil
    keep = {".git", "build", "lib", "notebooks", "tools", "archive", "runs", "config", "docs",
            ".gitignore", ".env.local", "taxonomy_reports"}
    for bname in names:
        subprocess.check_call(["git", "checkout", "-B", bname, "main"], cwd=root)
        for name in os.listdir(root):
            if name in keep:
                continue
            path = os.path.join(root, name)
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
        src = os.path.join(root, build_dir, bname)
        if not os.path.isdir(src):
            raise RuntimeError("Missing build output: %s" % src)
        for item in os.listdir(src):
            s, d = os.path.join(src, item), os.path.join(root, item)
            if os.path.isdir(s):
                shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)
        subprocess.check_call(["git", "add", "-A"], cwd=root)
        subprocess.check_call(
            ["git", "commit", "-m", "Add %s codebase" % bname], cwd=root)
    subprocess.check_call(["git", "checkout", "main"], cwd=root)
    return names


def push_branches(branch_names, repo_root=None):
    import subprocess
    root = repo_root or os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    for name in branch_names:
        subprocess.check_call(["git", "push", "-u", "origin", name, "--force"], cwd=root)
