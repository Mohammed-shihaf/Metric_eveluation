"""GitHub Git Data API push and zipball fetch — no local git required."""

from __future__ import print_function

import contextlib
import io
import os
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.request
import zipfile

from lib.github_auth import (
    _pat_write_help,
    authenticated_remote_url,
    normalize_repo_slug,
)
from lib.github_auth import _api_request as _auth_api_request

_api_request = _auth_api_request


def _git_env():
    from lib.generator import _git_env as gen_git_env
    return gen_git_env()


def _git_no_cred():
    from lib.generator import _GIT_NO_CRED
    return _GIT_NO_CRED


def _format_push_error(detail, repo_slug, login=None, token=None):
    detail = (detail or "").strip()
    slug = normalize_repo_slug(repo_slug)
    lowered = detail.lower()
    from lib.github_auth import github_app_install_help, github_oauth_app_mode, _token_kind

    permission_error = (
        "not accessible" in lowered
        or "authentication failed" in lowered
        or "invalid credentials" in lowered
        or "permission to" in lowered
        or "permission denied" in lowered
        or "403" in lowered
        or "write access" in lowered
        or "404" in lowered
    )
    if permission_error and _token_kind(token or "") == "github-app-user":
        return github_app_install_help(slug)
    if permission_error:
        return _pat_write_help(slug, login)
    return detail[:500] if detail else "git push failed"


def _git_remote_urls(token, slug, login=None):
    from urllib.parse import quote

    token_q = quote(token, safe="")
    owner = slug.split("/")[0]
    login = login or owner
    return [
        ("x-access-token", "https://x-access-token:%s@github.com/%s.git" % (token_q, slug)),
        ("owner-token", "https://%s:%s@github.com/%s.git" % (quote(login), token_q, slug)),
        ("token-only", "https://%s@github.com/%s.git" % (token_q, slug)),
    ]


def _prepare_git_commit(source_dir, message):
    env = _git_env()

    def _run(cmd):
        return subprocess.run(
            cmd,
            cwd=source_dir,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

    for cmd in (
        ["git", "init"],
        ["git", "config", "user.email", "tas@local"],
        ["git", "config", "user.name", "Testable Assurance Studio"],
        ["git", "add", "-A"],
        ["git", "commit", "-m", message],
    ):
        proc = _run(cmd)
        if proc.returncode != 0 and cmd[1] != "commit":
            return (proc.stderr or proc.stdout or "git %s failed" % cmd[1]).strip()
        if proc.returncode != 0 and cmd[1] == "commit" and "nothing to commit" not in (proc.stdout + proc.stderr):
            return (proc.stderr or proc.stdout or "git commit failed").strip()
    return None


def _git_push_prepared(source_dir, token, slug, branch_name, login=None):
    env = _git_env()
    ref = "HEAD:refs/heads/%s" % branch_name
    errors = []

    for label, url in _git_remote_urls(token, slug, login=login):
        proc = subprocess.run(
            ["git"] + _git_no_cred() + ["push", url, ref, "--force"],
            cwd=source_dir,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode == 0:
            sha_proc = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=source_dir,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            sha = sha_proc.stdout.strip() if sha_proc.returncode == 0 else ""
            return sha or None, None, label
        errors.append("%s: %s" % (label, (proc.stderr or proc.stdout or "failed").strip()[:200]))

    from lib.github_auth import github_https_url, git_auth_config

    plain = github_https_url(slug)
    auth_cfg = git_auth_config(token)
    proc = subprocess.run(
        ["git"] + _git_no_cred() + auth_cfg + ["push", plain, ref, "--force"],
        cwd=source_dir,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode == 0:
        sha_proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=source_dir,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        sha = sha_proc.stdout.strip() if sha_proc.returncode == 0 else ""
        return sha or None, None, "bearer-header"
    errors.append("bearer-header: %s" % (proc.stderr or proc.stdout or "failed").strip()[:200])
    return None, "\n".join(errors), None


def probe_api_write(token, repo_slug):
    """Return (ok, detail) for a lightweight Git Data API blob write."""
    slug = normalize_repo_slug(repo_slug)
    try:
        _api_request(
            token,
            "/repos/%s/git/blobs" % slug,
            method="POST",
            body={"content": "tas-write-probe", "encoding": "utf-8"},
        )
        return True, "Git Data API blob write OK"
    except urllib.error.HTTPError as exc:
        return False, _api_error_detail(exc, slug)
    except Exception as exc:
        return False, str(exc)


def push_branch_to_github(
    token,
    repo_slug,
    branch_name,
    files=None,
    source_dir=None,
    base="main",
    message=None,
    login=None,
):
    """Push a branch using Git Data API first, then HTTPS git fallbacks."""
    slug = normalize_repo_slug(repo_slug)
    token = (token or "").strip()
    if not slug or not token:
        return None, "missing token or repo slug", None

    message = message or "Add %s codebase" % branch_name
    errors = []

    if files:
        commit_sha, api_err = create_branch_via_api(
            token, slug, branch_name, files, base=base, message=message,
        )
        if not api_err:
            return commit_sha, None, "git-data-api"
        errors.append("git-data-api: %s" % api_err)

    if source_dir and os.path.isdir(source_dir):
        prep_err = _prepare_git_commit(source_dir, message)
        if prep_err:
            errors.append("git-prepare: %s" % prep_err)
        else:
            commit_sha, git_err, method = _git_push_prepared(
                source_dir, token, slug, branch_name, login=login,
            )
            if not git_err:
                return commit_sha, None, method
            errors.append("git-push: %s" % git_err)

    combined = "\n".join(errors) if errors else "no push method available"
    return None, _format_push_error(combined, slug, login=login, token=token), None


def push_branch_from_dir(token, repo_slug, branch_name, source_dir, message=None, login=None):
    """Push a validated branch directory to GitHub."""
    return push_branch_to_github(
        token,
        repo_slug,
        branch_name,
        source_dir=source_dir,
        message=message,
        login=login,
    )[:2]



def _api_download(token, path):
    """Download raw bytes from a GitHub API path (follows redirects)."""
    url = "https://api.github.com%s" % path
    req = urllib.request.Request(
        url,
        method="GET",
        headers={
            "Authorization": "Bearer %s" % token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "TestableAssuranceStudio",
        },
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.read()


def _api_error_detail(exc, repo_slug=None):
    try:
        body = exc.read().decode("utf-8", "replace")
    except Exception:
        return "HTTP %s" % exc.code
    if not body:
        return "HTTP %s" % exc.code
    if "not accessible" in body.lower() and repo_slug:
        return _pat_write_help(normalize_repo_slug(repo_slug))
    return body[:500]


def create_branch_via_api(token, repo_slug, branch, files, base="main", message=None):
    """Create or force-update a branch by overlaying *files* on *base* via Git Data API.

    *files* is a ``{relative_path: text_content}`` dict (same shape as
    ``generate_branch_files``). Returns ``(commit_sha, error)`` where *error*
    is ``None`` on success.
    """
    slug = normalize_repo_slug(repo_slug)
    token = (token or "").strip()
    if not slug or not token:
        return None, "missing token or repo slug"
    if not files:
        return None, "no files to push"

    message = message or "Add %s codebase" % branch
    api_base = "/repos/%s" % slug

    try:
        ref = _api_request(token, "%s/git/ref/heads/%s" % (api_base, base))
        base_sha = ref["object"]["sha"]
        base_commit = _api_request(token, "%s/git/commits/%s" % (api_base, base_sha))
        base_tree_sha = base_commit["tree"]["sha"]

        tree_entries = []
        for rel_path, content in sorted(files.items()):
            if content is None:
                continue
            text = content if isinstance(content, str) else str(content)
            blob = _api_request(
                token,
                "%s/git/blobs" % api_base,
                method="POST",
                body={
                    "content": text,
                    "encoding": "utf-8",
                },
            )
            tree_entries.append({
                "path": rel_path.replace("\\", "/"),
                "mode": "100644",
                "type": "blob",
                "sha": blob["sha"],
            })

        tree = _api_request(
            token,
            "%s/git/trees" % api_base,
            method="POST",
            body={"base_tree": base_tree_sha, "tree": tree_entries},
        )
        commit = _api_request(
            token,
            "%s/git/commits" % api_base,
            method="POST",
            body={
                "message": message,
                "tree": tree["sha"],
                "parents": [base_sha],
            },
        )
        commit_sha = commit["sha"]
        ref_path = "refs/heads/%s" % branch

        try:
            _api_request(
                token,
                "%s/git/refs" % api_base,
                method="POST",
                body={"ref": ref_path, "sha": commit_sha},
            )
        except urllib.error.HTTPError as exc:
            if exc.code != 422:
                return None, "create ref failed: %s" % _api_error_detail(exc, slug)
            _api_request(
                token,
                "%s/git/refs/heads/%s" % (api_base, branch),
                method="PATCH",
                body={"sha": commit_sha, "force": True},
            )

        return commit_sha, None
    except urllib.error.HTTPError as exc:
        return None, "GitHub API error: %s" % _api_error_detail(exc, slug)
    except Exception as exc:
        return None, str(exc)


def _flatten_zip_extract(zip_bytes, dest_dir):
    """Extract zipball bytes into *dest_dir*, flattening the single top folder."""
    os.makedirs(dest_dir, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        members = [m for m in zf.namelist() if m and not m.endswith("/")]
        if not members:
            return dest_dir
        top_prefix = members[0].split("/", 1)[0] + "/"
        for member in zf.namelist():
            if member.endswith("/"):
                continue
            rel = member[len(top_prefix):] if member.startswith(top_prefix) else member
            if not rel:
                continue
            target = os.path.join(dest_dir, rel.replace("/", os.sep))
            parent = os.path.dirname(target)
            if parent and not os.path.isdir(parent):
                os.makedirs(parent)
            with zf.open(member) as src, open(target, "wb") as dst:
                dst.write(src.read())
    return dest_dir


def fetch_branch_source(token, repo_slug, ref, dest_dir):
    """Download and extract a branch zipball into *dest_dir*.

    Returns the extracted root path (== *dest_dir* after flattening).
    """
    slug = normalize_repo_slug(repo_slug)
    token = (token or "").strip()
    if not slug or not token:
        raise ValueError("missing token or repo slug")
    ref = (ref or "").strip()
    if not ref:
        raise ValueError("missing ref")

    zip_bytes = _api_download(token, "/repos/%s/zipball/%s" % (slug, ref))
    return _flatten_zip_extract(zip_bytes, dest_dir)


@contextlib.contextmanager
def materialize_branch(token, repo_slug, branch, ref=None):
    """Fetch a branch from GitHub into a temp dir; delete on exit."""
    tmp = tempfile.mkdtemp(prefix="gh_branch_")
    try:
        fetch_branch_source(token, repo_slug, ref or branch, tmp)
        yield tmp
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def read_remote_text(token, repo_slug, ref, path):
    """Return decoded text for a file on a remote branch, or None if absent."""
    import base64
    import urllib.error
    import urllib.parse

    slug = normalize_repo_slug(repo_slug)
    token = (token or "").strip()
    ref = (ref or "").strip()
    rel_path = (path or "").replace("\\", "/").lstrip("/")
    if not slug or not token or not ref or not rel_path:
        return None

    enc_path = urllib.parse.quote(rel_path, safe="/")
    enc_ref = urllib.parse.quote(ref, safe="")
    api_path = "/repos/%s/contents/%s?ref=%s" % (slug, enc_path, enc_ref)
    try:
        data = _api_request(token, api_path)
        if not isinstance(data, dict):
            return None
        content = data.get("content", "")
        encoding = data.get("encoding", "")
        if encoding == "base64":
            return base64.b64decode(content).decode("utf-8", "replace")
        return content or None
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        return None
    except Exception:
        return None


def remote_branches_via_api(token, repo_slug, branch_names):
    """Check branch existence via GitHub REST API (reliable for OAuth/PAT tokens)."""
    import urllib.error
    import urllib.parse

    slug = normalize_repo_slug(repo_slug)
    token = (token or "").strip()
    status = {name: {"pushed": False, "sha": None} for name in branch_names}
    if not slug or not token:
        return status

    for name in branch_names:
        enc = urllib.parse.quote(name, safe="")
        path = "/repos/%s/branches/%s" % (slug, enc)
        try:
            data = _api_request(token, path)
            sha = ((data.get("commit") or {}).get("sha") or "")[:12]
            status[name] = {"pushed": True, "sha": sha or None}
        except (urllib.error.HTTPError, urllib.error.URLError, OSError, ValueError, KeyError):
            continue
    return status


def list_repo_branches(token, repo_slug, max_pages=10):
    """List all branch names on a GitHub repository."""
    import urllib.error

    slug = normalize_repo_slug(repo_slug)
    token = (token or "").strip()
    if not slug or not token:
        return []
    names = []
    for page in range(1, max_pages + 1):
        path = "/repos/%s/branches?per_page=100&page=%d" % (slug, page)
        try:
            data = _api_request(token, path)
        except (urllib.error.HTTPError, urllib.error.URLError, OSError, ValueError):
            break
        if not isinstance(data, list) or not data:
            break
        for item in data:
            name = (item.get("name") or "").strip()
            if name:
                names.append(name)
        if len(data) < 100:
            break
    return names
