"""Registry-driven branch generator — routes SA to sa_generator, others to python_generator."""

from __future__ import print_function

import os

from lib.metrics import branch_name, sanitize_version
from lib.registry import iter_branches, parse_techniques_arg, parse_types_arg


def _git_env():
    """Environment that forbids git from launching any interactive credential UI.

    Without this, a failed/expired token makes Git Credential Manager open a
    browser OAuth tab per call — across many ls-remote/push calls that becomes
    a flood of browser tabs. These vars force git to fail fast instead.
    """
    env = dict(os.environ)
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GCM_INTERACTIVE"] = "Never"
    env["GIT_ASKPASS"] = "echo"
    env["SSH_ASKPASS"] = "echo"
    return env


# Disables every configured credential helper (incl. Git Credential Manager)
# for a single invocation, so github.com auth never pops a browser.
_GIT_NO_CRED = ["-c", "credential.helper="]


def write_branch(root, technique_code, metric_code, branch_type, version="2.6", language="python"):
    technique_code = technique_code.upper()
    metric_code = metric_code.upper()
    version = sanitize_version(version)
    from lib.lang_generators import write_branch as lang_write
    return lang_write(root, technique_code, metric_code, branch_type, version, language)


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
    out = subprocess.check_output(
        ["git", "worktree", "list", "--porcelain"], cwd=root, env=_git_env()
    )
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

    Used by CLI scripts (generate_branches.py, run_dataflow_pipeline.py).
    The Streamlit UI pipeline pushes via lib.github_api instead.

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
                subprocess.check_call(
                    ["git", "worktree", "add", "--force", "-B", bname, wt, base],
                    cwd=root, env=_git_env(),
                )
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
                subprocess.check_call(["git", "add", "-A"], cwd=wt, env=_git_env())
                # commit only when the branch tip would actually change
                if subprocess.call(["git", "diff", "--cached", "--quiet"], cwd=wt, env=_git_env()) != 0:
                    subprocess.check_call(
                        ["git", "commit", "-m", "Add %s codebase" % bname],
                        cwd=wt, env=_git_env(),
                    )
                created.append(bname)
                if progress_callback:
                    progress_callback("git", idx, total, bname, "committed")
            except (subprocess.CalledProcessError, OSError) as exc:
                errors.append({"branch": bname, "error": str(exc)})
            finally:
                subprocess.call(["git", "worktree", "remove", "--force", wt], cwd=root, env=_git_env())
    finally:
        shutil.rmtree(wt_root, ignore_errors=True)
        subprocess.call(["git", "worktree", "prune"], cwd=root, env=_git_env())
    return created, errors


def push_branches(branch_names, repo_root=None, github_config=None):
    """Push branches to GitHub. Uses github_config token/repo or falls back to origin."""
    import subprocess

    root = repo_root or os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    pushed = []
    errors = []
    push_url = None
    auth_cfg = []
    if github_config:
        from lib.github_auth import git_auth_config, github_https_url

        token = github_config.get("token", "")
        push_url = github_https_url(github_config.get("repo_slug", ""))
        auth_cfg = git_auth_config(token)
        if not push_url or not auth_cfg:
            return [], [{"branch": "*", "error": "invalid GitHub push configuration"}]
    for name in branch_names:
        try:
            if push_url:
                ref = "refs/heads/%s:refs/heads/%s" % (name, name)
                subprocess.check_call(
                    ["git"] + _GIT_NO_CRED + auth_cfg + ["push", push_url, ref, "--force"],
                    cwd=root,
                    env=_git_env(),
                )
            else:
                subprocess.check_call(
                    ["git"] + _GIT_NO_CRED + ["push", "-u", "origin", name, "--force"],
                    cwd=root,
                    env=_git_env(),
                )
            pushed.append(name)
        except subprocess.CalledProcessError as exc:
            errors.append({"branch": name, "error": "git push failed: %s" % exc})
    return pushed, errors


def remote_branch_status(branch_names, repo_root=None, github_config=None):
    """Check whether each branch exists on the configured remote."""
    root = repo_root or os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    status = {name: {"pushed": False, "sha": None} for name in branch_names}

    if github_config and github_config.get("token") and github_config.get("repo_slug"):
        from lib.github_api import remote_branches_via_api

        return remote_branches_via_api(
            github_config["token"],
            github_config["repo_slug"],
            branch_names,
        )

    import subprocess

    cmd = ["git"] + _GIT_NO_CRED + ["ls-remote", "--heads", "origin"]
    try:
        out = subprocess.check_output(
            cmd, cwd=root, stderr=subprocess.DEVNULL, env=_git_env()
        )
    except subprocess.CalledProcessError:
        return status

    wanted = set(branch_names)
    for line in out.decode("utf-8", "replace").splitlines():
        line = line.strip()
        if not line or "\t" not in line:
            continue
        sha, ref = line.split("\t", 1)
        name = ref.strip().replace("refs/heads/", "")
        if name in wanted:
            status[name] = {"pushed": True, "sha": sha[:12]}
    return status
