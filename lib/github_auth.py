"""GitHub account verification and authenticated git remote URLs."""

from __future__ import print_function

import json
import os
import shutil
import tempfile
import urllib.error
import urllib.request


def _api_request(token, path, method="GET", body=None):
    url = "https://api.github.com%s" % path
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
    headers = {
        "Authorization": "Bearer %s" % token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "TestableAssuranceStudio",
    }
    if body is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers=headers,
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def verify_github_token(token):
    """Validate a PAT and return (ok, message, user_dict)."""
    token = (token or "").strip()
    if not token:
        return False, "GitHub token is required", None
    try:
        user = _api_request(token, "/user")
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            return False, "Invalid or expired GitHub token", None
        return False, "GitHub API error (%s)" % exc.code, None
    except Exception as exc:
        return False, "Could not reach GitHub: %s" % exc, None
    login = user.get("login") or ""
    if not login:
        return False, "GitHub user response missing login", None
    return True, "Connected as @%s" % login, user


def normalize_repo_slug(repo_slug):
    slug = (repo_slug or "").strip().strip("/")
    if slug.endswith(".git"):
        slug = slug[:-4]
    parts = [p for p in slug.split("/") if p]
    if len(parts) != 2:
        return ""
    return "%s/%s" % (parts[0], parts[1])


def _api_error_body(exc):
    try:
        return exc.read().decode("utf-8", "replace")
    except Exception:
        return ""


def _pat_write_help(slug, login=None):
    owner = slug.split("/")[0] if slug and "/" in slug else ""
    lines = [
        "Token cannot push to **%s**." % slug,
        "Your REST check may pass while git/API writes still fail — common with **fine-grained** tokens.",
    ]
    if login and owner and login.lower() != owner.lower():
        lines.append(
            "Token account is **@%s** but repo owner is **%s**." % (login, owner)
        )
    lines.extend([
        "Fine-grained PAT checklist: set **Repository access → Only select repositories** "
        "and include this repo (not *Public repositories read-only*).",
        "Set **Repository permissions → Contents → Read and write**, then **regenerate** the token.",
        "Fastest workaround: create a **classic PAT** with the **repo** scope at "
        "github.com/settings/tokens?type=beta (classic).",
    ])
    return " ".join(lines)


def _token_kind(token):
    token = (token or "").strip()
    if token.startswith("github_pat_"):
        return "fine-grained"
    if token.startswith("ghu_"):
        return "github-app-user"
    if token.startswith(("ghp_", "gho_", "ghs_", "ghr_")):
        return "classic"
    return "unknown"


def diagnose_github_access(token, repo_slug):
    """Return step-by-step GitHub access checks for UI troubleshooting."""
    token = (token or "").strip()
    slug = normalize_repo_slug(repo_slug)
    steps = []
    login = ""

    ok, msg, user = verify_github_token(token)
    steps.append({"step": "token", "ok": ok, "detail": msg})
    if not ok:
        return steps
    login = user.get("login", "")

    ok2, msg2, repo = check_repo_access(token, repo_slug)
    perms = (repo or {}).get("permissions") or {}
    steps.append({
        "step": "repo",
        "ok": ok2,
        "detail": msg2,
        "permissions": perms,
        "token_kind": _token_kind(token),
        "token_login": login,
        "repo_owner": slug.split("/")[0] if slug else "",
    })
    if not ok2:
        return steps

    default_branch = (repo or {}).get("default_branch", "main")
    from lib.github_api import probe_api_write, push_branch_to_github

    api_ok, api_detail = probe_api_write(token, slug)
    steps.append({"step": "git_data_api", "ok": api_ok, "detail": api_detail})

    probe_dir = tempfile.mkdtemp(prefix="gh_probe_")
    probe_branch = "_tas_connect_probe"
    try:
        with open(os.path.join(probe_dir, "tas_connect_probe.txt"), "w", encoding="utf-8") as handle:
            handle.write("tas-connect-probe\n")
        sha, err, method = push_branch_to_github(
            token,
            slug,
            probe_branch,
            files={"tas_connect_probe.txt": "tas-connect-probe\n"},
            source_dir=probe_dir,
            base=default_branch,
            message="TAS connect probe",
            login=login,
        )
        steps.append({
            "step": "push",
            "ok": not err,
            "detail": ("Push OK via %s" % method) if not err else err,
            "commit_sha": (sha or "")[:12],
        })
        if not err:
            try:
                _api_request(token, "/repos/%s/git/refs/heads/%s" % (slug, probe_branch), method="DELETE")
            except Exception:
                pass
    finally:
        shutil.rmtree(probe_dir, ignore_errors=True)

    return steps


def verify_git_write_access(token, repo_slug, default_branch="main"):
    """Prove the PAT can push via Git Data API or HTTPS git."""
    slug = normalize_repo_slug(repo_slug)
    if not slug:
        return False, "Repository must be owner/repo", None
    ok, msg, user = verify_github_token(token)
    login = (user or {}).get("login", "") if ok else ""
    from lib.github_api import probe_api_write, push_branch_to_github

    api_ok, api_detail = probe_api_write(token, slug)
    probe_dir = tempfile.mkdtemp(prefix="gh_probe_")
    probe_branch = "_tas_connect_probe"
    try:
        with open(os.path.join(probe_dir, "tas_connect_probe.txt"), "w", encoding="utf-8") as handle:
            handle.write("tas-connect-probe\n")
        _sha, err, method = push_branch_to_github(
            token,
            slug,
            probe_branch,
            files={"tas_connect_probe.txt": "tas-connect-probe\n"},
            source_dir=probe_dir,
            base=default_branch,
            message="TAS connect probe",
            login=login,
        )
        if err:
            if api_ok:
                return True, "Git Data API write OK for %s (git push blocked: fine-grained token)" % slug, {
                    "default_branch": (default_branch or "main").strip() or "main",
                    "push_method": "git-data-api",
                }
            return False, err, None
        try:
            _api_request(token, "/repos/%s/git/refs/heads/%s" % (slug, probe_branch), method="DELETE")
        except Exception:
            pass
        return True, "Push access OK for %s via %s" % (slug, method or "git"), {
            "default_branch": (default_branch or "main").strip() or "main",
            "push_method": method or "git",
        }
    finally:
        shutil.rmtree(probe_dir, ignore_errors=True)


def github_app_install_url():
    """Public install URL for the configured GitHub App."""
    app_slug = os.getenv("GITHUB_APP_SLUG", "").strip() or "testable-assurance-studio"
    return "https://github.com/apps/%s/installations/new" % app_slug


def github_app_install_help(slug):
    """Actionable message when the GitHub App lacks repo access."""
    return (
        "GitHub App is not installed on **%s** or lacks **Contents: Read & write**. "
        "Install the app and select this repository: %s"
        % (slug, github_app_install_url())
    )


def _configured_app_slug():
    return os.getenv("GITHUB_APP_SLUG", "").strip() or "testable-assurance-studio"


def app_repo_install_status(token, repo_slug):
    """Check whether the configured GitHub App is installed and includes *repo_slug*.

    Returns ``(installed, repo_in_install, detail)`` where *installed* means at
    least one user installation exists for the configured app, and
    *repo_in_install* means the target repo appears in one of those installations.
    """
    slug = normalize_repo_slug(repo_slug)
    token = (token or "").strip()
    if not slug:
        return False, False, "Repository must be owner/repo"
    if not token:
        return False, False, "GitHub token is required"

    app_slug = _configured_app_slug()
    if _token_kind(token) != "github-app-user":
        return True, True, "not a GitHub App user token — skip install check"

    try:
        payload = _api_request(token, "/user/installations?per_page=100")
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            return False, False, "Cannot list GitHub App installations"
        return False, False, "GitHub API error listing installations (%s)" % exc.code
    except Exception as exc:
        return False, False, "Could not list GitHub App installations: %s" % exc

    installations = payload.get("installations") or []
    app_installs = [
        inst for inst in installations
        if (inst.get("app_slug") or "").strip() == app_slug
    ]
    if not app_installs:
        if not installations:
            return False, False, github_app_install_help(slug)
        return False, False, (
            "GitHub App **%s** is not installed for this account. %s"
            % (app_slug, github_app_install_help(slug))
        )

    for inst in app_installs:
        install_id = inst.get("id")
        if not install_id:
            continue
        try:
            repos_payload = _api_request(
                token,
                "/user/installations/%s/repositories?per_page=100" % install_id,
            )
        except urllib.error.HTTPError:
            continue
        except Exception:
            continue
        for repo in repos_payload.get("repositories") or []:
            full_name = (repo.get("full_name") or "").strip()
            if full_name.lower() == slug.lower():
                return True, True, "GitHub App installed on %s" % slug

    return True, False, github_app_install_help(slug)


def check_app_repo_access(token, repo_slug):
    """Return (ok, needs_install, detail) for GitHub App user token repo access."""
    slug = normalize_repo_slug(repo_slug)
    if not slug:
        return False, False, "Repository must be owner/repo"

    is_app_context = _token_kind(token) == "github-app-user"
    if is_app_context:
        installed, repo_in_install, install_detail = app_repo_install_status(token, slug)
        if not installed or not repo_in_install:
            return False, True, install_detail

    ok, msg, repo = check_repo_access(token, slug)
    if not ok:
        lowered = (msg or "").lower()
        needs_install = (
            "not found" in lowered
            or "no access" in lowered
            or "cannot access" in lowered
            or "read access only" in lowered
            or "not accessible" in lowered
        )
        if is_app_context and needs_install:
            needs_install = True
            msg = github_app_install_help(slug)
        return False, needs_install, msg

    from lib.github_api import probe_api_write

    api_ok, api_detail = probe_api_write(token, slug)
    if api_ok:
        return True, False, "GitHub App has read/write access to %s" % slug

    lowered = (api_detail or "").lower()
    needs_install = (
        "not accessible" in lowered
        or "404" in lowered
        or "403" in lowered
        or "write access" in lowered
    )
    perms = (repo or {}).get("permissions") or {}
    if not perms.get("push") and not perms.get("admin"):
        needs_install = True
    detail = api_detail or "GitHub App cannot write to %s" % slug
    if needs_install and is_app_context:
        detail = github_app_install_help(slug)
    return False, needs_install, detail


def github_oauth_app_mode():
    return bool(os.getenv("GITHUB_APP_SLUG", "").strip())


def check_repo_access(token, repo_slug):
    """Return (ok, message, repo_dict) for push access to owner/repo."""
    slug = normalize_repo_slug(repo_slug)
    if not slug:
        return False, "Repository must be owner/repo (e.g. your-user/Metric_evaluation)", None
    try:
        repo = _api_request(token, "/repos/%s" % slug)
    except urllib.error.HTTPError as exc:
        body = _api_error_body(exc)
        if exc.code == 404:
            return False, "Repository not found or no access: %s" % slug, None
        if exc.code in (401, 403):
            if "not accessible" in body.lower():
                return False, _pat_write_help(slug), None
            return False, "Token cannot access %s" % slug, None
        return False, "GitHub API error (%s)" % exc.code, None
    except Exception as exc:
        return False, "Could not reach GitHub: %s" % exc, None
    perms = repo.get("permissions") or {}
    if not perms.get("push") and not perms.get("admin"):
        return False, "Token has read access only — need push permission on %s" % slug, None
    return True, "Push access OK for %s" % slug, repo


def connect_github(token, repo_slug):
    """Full connect flow: verify user + repo + git push. Returns (ok, message, info_dict)."""
    ok, msg, user = verify_github_token(token)
    if not ok:
        return False, msg, None
    ok2, msg2, repo = check_repo_access(token, repo_slug)
    if not ok2:
        return False, msg2, None
    slug = normalize_repo_slug(repo_slug)
    default_branch = repo.get("default_branch", "main")
    ok3, msg3, write_info = verify_git_write_access(token, slug, default_branch)
    if not ok3:
        return False, msg3, None
    return True, "%s · %s · %s" % (msg, msg2, msg3), {
        "login": user.get("login", ""),
        "name": user.get("name") or user.get("login", ""),
        "repo_slug": slug,
        "repo_url": repo.get("html_url", ""),
        "default_branch": default_branch,
        "push_method": (write_info or {}).get("push_method", "auto"),
    }


def authenticated_remote_url(token, repo_slug):
    """HTTPS git URL with embedded token for push/ls-remote (never log this)."""
    slug = normalize_repo_slug(repo_slug)
    if not slug or not token:
        return ""
    return "https://x-access-token:%s@github.com/%s.git" % (token, slug)


def github_https_url(repo_slug):
    """Public HTTPS git URL without credentials (safe for logs/argv)."""
    slug = normalize_repo_slug(repo_slug)
    if not slug:
        return ""
    return "https://github.com/%s.git" % slug


def git_auth_config(token):
    """Return git -c args for bearer auth without embedding token in the URL."""
    token = (token or "").strip()
    if not token:
        return []
    return ["-c", "http.extraheader=AUTHORIZATION: bearer %s" % token]
