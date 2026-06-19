"""Run SA branches on Testable QA and verify taxonomy HTML reports."""

from __future__ import print_function

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

from lib.sa_metrics import (  # noqa: E402
    ABBREV_TO_CLASSIFICATION,
    SA_METRICS,
    SA_TESTING_TYPE,
    branch_name_from_report_folder,
    infer_metric_from_report_folder,
    report_folder_name,
    report_output_dir,
)

CLASSIFICATION_TO_ABBREV = {cls: abbrev for _, abbrev, cls, _, _ in SA_METRICS}
ROW_RE = re.compile(
    r'<div class="cls-name">([^<]+)</div>.*?'
    r'<td class="result-em"><span class="rp rp-(\w+)">',
    re.DOTALL,
)

TERMINAL_STATUSES = frozenset(["completed", "failed", "partial", "cancelled"])
IN_FLIGHT_STATUSES = frozenset(["pending", "queued", "running", "executing", "in_progress"])
BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


S3_AWS_ENV_KEYS = (
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_SESSION_TOKEN",
    "AWS_DEFAULT_REGION",
    "S3_BUCKET",
    "S3_SEARCH_PREFIX",
    "S3_DOWNLOAD_ROOT",
    "S3_CELL_BATCH_ID",
)


def _parse_env_file(path):
    """Return key -> value mapping from a dotenv-style file."""
    out = {}
    if not os.path.isfile(path):
        return out
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            k, v = key.strip(), val.strip()
            if k:
                out[k] = v
    return out


def load_env(path, override=False):
    if not os.path.isfile(path):
        print("WARNING: env file not found: %s" % path, file=sys.stderr, flush=True)
        return
    parsed = _parse_env_file(path)
    for k, v in parsed.items():
        if override or k not in os.environ or not str(os.environ.get(k, "")).strip():
            os.environ[k] = v


def reload_env_keys(path, keys, override=True):
    """Re-read selected keys from an env file into os.environ."""
    if not os.path.isfile(path):
        print("WARNING: env file not found: %s" % path, file=sys.stderr, flush=True)
        return 0
    parsed = _parse_env_file(path)
    key_set = frozenset(keys) if keys else None
    updated = 0
    for k, v in parsed.items():
        if key_set is not None and k not in key_set:
            continue
        if override or k not in os.environ or not str(os.environ.get(k, "")).strip():
            os.environ[k] = v
            updated += 1
    return updated


def reload_s3_credentials(path=None, root=None):
    """Force-reload AWS/S3 keys from .env.local after pasting fresh STS credentials."""
    repo_root = root or ROOT
    env_path = path or os.path.join(repo_root, ".env.local")
    return reload_env_keys(env_path, S3_AWS_ENV_KEYS, override=True)


class PlatformClient(object):
    def __init__(self, identity_url, runtime_url, views_url, session_token):
        self.identity_url = identity_url.rstrip("/")
        self.runtime_url = runtime_url.rstrip("/")
        self.views_url = views_url.rstrip("/")
        self.session_token = session_token

    def _request(self, method, url, body=None, accept=None):
        req = urllib.request.Request(url, method=method)
        req.add_header("Content-Type", "application/json")
        req.add_header("User-Agent", BROWSER_USER_AGENT)
        if accept:
            req.add_header("Accept", accept)
        if self.session_token:
            req.add_header("Cookie", "session_token=%s" % self.session_token)
        if body is not None:
            req.data = json.dumps(body).encode("utf-8")
        try:
            resp = urllib.request.urlopen(req, timeout=300)
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", errors="replace")
            raise RuntimeError("HTTP %s %s %s" % (method, url, detail)) from e
        content_type = resp.headers.get("Content-Type", "")
        raw = resp.read()
        if "application/json" in content_type or (raw[:1] in (b"{", b"[")):
            return json.loads(raw.decode("utf-8"))
        return raw

    def get_json(self, url):
        return self._request("GET", url)

    def post_json(self, url, body):
        return self._request("POST", url, body=body)


def resolve_tenant_id(client):
    """Resolve tenant from the authenticated session (QA/live friendly)."""
    data = client.get_json("%s/v1/me/tenant" % client.identity_url)
    tenant_id = data.get("tenant_id")
    if not tenant_id:
        raise RuntimeError("Session tenant missing from /v1/me/tenant: %s" % data)
    return str(tenant_id)


TRANSIENT_HTTP_CODES = frozenset([502, 503, 504, 520, 521, 522, 523, 524])


def _is_transient_login_error(exc):
    if isinstance(exc, urllib.error.HTTPError):
        return exc.code in TRANSIENT_HTTP_CODES
    if isinstance(exc, (urllib.error.URLError, TimeoutError, OSError)):
        return True
    msg = str(exc).lower()
    return any(
        token in msg
        for token in ("error code: 520", "error code: 502", "error code: 503", "error code: 504",
                      "temporarily unavailable", "timed out", "connection reset")
    )


def login(identity_url, email, password):
    url = "%s/api/v1/auth/login" % identity_url.rstrip("/")
    max_retries = max(1, int(os.environ.get("AUTH_LOGIN_RETRIES", "3")))
    base_wait = max(1, int(os.environ.get("AUTH_LOGIN_RETRY_SEC", "5")))
    last_exc = None

    for attempt in range(1, max_retries + 1):
        req = urllib.request.Request(url, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("User-Agent", BROWSER_USER_AGENT)
        req.add_header("Origin", os.environ.get("FRONTEND_URL", "https://qa-frontend.testable.cc"))
        req.add_header("Referer", "%s/auth/login" % os.environ.get(
            "FRONTEND_URL", "https://qa-frontend.testable.cc").rstrip("/"))
        req.data = json.dumps({"identifier": email, "password": password}).encode("utf-8")
        try:
            resp = urllib.request.urlopen(req, timeout=60)
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", errors="replace")
            last_exc = RuntimeError("Login failed: %s" % detail)
            if _is_transient_login_error(e) and attempt < max_retries:
                wait = base_wait * (2 ** (attempt - 1))
                print(
                    "  login attempt %d/%d failed (HTTP %s) — retrying in %ds..."
                    % (attempt, max_retries, e.code, wait),
                    flush=True,
                )
                time.sleep(wait)
                continue
            if _is_transient_login_error(e):
                raise RuntimeError(
                    "Testable platform temporarily unavailable (HTTP %s) after %d attempts — try again shortly."
                    % (e.code, max_retries)
                ) from e
            raise last_exc from e
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            last_exc = RuntimeError("Login failed: %s" % e)
            if attempt < max_retries:
                wait = base_wait * (2 ** (attempt - 1))
                print(
                    "  login attempt %d/%d failed (%s) — retrying in %ds..."
                    % (attempt, max_retries, e, wait),
                    flush=True,
                )
                time.sleep(wait)
                continue
            raise RuntimeError(
                "Testable platform temporarily unavailable after %d attempts — try again shortly."
                % max_retries
            ) from e

        cookie = resp.headers.get("Set-Cookie", "")
        token = None
        for part in cookie.split(";"):
            part = part.strip()
            if part.startswith("session_token="):
                token = part.split("=", 1)[1]
                break
        if not token:
            raise RuntimeError("Login succeeded but session_token cookie missing")
        return token

    if last_exc:
        raise last_exc
    raise RuntimeError("Login failed after %d attempts" % max_retries)


def dev_verify(identity_url, email):
    url = "%s/v1/auth/dev-verify" % identity_url.rstrip("/")
    req = urllib.request.Request(url, method="POST")
    req.add_header("Content-Type", "application/json")
    req.data = json.dumps({"email": email}).encode("utf-8")
    try:
        urllib.request.urlopen(req, timeout=30)
    except urllib.error.HTTPError:
        pass


def verify_login(env_file=None, email=None, password=None):
    """Validate Testable credentials; returns (ok, message). Never returns password."""
    env_file = env_file or os.path.join(ROOT, ".env.local")
    load_env(env_file)
    identity_url = os.environ.get("IDENTITY_URL", "http://localhost:8000")
    runtime_url = os.environ.get("RUNTIME_URL", "http://localhost:8002")
    views_url = os.environ.get("VIEWS_URL", "http://localhost:8003")
    use_env = email is None and password is None
    if email is None:
        email = os.environ.get("AUTH_EMAIL", "")
    if password is None:
        password = os.environ.get("AUTH_PASSWORD", "")
    email = (email or "").strip()
    password = password or ""
    if not email or not password:
        if use_env:
            return False, "email and password required (UI or .env.local)"
        return False, "email and password required"
    try:
        if "localhost" in identity_url or "127.0.0.1" in identity_url:
            dev_verify(identity_url, email)
        token = login(identity_url, email, password)
        client = PlatformClient(identity_url, runtime_url, views_url, token)
        tenant_id = resolve_tenant_id(client)
        return True, "logged in as %s (tenant %s)" % (email, tenant_id)
    except Exception as exc:
        return False, str(exc)


def github_tip_sha(branch_name, repository_match):
    repo = repository_match.strip().strip("/")
    if repo.endswith(".git"):
        repo = repo[:-4]
    parts = repo.split("/")
    if len(parts) < 2:
        return None
    owner, name = parts[-2], parts[-1]
    api_url = "https://api.github.com/repos/%s/%s/git/ref/heads/%s" % (
        owner, name, urllib.parse.quote(branch_name))
    req = urllib.request.Request(api_url, headers={"Accept": "application/vnd.github+json"})
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        data = json.loads(resp.read().decode("utf-8"))
        return data.get("object", {}).get("sha")
    except Exception:
        return None


def resolve_commit_sha(branch_name, branch_row, repository_match, prefer_github=False):
    if prefer_github:
        sha = github_tip_sha(branch_name, repository_match)
        if sha:
            print("  commit from GitHub tip: %s" % sha[:12], flush=True)
            return sha
    for key in ("head_commit_sha", "headCommitSha", "commit_sha", "tip_sha"):
        val = branch_row.get(key)
        if val:
            return val
    sha = github_tip_sha(branch_name, repository_match)
    if sha:
        print("  resolved commit via GitHub API: %s" % sha[:12], flush=True)
        return sha
    # Fallback: local git ls-remote (works when repo is cloned and remote configured)
    try:
        _git_env = dict(os.environ)
        _git_env.update({
            "GIT_TERMINAL_PROMPT": "0", "GCM_INTERACTIVE": "Never",
            "GIT_ASKPASS": "echo", "SSH_ASKPASS": "echo",
        })
        proc = subprocess.Popen(
            ["git", "-c", "credential.helper=", "ls-remote", "origin",
             "refs/heads/%s" % branch_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=ROOT,
            env=_git_env,
        )
        out, _ = proc.communicate(timeout=30)
        line = out.decode("utf-8", errors="replace").strip().splitlines()
        if line:
            sha = line[0].split()[0]
            print("  resolved commit via git ls-remote: %s" % sha[:12])
            return sha
    except Exception as exc:
        print("  git ls-remote failed: %s" % exc)
    return None


def normalize_repo_label(clone_url):
    if not clone_url:
        return ""
    raw = clone_url.strip().rstrip("/")
    if raw.endswith(".git"):
        raw = raw[:-4]
    parts = raw.replace(":", "/").split("/")
    parts = [p for p in parts if p and p not in ("https", "http", "git@github.com")]
    if len(parts) >= 2:
        return "%s/%s" % (parts[-2], parts[-1])
    return raw


def ingestion_url_from_env():
    """Resolve Testable ingestion-api base URL for SCM sync/import."""
    explicit = (os.environ.get("INGESTION_URL") or "").strip()
    if explicit:
        return explicit.rstrip("/")
    identity = (os.environ.get("IDENTITY_URL") or "").strip().rstrip("/")
    if "qa-api" in identity:
        return "https://qa-ingestion.testable.cc"
    if "localhost" in identity or "127.0.0.1" in identity:
        return "http://localhost:8001"
    if identity:
        return identity.replace("qa-api", "qa-ingestion")
    return "https://qa-ingestion.testable.cc"


def resolve_github_default_branch(repository_match, github_token=None):
    """Return the GitHub default branch for *repository_match* (usually ``main``)."""
    slug = normalize_repo_label(repository_match)
    if not slug:
        return "main"
    token = (github_token or os.environ.get("GITHUB_TOKEN") or "").strip()
    if token:
        try:
            import urllib.error

            path = "/repos/%s" % slug
            req = urllib.request.Request("https://api.github.com%s" % path)
            req.add_header("Accept", "application/vnd.github+json")
            req.add_header("Authorization", "Bearer %s" % token)
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            default_branch = (data.get("default_branch") or "").strip()
            if default_branch:
                return default_branch
        except Exception:
            pass
    oauth_default = (os.environ.get("GITHUB_DEFAULT_BRANCH") or "").strip()
    if oauth_default:
        return oauth_default
    return "main"


def get_repository_record(client, project_id, repository_id):
    """Fetch a repository row from runtime-api."""
    repos_resp = client.get_json(
        "%s/v1/projects/%s/repositories" % (client.runtime_url, project_id)
    )
    repo_list = repos_resp.get("repositories") or repos_resp.get("items") or []
    for repo in repo_list:
        if repo.get("id") == repository_id:
            return repo
    return None


def is_misseeded_repository(repo_record, github_default, required_branches):
    """True when catalog was seeded with an analysis branch instead of the repo default."""
    if not repo_record:
        return False
    seeded = (repo_record.get("default_branch") or "").strip()
    github_default = (github_default or "main").strip()
    if not seeded or seeded == github_default:
        return False
    required = list(required_branches or [])
    if seeded in required:
        return True
    return False


def list_scm_connections(client):
    """Return active SCM connections from ingestion-api."""
    ingestion = ingestion_url_from_env()
    ingestion_client = PlatformClient(
        client.identity_url, ingestion, client.views_url, client.session_token
    )
    try:
        data = ingestion_client.get_json("%s/v1/scm/connections" % ingestion)
    except Exception:
        return []
    connections = data.get("connections") or []
    return [c for c in connections if (c.get("status") or "").lower() == "active"]


def trigger_scm_sync(client, connection_id):
    ingestion = ingestion_url_from_env()
    ingestion_client = PlatformClient(
        client.identity_url, ingestion, client.views_url, client.session_token
    )
    return ingestion_client.post_json(
        "%s/v1/scm/connections/%s/sync" % (ingestion, connection_id),
        {},
    )


def wait_for_scm_sync(client, sync_id, timeout_sec=120, poll_interval=5):
    ingestion = ingestion_url_from_env()
    ingestion_client = PlatformClient(
        client.identity_url, ingestion, client.views_url, client.session_token
    )
    started = time.time()
    last_status = None
    detail = {}
    while time.time() - started < timeout_sec:
        detail = ingestion_client.get_json("%s/v1/scm/syncs/%s" % (ingestion, sync_id))
        status = (detail.get("status") or "").lower()
        if status != last_status:
            print(
                "  scm sync status=%s phase=%s"
                % (status or "unknown", detail.get("phase") or "—"),
                flush=True,
            )
            last_status = status
        if status in ("completed", "partial", "failed"):
            return detail
        time.sleep(poll_interval)
    detail["status"] = detail.get("status") or "timeout"
    return detail


def find_discovered_repository(client, connection_id, repository_match):
    ingestion = ingestion_url_from_env()
    ingestion_client = PlatformClient(
        client.identity_url, ingestion, client.views_url, client.session_token
    )
    needle = normalize_repo_label(repository_match).lower()
    offset = 0
    while True:
        url = "%s/v1/scm/connections/%s/discovered?limit=100&offset=%d" % (
            ingestion,
            connection_id,
            offset,
        )
        data = ingestion_client.get_json(url)
        rows = data.get("repositories") or []
        for row in rows:
            full_name = (row.get("full_name") or normalize_repo_label(row.get("clone_url") or "")).lower()
            if full_name == needle:
                return row
        total = int(data.get("total") or 0)
        offset += len(rows)
        if not rows or offset >= total:
            break
    return None


def import_discovered_branches(client, connection_id, discovered_repo_id, branch_names):
    ingestion = ingestion_url_from_env()
    ingestion_client = PlatformClient(
        client.identity_url, ingestion, client.views_url, client.session_token
    )
    body = {
        "repositories": [
            {
                "discovered_repo_id": discovered_repo_id,
                "branches": list(branch_names or []),
                "trigger_events": ["push"],
            }
        ]
    }
    return ingestion_client.post_json(
        "%s/v1/scm/connections/%s/import" % (ingestion, connection_id),
        body,
    )


def wait_for_scm_import(client, import_run_id, timeout_sec=180, poll_interval=5):
    ingestion = ingestion_url_from_env()
    ingestion_client = PlatformClient(
        client.identity_url, ingestion, client.views_url, client.session_token
    )
    started = time.time()
    last_status = None
    detail = {}
    while time.time() - started < timeout_sec:
        detail = ingestion_client.get_json(
            "%s/v1/scm/imports/%s" % (ingestion, import_run_id)
        )
        status = (detail.get("status") or "").lower()
        if status != last_status:
            print(
                "  scm import status=%s imported=%s failed=%s"
                % (
                    status or "unknown",
                    detail.get("total_imported"),
                    detail.get("total_failed"),
                ),
                flush=True,
            )
            last_status = status
        if status in ("completed", "partial", "failed"):
            return detail
        time.sleep(poll_interval)
    detail["status"] = detail.get("status") or "timeout"
    return detail


def ensure_branches_via_scm_import(client, repository_match, required_branches):
    """Sync SCM discovery and import selected branches into the runtime catalog."""
    required = [b.strip() for b in (required_branches or []) if b and b.strip()]
    if not required:
        return False

    connections = list_scm_connections(client)
    if not connections:
        print(
            "  WARNING: no Testable SCM connection — link GitHub in the QA UI "
            "(Code → Linked) for the same account as your session repo.",
            flush=True,
        )
        return False

    github_connections = [
        c for c in connections if (c.get("provider") or "").lower() == "github"
    ]
    if not github_connections:
        github_connections = connections

    repo_owner = ""
    if "/" in repository_match:
        repo_owner = repository_match.split("/", 1)[0].strip().lower()

    for conn in github_connections:
        connection_id = conn.get("id")
        if not connection_id:
            continue
        username = conn.get("provider_username") or conn.get("provider") or "scm"
        if repo_owner and username.lower() != repo_owner:
            print(
                "  HINT: Testable SCM is connected as %r but the session repo owner is %r — "
                "use the same GitHub account in the QA UI (Code → Linked) as on the Branches tab."
                % (username, repo_owner),
                flush=True,
            )
        print(
            "  scm sync for connection %s (%s)..."
            % (connection_id, username),
            flush=True,
        )
        try:
            sync_resp = trigger_scm_sync(client, connection_id)
        except Exception as exc:
            print("  scm sync trigger failed: %s" % exc, flush=True)
            continue
        sync_id = sync_resp.get("sync_id")
        if sync_id:
            wait_for_scm_sync(
                client,
                sync_id,
                timeout_sec=int(os.environ.get("SCM_SYNC_TIMEOUT_SEC", "120")),
            )

        discovered = find_discovered_repository(client, connection_id, repository_match)
        if not discovered:
            continue

        discovered_id = discovered.get("id")
        discovered_names = {
            (b.get("name") or "").strip()
            for b in (discovered.get("branches") or [])
            if isinstance(b, dict)
        }
        discovered_names.discard("")
        import_names = [name for name in required if name in discovered_names]
        if not import_names:
            import_names = list(required)

        print(
            "  scm import: registering %d branch(es) for %s via discovered repo %s"
            % (len(import_names), repository_match, discovered_id),
            flush=True,
        )
        try:
            import_resp = import_discovered_branches(
                client, connection_id, discovered_id, import_names
            )
        except Exception as exc:
            print("  scm import request failed: %s" % exc, flush=True)
            continue
        import_run_id = import_resp.get("import_run_id")
        if not import_run_id:
            continue
        result = wait_for_scm_import(
            client,
            import_run_id,
            timeout_sec=int(os.environ.get("SCM_IMPORT_TIMEOUT_SEC", "180")),
        )
        if (result.get("status") or "").lower() in ("completed", "partial"):
            if int(result.get("total_imported") or 0) > 0:
                return True
    return False

def ensure_project(client, name, clone_url, default_branch):
    projects = client.get_json("%s/v1/projects" % client.runtime_url)
    if projects.get("projects"):
        return None
    body = {
        "name": name,
        "clone_url": clone_url,
        "branch_name": default_branch,
        "scm_provider": "github",
    }
    print("  creating project '%s'..." % name)
    return client.post_json("%s/v1/projects" % client.runtime_url, body)


def clone_url_for_repository_match(repository_match):
    """Build a GitHub clone URL from owner/repo slug."""
    slug = (repository_match or "").strip().rstrip("/")
    if slug.endswith(".git"):
        slug = slug[:-4]
    if not slug:
        return ""
    if slug.startswith("http://") or slug.startswith("https://"):
        return slug if slug.endswith(".git") else slug + ".git"
    return "https://github.com/%s.git" % slug


def provision_project_for_repo(client, name, clone_url, default_branch):
    """Register a GitHub repo as a Testable project (always POST, even if other projects exist)."""
    body = {
        "name": name,
        "clone_url": clone_url,
        "branch_name": default_branch,
        "scm_provider": "github",
    }
    print("  registering repo %s into Testable catalog..." % normalize_repo_label(clone_url), flush=True)
    return client.post_json("%s/v1/projects" % client.runtime_url, body)


def _catalog_needs_provisioning(exc):
    msg = str(exc).lower()
    return "no projects found" in msg or "not found" in msg


def refresh_branches(client, repository_id):
    url = "%s/v1/repositories/%s/branches/refresh" % (client.runtime_url, repository_id)
    return client.post_json(url, {})


def repository_matches_slug(repo, repository_match):
    """True when a Testable repository record matches owner/repo slug."""
    label = normalize_repo_label(repo.get("clone_url") or repo.get("url") or "").lower()
    needle = normalize_repo_label(repository_match).lower()
    return bool(label and needle and label == needle)


def find_repository_candidates(client, repository_match, project_list=None):
    """Return (project, repository) pairs matching *repository_match* across all projects."""
    if project_list is None:
        projects_resp = client.get_json("%s/v1/projects" % client.runtime_url)
        project_list = projects_resp.get("projects") or []
    candidates = []
    for project in project_list:
        pid = project["id"]
        repos_resp = client.get_json(
            "%s/v1/projects/%s/repositories" % (client.runtime_url, pid)
        )
        repo_list = repos_resp.get("repositories") or repos_resp.get("items") or []
        for repo in repo_list:
            if repository_matches_slug(repo, repository_match):
                candidates.append((project, repo))
    return candidates


def list_connected_repositories(client, project_list=None):
    """Return deduplicated repositories connected in Testable QA for this account."""
    if project_list is None:
        projects_resp = client.get_json("%s/v1/projects" % client.runtime_url)
        project_list = projects_resp.get("projects") or []
    seen = set()
    rows = []
    for project in project_list:
        pid = project.get("id")
        pname = project.get("name")
        repos_resp = client.get_json(
            "%s/v1/projects/%s/repositories" % (client.runtime_url, pid)
        )
        repo_list = repos_resp.get("repositories") or repos_resp.get("items") or []
        for repo in repo_list:
            label = normalize_repo_label(repo.get("clone_url") or repo.get("url") or "")
            if not label:
                continue
            rid = repo.get("id") or ""
            dedupe_key = (label.lower(), rid)
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            rows.append({
                "label": label,
                "project_name": pname,
                "project_id": pid,
                "repository_id": rid,
            })
    rows.sort(key=lambda row: (row["label"].lower(), (row.get("project_name") or "").lower()))
    return rows


def rank_qa_repos_for_branches(client, connected_repos, branch_names):
    """Rank connected QA repos by how many required branches appear in each catalog."""
    branch_names = [b.strip() for b in (branch_names or []) if b and b.strip()]
    ranked = []
    for row in connected_repos or []:
        label = row.get("label")
        if not label:
            continue
        entry = dict(row)
        try:
            catalog = resolve_catalog(
                client,
                None,
                label,
                required_branches=branch_names,
            )
            ready = [name for name in branch_names if name in catalog["branches"]]
            entry["ready_count"] = len(ready)
            entry["ready"] = ready
            entry["catalog_total"] = catalog.get("catalog_total") or len(catalog["branches"])
            entry["repository_label"] = catalog.get("repository_label") or label
        except RuntimeError:
            entry["ready_count"] = 0
            entry["ready"] = []
            entry["catalog_total"] = 0
            entry["repository_label"] = label
        ranked.append(entry)
    ranked.sort(
        key=lambda row: (row.get("ready_count", 0), row.get("catalog_total", 0)),
        reverse=True,
    )
    return ranked


def fetch_repository_branches(client, repository_id, max_pages=20):
    """Fetch branch catalog for a repository (handles paginated responses)."""
    branch_map = {}
    total_reported = None
    per_page = int(os.environ.get("CATALOG_BRANCHES_PER_PAGE", "100"))
    for page in range(1, max_pages + 1):
        url = "%s/v1/repositories/%s/branches?page=%d&per_page=%d" % (
            client.runtime_url,
            repository_id,
            page,
            per_page,
        )
        resp = client.get_json(url)
        branch_list = resp.get("branches") or resp.get("items") or []
        if resp.get("total") is not None:
            total_reported = int(resp.get("total"))
        for branch in branch_list:
            name = branch.get("name")
            if name:
                branch_map[name] = branch
        if not branch_list:
            break
        if total_reported is not None and len(branch_map) >= total_reported:
            break
        if len(branch_list) < per_page and (
            total_reported is None or len(branch_map) >= total_reported
        ):
            break
    return branch_map, total_reported


def _pick_repository_candidate(candidates, client, project_id=None, project_name=None, required_branches=None):
    """Choose the best project/repository pair for whitebox runs."""
    if not candidates:
        return None
    required = list(required_branches or [])

    def _coverage(project_repo):
        _project, repo = project_repo
        branch_map, _total = fetch_repository_branches(client, repo["id"])
        if not required:
            return len(branch_map), branch_map
        found = sum(1 for name in required if name in branch_map)
        return found, branch_map

    narrowed = list(candidates)
    if project_id:
        by_id = [item for item in narrowed if item[0].get("id") == project_id]
        if by_id:
            narrowed = by_id
    if project_name and len(narrowed) > 1:
        pname = project_name.strip().lower()
        by_name = [
            item for item in narrowed
            if (item[0].get("name") or "").strip().lower() == pname
        ]
        if by_name:
            narrowed = by_name

    scored = []
    for item in narrowed:
        found_count, branch_map = _coverage(item)
        scored.append((found_count, len(branch_map), item, branch_map))
    scored.sort(key=lambda row: (row[0], row[1]), reverse=True)
    _found, _total, chosen, _branch_map = scored[0]
    return chosen


def catalog_branch_hints(client, repository_match, required_branches, catalog_branch_map=None, github_branch_names=None):
    """Explain likely catalog/GitHub mismatches for Stage 2 whitebox."""
    hints = []
    required = list(required_branches or [])
    catalog_branch_map = catalog_branch_map or {}
    catalog_found = [name for name in required if name in catalog_branch_map]
    catalog_missing = [name for name in required if name not in catalog_branch_map]

    if github_branch_names is not None:
        gh_set = set(github_branch_names)
        gh_found = [name for name in required if name in gh_set]
        if len(gh_found) == len(required) and catalog_missing:
            hints.append(
                "GitHub repo %s has all %d required branch(es), but the QA-connected repo %s only lists %d/%d in its Testable catalog — branch discovery may still be running or reconnect GitHub for that repo in Testable QA."
                % (repository_match, len(required), repository_match, len(catalog_found), len(required))
            )

    if not catalog_missing:
        return hints

    projects_resp = client.get_json("%s/v1/projects" % client.runtime_url)
    project_list = projects_resp.get("projects") or []
    for project in project_list:
        repos_resp = client.get_json(
            "%s/v1/projects/%s/repositories" % (client.runtime_url, project["id"])
        )
        repo_list = repos_resp.get("repositories") or repos_resp.get("items") or []
        for repo in repo_list:
            label = normalize_repo_label(repo.get("clone_url") or repo.get("url") or "")
            if repository_matches_slug(repo, repository_match):
                continue
            branch_map, _total = fetch_repository_branches(client, repo["id"])
            alt_found = [name for name in required if name in branch_map]
            if len(alt_found) >= len(required):
                hints.append(
                    "Required branches appear under Testable project %r / repo %s, but Stage 2 is querying QA repo %s — select %s in the **Testable QA repository** dropdown on the Whitebox tab."
                    % (project.get("name"), label, repository_match, label)
                )
                return hints
    return hints


def resolve_catalog(client, project_id, repository_match, required_branches=None, project_name=None):
    projects_resp = client.get_json("%s/v1/projects" % client.runtime_url)
    project_list = projects_resp.get("projects") or []
    if not project_list:
        raise RuntimeError("No projects found for this user")

    candidates = find_repository_candidates(client, repository_match, project_list)
    if not candidates:
        available = []
        for project in project_list:
            repos_resp = client.get_json(
                "%s/v1/projects/%s/repositories" % (client.runtime_url, project["id"])
            )
            repo_list = repos_resp.get("repositories") or repos_resp.get("items") or []
            for repo in repo_list:
                available.append(
                    "%s (%s)" % (
                        normalize_repo_label(repo.get("clone_url")),
                        project.get("name"),
                    )
                )
        raise RuntimeError(
            "Repository '%s' not found in any Testable project. Available: %s"
            % (repository_match, available)
        )

    chosen = _pick_repository_candidate(
        candidates,
        client,
        project_id=project_id,
        project_name=project_name,
        required_branches=required_branches,
    )
    project, repository = chosen
    branch_map, catalog_total = fetch_repository_branches(client, repository["id"])
    if catalog_total is not None and catalog_total != len(branch_map):
        print(
            "  WARNING: catalog reported total=%d but fetched %d branch records"
            % (catalog_total, len(branch_map)),
            flush=True,
        )
    return {
        "project_id": project["id"],
        "project_name": project.get("name"),
        "repository_id": repository["id"],
        "repository_label": normalize_repo_label(repository.get("clone_url")),
        "default_branch": repository.get("default_branch"),
        "branches": branch_map,
        "catalog_total": catalog_total,
    }


def preview_catalog_status(client, repository_match, branch_names, project_id=None, project_name=None):
    """Lightweight Stage 2 readiness check for UI (no branch refresh)."""
    branch_names = [b.strip() for b in (branch_names or []) if b and b.strip()]
    catalog = resolve_catalog(
        client,
        project_id,
        repository_match,
        required_branches=branch_names,
        project_name=project_name,
    )
    ready = [name for name in branch_names if name in catalog["branches"]]
    missing = [name for name in branch_names if name not in catalog["branches"]]
    return {
        "project_name": catalog.get("project_name"),
        "project_id": catalog.get("project_id"),
        "repository_label": catalog.get("repository_label"),
        "repository_id": catalog.get("repository_id"),
        "catalog_total": catalog.get("catalog_total", len(catalog["branches"])),
        "ready": ready,
        "missing": missing,
    }


def wait_for_branches(
    client,
    repository_id,
    required_names,
    poll_interval=10,
    timeout_sec=300,
    allow_partial=False,
    refresh_every_sec=None,
):
    """Poll Testable catalog until required branches appear or timeout.

    When allow_partial is True, missing branches are only accepted after the full
    timeout elapses (not on the first branch found).
    """
    required_names = list(required_names or [])
    if not required_names:
        return {}

    started = time.time()
    branch_map = {}
    last_refresh = started
    if refresh_every_sec is None:
        refresh_every_sec = int(os.environ.get("BRANCH_REFRESH_EVERY_SEC", "30"))
    last_reported = -1

    def _maybe_refresh():
        nonlocal last_refresh
        if refresh_every_sec <= 0:
            return
        now = time.time()
        if now - last_refresh >= refresh_every_sec:
            try:
                refresh_branches(client, repository_id)
            except Exception as exc:
                print("  branch refresh trigger: %s" % exc, flush=True)
            last_refresh = now

    while time.time() - started < timeout_sec:
        _maybe_refresh()
        try:
            branch_map, catalog_total = fetch_repository_branches(client, repository_id)
        except Exception as exc:
            print("  branch poll error: %s (retrying...)" % exc, flush=True)
            time.sleep(poll_interval)
            continue
        found = [n for n in required_names if n in branch_map]
        missing = [n for n in required_names if n not in branch_map]
        if not missing:
            print(
                "  catalog sync: all %d branches ready (catalog total=%s)"
                % (len(required_names), catalog_total if catalog_total is not None else len(branch_map)),
                flush=True,
            )
            return branch_map
        if len(found) != last_reported:
            print(
                "  catalog sync: %d/%d branches ready (catalog total=%s, missing: %s)"
                % (
                    len(found),
                    len(required_names),
                    catalog_total if catalog_total is not None else len(branch_map),
                    missing,
                ),
                flush=True,
            )
            last_reported = len(found)
        print("  waiting for branches (missing: %s)..." % missing, flush=True)
        time.sleep(poll_interval)

    found = [n for n in required_names if n in branch_map]
    missing = [n for n in required_names if n not in branch_map]
    elapsed = int(time.time() - started)
    if allow_partial and found:
        print(
            "  partial catalog after %ss: %d/%d branches ready (missing: %s)"
            % (elapsed, len(found), len(required_names), missing),
            flush=True,
        )
    elif missing:
        print(
            "  catalog sync timeout (%ss): %d/%d branches ready (missing: %s)"
            % (elapsed, len(found), len(required_names), missing),
            flush=True,
        )
    return branch_map


def extract_task_failures(summary):
    """Return structured failures from a Testable run summary payload."""
    if not summary:
        return []

    failures = []

    def _add(name, status, message=""):
        label = (name or "unknown").strip() or "unknown"
        failures.append({
            "name": label,
            "status": (status or "failed").strip() or "failed",
            "message": (message or "")[:500],
        })

    for key in ("failed_task_details", "failures", "task_failures"):
        items = summary.get(key)
        if not isinstance(items, list) or not items:
            continue
        for item in items:
            if isinstance(item, dict):
                _add(
                    item.get("name") or item.get("task") or item.get("tool") or item.get("task_name"),
                    item.get("status") or "failed",
                    item.get("message") or item.get("error") or item.get("detail"),
                )
            elif isinstance(item, str) and item.strip():
                _add(item.strip(), "failed")
        if failures:
            return failures

    tasks = summary.get("tasks") or summary.get("task_results") or []
    if isinstance(tasks, list):
        for task in tasks:
            if not isinstance(task, dict):
                continue
            status = (task.get("status") or "").lower()
            if status in ("failed", "error", "partial", "timeout", "cancelled"):
                _add(
                    task.get("name") or task.get("task_name") or task.get("tool"),
                    status,
                    task.get("message") or task.get("error") or task.get("detail"),
                )
    return failures


def format_task_failure_detail(task_failures, max_items=5):
    """Compact human-readable summary of failed tasks."""
    if not task_failures:
        return ""
    parts = []
    for item in task_failures[:max_items]:
        name = item.get("name") or "task"
        msg = (item.get("message") or item.get("status") or "").strip()
        parts.append("%s (%s)" % (name, msg) if msg else name)
    text = ", ".join(parts)
    if len(task_failures) > max_items:
        text += " +%d more" % (len(task_failures) - max_items)
    return text


def is_admission_delayed(exc):
    msg = str(exc).lower()
    return (
        "rate_limited" in msg
        or "quota_exceeded" in msg
        or "admission delayed" in msg
    )


def create_run(client, project_id, repository_id, branch_id, commit_sha):
    body = {
        "project_id": project_id,
        "repository_id": repository_id,
        "branch_id": branch_id,
        "commit_sha": commit_sha,
        "trigger_type": "manual",
    }
    return client.post_json("%s/v1/runs" % client.runtime_url, body)


def create_run_with_retry(client, project_id, repository_id, branch_id, commit_sha,
                          max_retries, retry_delay_sec):
    last_exc = None
    for attempt in range(1, max_retries + 1):
        try:
            return create_run(client, project_id, repository_id, branch_id, commit_sha)
        except Exception as exc:
            last_exc = exc
            if not is_admission_delayed(exc) or attempt >= max_retries:
                raise
            wait = retry_delay_sec * attempt
            print(
                "  quota/rate limit (attempt %d/%d) — waiting %ds before retry..."
                % (attempt, max_retries, wait),
                flush=True,
            )
            time.sleep(wait)
    raise last_exc


def get_run_summary(client, run_id, tenant_id):
    params = urllib.parse.urlencode({"tenant_id": tenant_id})
    return client.get_json("%s/v1/runs/%s/summary?%s" % (client.views_url, run_id, params))


def wait_for_whitebox_run(client, run_id, tenant_id, poll_interval, timeout_sec, require_completed):
    """Poll until whitebox execution finishes. Reports require a completed run by default."""
    started = time.time()
    while True:
        if time.time() - started > timeout_sec:
            raise RuntimeError("Timeout waiting for whitebox run %s" % run_id)
        summary = get_run_summary(client, run_id, tenant_id)
        status = (summary.get("status") or "").lower()
        total = summary.get("total_tasks") or 0
        done = summary.get("completed_tasks") or 0
        failed = summary.get("failed_tasks") or 0
        print(
            "    whitebox status=%s tasks=%s/%s failed=%s"
            % (status, done, total, failed),
            flush=True,
        )
        if status in IN_FLIGHT_STATUSES:
            time.sleep(poll_interval)
            continue
        if status not in TERMINAL_STATUSES:
            time.sleep(poll_interval)
            continue
        if require_completed and status != "completed":
            raise RuntimeError(
                "Whitebox run ended with status '%s' — taxonomy report not generated "
                "(set REQUIRE_RUN_COMPLETED=false to save after whitebox finishes, even if status is failed/partial)"
                % status
            )
        if status in ("failed", "partial") and total > 0:
            print(
                "    whitebox finished (status=%s, tasks=%s/%s, tool_failures=%s) — proceeding to taxonomy"
                % (status, done, total, failed),
                flush=True,
            )
        return summary


def fetch_taxonomy_gate(client, run_id, tenant_id):
    params = urllib.parse.urlencode({"tenant_id": tenant_id})
    return client.get_json(
        "%s/v1/runs/%s/taxonomy-gate?%s" % (client.views_url, run_id, params))


def wait_for_taxonomy_ready(client, run_id, tenant_id, poll_interval, timeout_sec):
    """Poll taxonomy gate until gate_status is completed (matches UI export readiness)."""
    started = time.time()
    while True:
        if time.time() - started > timeout_sec:
            raise RuntimeError("Timeout waiting for taxonomy gate on run %s" % run_id)
        taxonomy = fetch_taxonomy_gate(client, run_id, tenant_id)
        gate_status = (taxonomy.get("gate_status") or "").lower()
        has_types = bool(taxonomy.get("testing_types"))
        print("    taxonomy gate_status=%s types=%s" % (gate_status, has_types), flush=True)
        if gate_status == "completed" and has_types:
            return taxonomy
        time.sleep(poll_interval)


def fetch_taxonomy(client, run_id, tenant_id):
    params = urllib.parse.urlencode({"tenant_id": tenant_id})
    json_url = "%s/v1/runs/%s/taxonomy-gate?%s" % (client.views_url, run_id, params)
    xml_url = "%s/v1/runs/%s/taxonomy-gate.xml?%s" % (client.views_url, run_id, params)
    taxonomy_json = fetch_taxonomy_gate(client, run_id, tenant_id)
    taxonomy_xml = client._request("GET", xml_url, accept="application/xml")
    return taxonomy_json, taxonomy_xml


def ensure_dir(path):
    if not os.path.isdir(path):
        os.makedirs(path)


def export_html_reports(batch_dir):
    """Build UI-format HTML from saved taxonomy-gate.json files."""
    html_script = os.path.join(ROOT, "tools", "export_taxonomy_html.ts")
    web_console = os.environ.get(
        "WEB_CONSOLE_DIR",
        os.path.join(os.path.dirname(ROOT), "ai-testable-platform", "frontend", "web-console"),
    )
    if not os.path.isfile(html_script):
        print("  WARNING: HTML export script not found: %s" % html_script, flush=True)
        return False
    if not os.path.isdir(web_console):
        print("  WARNING: web-console not found: %s" % web_console, flush=True)
        return False
    print("\n=== Export HTML reports ===", flush=True)
    npx = shutil.which("npx")
    if not npx and sys.platform == "win32":
        npx = shutil.which("npx.cmd")
    if not npx:
        print("  WARNING: npx not found on PATH", flush=True)
        return False
    result = subprocess.run(
        [npx, "--yes", "tsx", "--tsconfig", "tsconfig.json", html_script, os.path.abspath(batch_dir)],
        cwd=web_console,
        shell=False,
    )
    return result.returncode == 0


def prune_to_html_only(batch_dir):
    """Keep manifest.json and *.html per branch; remove intermediate JSON/XML."""
    removed = 0
    for name in os.listdir(batch_dir):
        branch_dir = os.path.join(batch_dir, name)
        if not os.path.isdir(branch_dir):
            continue
        for fn in os.listdir(branch_dir):
            if fn.endswith(".html"):
                continue
            path = os.path.join(branch_dir, fn)
            if os.path.isfile(path):
                os.remove(path)
                removed += 1
    if removed:
        print("  removed %d non-HTML artifact(s)" % removed, flush=True)


def save_report(output_dir, branch_name, run_id, summary, taxonomy_json, taxonomy_xml, collected_at=None):
    folder_name = report_folder_name(branch_name, collected_at)
    branch_dir = os.path.join(output_dir, folder_name)
    ensure_dir(branch_dir)
    with open(os.path.join(branch_dir, "run_id.txt"), "w", encoding="utf-8") as fh:
        fh.write(run_id)
    with open(os.path.join(branch_dir, "run_summary.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)
    with open(os.path.join(branch_dir, "taxonomy-gate.json"), "w", encoding="utf-8") as fh:
        json.dump(taxonomy_json, fh, indent=2)
    with open(os.path.join(branch_dir, "taxonomy-gate.xml"), "wb") as fh:
        if isinstance(taxonomy_xml, bytes):
            fh.write(taxonomy_xml)
        else:
            fh.write(str(taxonomy_xml).encode("utf-8"))
    return folder_name


def extract_gate_score(taxonomy_json):
    for key in ("pipeline_gate_score", "gate_score", "overall_score", "headline_score"):
        if key in taxonomy_json and taxonomy_json[key] is not None:
            return taxonomy_json[key]
    return taxonomy_json.get("score")


def parse_args():
    parser = argparse.ArgumentParser(description="Run SA branches and collect taxonomy reports")
    parser.add_argument("--env-file", default=os.path.join(ROOT, ".env.local"))
    parser.add_argument("--branches", default=None, help="Comma-separated branch names")
    parser.add_argument("--dry-run", action="store_true", help="Resolve catalog only, do not run")
    parser.add_argument("--skip-login", action="store_true", help="Use SESSION_TOKEN env var")
    parser.add_argument("--ensure-project", action="store_true", help="Create project if none exists")
    parser.add_argument("--refresh-branches", action="store_true", help="Refresh branch catalog before runs")
    parser.add_argument(
        "--allow-partial-branches",
        action="store_true",
        help="Run only branches present in catalog (skip missing)",
    )
    parser.add_argument(
        "--export-html",
        action="store_true",
        default=os.environ.get("EXPORT_HTML", "true").lower() == "true",
        help="Generate taxonomy-gate HTML after batch (default: true)",
    )
    parser.add_argument(
        "--no-export-html",
        action="store_false",
        dest="export_html",
        help="Skip HTML export",
    )
    parser.add_argument(
        "--html-only",
        action="store_true",
        default=os.environ.get("HTML_ONLY", "false").lower() == "true",
        help="After HTML export, delete JSON/XML/run_id files (keep .html + manifest)",
    )
    return parser.parse_args()


def main():
    rc, _ = main_with_args(parse_args())
    return rc


def parse_sa_results(html):
    sa_start = html.find("<h2>Structural Analysis</h2>")
    if sa_start < 0:
        return {}
    section = html[sa_start:]
    cyclo_start = section.find("<h3>Cyclomatic Complexity</h3>")
    if cyclo_start < 0:
        return {}
    section = section[cyclo_start:]
    next_h2 = section.find("<h2>", 1)
    if next_h2 > 0:
        section = section[:next_h2]
    return {name.strip(): result.strip().lower() for name, result in ROW_RE.findall(section)}


def infer_from_folder(path):
    folder = os.path.basename(os.path.dirname(path))
    abbrev, branch_type = infer_metric_from_report_folder(folder)
    if abbrev and branch_type:
        return abbrev, branch_type
    base = branch_name_from_report_folder(folder)
    parts = base.split("_")
    if len(parts) >= 3 and parts[0] == "SA":
        return parts[1], parts[2]
    return None, None


def verify_taxonomy_file(html_path, target_abbrev, branch_type):
    with open(html_path, encoding="utf-8") as fh:
        html = fh.read()
    results = parse_sa_results(html)
    if not results:
        return False, "Structural Analysis / Cyclomatic Complexity section not found"
    target_cls = ABBREV_TO_CLASSIFICATION[target_abbrev]
    expect_target_fail = branch_type == "Bug"
    lines = []
    ok = True
    for cls, abbrev in sorted(CLASSIFICATION_TO_ABBREV.items(), key=lambda x: x[1]):
        result = results.get(cls, "missing")
        is_target = abbrev == target_abbrev
        if is_target:
            if expect_target_fail:
                if result != "fail":
                    ok = False
                    lines.append("  TARGET %s (%s): %s (expected FAIL)" % (abbrev, cls, result.upper()))
                else:
                    lines.append("  TARGET %s (%s): FAIL (ok)" % (abbrev, cls))
            else:
                if result == "fail":
                    ok = False
                    lines.append("  TARGET %s (%s): FAIL (expected PASS/WARN)" % (abbrev, cls))
                else:
                    lines.append("  TARGET %s (%s): %s (ok)" % (abbrev, cls, result.upper()))
        else:
            lines.append("  other  %s (%s): %s" % (abbrev, cls, result.upper()))
    return ok, "\n".join(lines)


def verify_taxonomy_dir(batch_dir):
    """Verify all HTML reports under a batch directory. Returns failure count."""
    failed = 0
    for name in sorted(os.listdir(batch_dir)):
        folder = os.path.join(batch_dir, name)
        if not os.path.isdir(folder):
            continue
        for fn in os.listdir(folder):
            if not fn.endswith(".html"):
                continue
            path = os.path.join(folder, fn)
            abbrev, branch_type = infer_from_folder(path)
            if not abbrev or not branch_type:
                print("%s: cannot infer metric/type" % path)
                failed += 1
                continue
            ok, detail = verify_taxonomy_file(path, abbrev, branch_type)
            print("\n%s (target=%s, type=%s) %s" % (path, abbrev, branch_type, "PASS" if ok else "FAIL"))
            print(detail)
            if not ok:
                failed += 1
    return failed


def run_taxonomy_batch(env_file=None, branches_csv=None, dry_run=False, refresh_branches=False,
                       allow_partial_branches=False, export_html=True, html_only=True,
                       auth_email=None, auth_password=None, repository_match=None,
                       progress_callback=None, result_meta=None):
    """Notebook-friendly wrapper. Returns (exit_code, batch_output_dir)."""
    env_file = env_file or os.path.join(ROOT, ".env.local")
    load_env(env_file)
    branches = (branches_csv or os.environ.get("BRANCHES", "")).split(",")
    branches = [b.strip() for b in branches if b.strip()]
    args = argparse.Namespace(
        env_file=env_file,
        branches=",".join(branches),
        dry_run=dry_run,
        skip_login=False,
        ensure_project=False,
        refresh_branches=refresh_branches,
        allow_partial_branches=allow_partial_branches,
        export_html=export_html,
        html_only=html_only,
        auth_email=auth_email,
        auth_password=auth_password,
        repository_match=repository_match,
    )
    return main_with_args(args, progress_callback=progress_callback, result_meta=result_meta)


def main_with_args(args, progress_callback=None, result_meta=None):
    """Core batch logic extracted for programmatic use."""
    def _progress(phase, current, total, branch, message):
        if progress_callback:
            progress_callback(phase, current, total, branch, message)

    load_env(args.env_file)
    identity_url = os.environ.get("IDENTITY_URL", "http://localhost:8000")
    runtime_url = os.environ.get("RUNTIME_URL", "http://localhost:8002")
    views_url = os.environ.get("VIEWS_URL", "http://localhost:8003")
    email = getattr(args, "auth_email", None)
    password = getattr(args, "auth_password", None)
    use_env_auth = email is None and password is None
    if email is None:
        email = os.environ.get("AUTH_EMAIL")
    if password is None:
        password = os.environ.get("AUTH_PASSWORD")
    if not use_env_auth and (not (email or "").strip() or not password):
        print("ERROR: UI auth_email/auth_password required when overriding .env.local", file=sys.stderr)
        return 1, None
    tenant_id = os.environ.get("TENANT_ID")
    project_id = os.environ.get("PROJECT_ID") or None
    repository_match = (
        getattr(args, "repository_match", None)
        or os.environ.get("REPOSITORY_MATCH", "")
    ).strip()
    if not repository_match:
        print(
            "ERROR: repository_match required — select a GitHub repo in the UI "
            "or set REPOSITORY_MATCH for CLI/notebook runs.",
            file=sys.stderr,
        )
        return 1, None
    branches = (args.branches or os.environ.get(
        "BRANCHES", "SA_bug_2.6,SA_bugFX_2.6,SA_TCC_2.6,SA_CC_2.6")).split(",")
    branches = [b.strip() for b in branches if b.strip()]
    output_root = os.environ.get("OUTPUT_DIR", "taxonomy_reports")
    poll_interval = int(os.environ.get("POLL_INTERVAL_SEC", "30"))
    poll_timeout = int(os.environ.get("POLL_TIMEOUT_SEC", "3600"))
    continue_on_failure = os.environ.get("CONTINUE_ON_FAILURE", "true").lower() == "true"
    require_run_completed = os.environ.get("REQUIRE_RUN_COMPLETED", "true").lower() == "true"
    taxonomy_poll_timeout = int(os.environ.get("TAXONOMY_POLL_TIMEOUT_SEC", str(poll_timeout)))
    branch_delay_sec = int(os.environ.get("BRANCH_DELAY_SEC", "0"))
    run_create_max_retries = int(os.environ.get("RUN_CREATE_MAX_RETRIES", "15"))
    run_create_retry_sec = int(os.environ.get("RUN_CREATE_RETRY_SEC", "120"))
    prefer_github_commit = os.environ.get("PREFER_GITHUB_COMMIT", "true").lower() == "true"

    print("=== Authenticate ===", flush=True)
    _progress("auth", 0, 1, "", "authenticating")
    if args.skip_login:
        token = os.environ.get("SESSION_TOKEN")
        if not token:
            print("ERROR: SESSION_TOKEN required with --skip-login", file=sys.stderr)
            return 1, None
    else:
        if not email or not password:
            print("ERROR: AUTH_EMAIL and AUTH_PASSWORD required", file=sys.stderr)
            return 1, None
        if "localhost" in identity_url or "127.0.0.1" in identity_url:
            dev_verify(identity_url, email)
        token = login(identity_url, email, password)
        print("  logged in as %s" % email, flush=True)
    _progress("auth", 1, 1, "", "authenticated")

    client = PlatformClient(identity_url, runtime_url, views_url, token)
    env_tenant_id = tenant_id
    try:
        tenant_id = resolve_tenant_id(client)
        print("  tenant_id=%s (from session)" % tenant_id, flush=True)
        if env_tenant_id and env_tenant_id != tenant_id:
            print("  WARNING: TENANT_ID in .env.local differs from session", flush=True)
    except Exception as exc:
        if not tenant_id:
            print("ERROR: could not resolve tenant: %s" % exc, file=sys.stderr)
            return 1, None
        print("  WARNING: using TENANT_ID from env: %s" % exc, flush=True)

    if args.ensure_project:
        clone_url = os.environ.get("CLONE_URL", "https://github.com/%s.git" % repository_match)
        seed_branch = resolve_github_default_branch(repository_match)
        ensure_project(
            client,
            os.environ.get("PROJECT_NAME", "Metric Evaluation SA"),
            clone_url,
            seed_branch,
        )

    print("\n=== Resolve catalog ===")
    _progress("catalog", 0, 1, "", "resolving catalog")
    project_name = os.environ.get("PROJECT_NAME") or None
    try:
        catalog = resolve_catalog(
            client,
            project_id,
            repository_match,
            required_branches=branches,
            project_name=project_name,
        )
    except RuntimeError:
        print(
            "ERROR: repository %r is not connected in the Testable QA app yet. "
            "Connect/sync it in the QA application, then re-run Stage 2."
            % repository_match,
            file=sys.stderr,
        )
        return 1, None
    print(
        "  catalog snapshot: %d branch(es) indexed for this repository"
        % len(catalog.get("branches") or {}),
        flush=True,
    )
    if args.refresh_branches:
        print("  refreshing branch catalog...")
        try:
            refresh_branches(client, catalog["repository_id"])
        except Exception as exc:
            print("  refresh trigger: %s" % exc)
        sync_timeout = (
            int(os.environ.get("PARTIAL_BRANCH_SYNC_SEC", "120"))
            if args.allow_partial_branches
            else int(os.environ.get("BRANCH_SYNC_TIMEOUT_SEC", "300"))
        )
        catalog["branches"] = wait_for_branches(
            client,
            catalog["repository_id"],
            branches,
            timeout_sec=sync_timeout,
            allow_partial=args.allow_partial_branches,
        )
    github_branch_names = None
    if prefer_github_commit:
        try:
            from lib.github_api import list_repo_branches

            pat = os.environ.get("GITHUB_TOKEN", "").strip()
            if pat:
                github_branch_names = list_repo_branches(pat, repository_match)
        except Exception:
            github_branch_names = None
    missing = [b for b in branches if b not in catalog["branches"]]
    if missing:
        for hint in catalog_branch_hints(
            client,
            repository_match,
            branches,
            catalog_branch_map=catalog["branches"],
            github_branch_names=github_branch_names,
        ):
            print("  HINT: %s" % hint, flush=True)
    print("  project: %s (%s)" % (catalog.get("project_name"), catalog["project_id"]))
    print("  repository: %s (%s)" % (catalog.get("repository_label"), catalog["repository_id"]))

    catalog_skipped = list(missing)
    if result_meta is not None:
        result_meta["catalog_skipped"] = catalog_skipped
    if missing:
        print("  WARNING: skipping branches not in QA catalog after wait: %s" % missing)
        branches = [b for b in branches if b in catalog["branches"]]
    if not branches:
        print(
            "ERROR: none of the requested branches are in the QA catalog for %s"
            % repository_match,
            file=sys.stderr,
        )
        return 1, None
    _progress("catalog", 1, 1, "", "%d branches ready" % len(branches))
    if args.dry_run:
        print("\nDry run complete.")
        from lib.metrics import classification_label_for_branch

        dirs = {}
        for b in list(branches) + list(catalog_skipped):
            label = classification_label_for_branch(b)
            dirs[label] = os.path.join(ROOT, report_output_dir(output_root, label))
        for label, path in sorted(dirs.items()):
            print("  %s -> %s" % (label, path))
        if len(dirs) == 1:
            primary_dir = next(iter(dirs.values()))
        else:
            primary_dir = os.path.join(ROOT, output_root)
        return 0, primary_dir

    batch_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    from lib.metrics import classification_label_for_branch

    def _classification_for(branch):
        return classification_label_for_branch(branch)

    manifests = {}
    output_dirs = {}

    def _manifest_for(classification):
        if classification not in manifests:
            out_dir = os.path.join(ROOT, report_output_dir(output_root, classification))
            ensure_dir(out_dir)
            output_dirs[classification] = out_dir
            manifests[classification] = {
                "batch_id": batch_id,
                "classification": classification,
                "tenant_id": tenant_id,
                "repository": catalog.get("repository_label"),
                "project_id": catalog["project_id"],
                "repository_id": catalog["repository_id"],
                "catalog_skipped": catalog_skipped,
                "runs": [],
            }
        return manifests[classification], output_dirs[classification]

    # Pre-create a manifest per classification (including skipped branches) so the
    # reader can report SKIPPED in the correct folder.
    for _b in list(branches) + list(catalog_skipped):
        _manifest_for(_classification_for(_b))

    old_s3_active = os.environ.get("S3_SYNC_ACTIVE_BRANCHES")
    os.environ["S3_SYNC_ACTIVE_BRANCHES"] = ",".join(branches)

    print("\n=== Sequential branch runs ===")
    total_branches = len(branches)
    for idx, branch_name in enumerate(branches, start=1):
        print("\n[%d/%d] %s" % (idx, total_branches, branch_name))
        _progress("whitebox", idx - 1, total_branches, branch_name, "starting")
        manifest, output_dir = _manifest_for(_classification_for(branch_name))
        branch = catalog["branches"][branch_name]
        branch_id = branch.get("id") or branch.get("branch_id")
        if idx > 1 and branch_delay_sec > 0:
            time.sleep(branch_delay_sec)
        commit_sha = resolve_commit_sha(
            branch_name, branch, catalog.get("repository_label"), prefer_github_commit)
        if not branch_id or not commit_sha:
            if not continue_on_failure:
                return 1, output_dir
            continue
        try:
            run_resp = create_run_with_retry(
                client, catalog["project_id"], catalog["repository_id"], branch_id, commit_sha,
                run_create_max_retries, run_create_retry_sec)
            run_id = run_resp["run_id"]
            summary = wait_for_whitebox_run(
                client, run_id, tenant_id, poll_interval, poll_timeout, require_run_completed)
            task_failures = extract_task_failures(summary)
            if task_failures:
                summary = dict(summary)
                summary["task_failures"] = task_failures
            taxonomy_json = wait_for_taxonomy_ready(
                client, run_id, tenant_id, poll_interval, taxonomy_poll_timeout)
            _, taxonomy_xml = fetch_taxonomy(client, run_id, tenant_id)
            report_folder = save_report(output_dir, branch_name, run_id, summary, taxonomy_json, taxonomy_xml)
            run_entry = {
                "branch": branch_name,
                "report_folder": report_folder,
                "run_id": run_id,
                "commit_sha": commit_sha,
                "status": summary.get("status"),
                "run_status": (summary.get("status") or "").lower(),
                "total_tasks": summary.get("total_tasks") or 0,
                "completed_tasks": summary.get("completed_tasks") or 0,
                "failed_tasks": summary.get("failed_tasks") or 0,
                "task_failures": task_failures,
                "gate_score": extract_gate_score(taxonomy_json),
            }
            s3_meta = {
                "branch": branch_name,
                "commit_sha": commit_sha,
                "run_id": run_id,
                "report_folder": report_folder,
                "report_dir": os.path.join(output_dir, report_folder),
            }
            s3_wait = int(os.environ.get("S3_SYNC_WAIT_SEC", "60"))
            s3_poll = int(os.environ.get("S3_SYNC_POLL_SEC", "10"))
            try:
                from lib.s3_sync import sync_from_taxonomy_meta_with_retry

                reload_s3_credentials(args.env_file)
                s3_sync = sync_from_taxonomy_meta_with_retry(
                    s3_meta, wait_sec=s3_wait, poll_sec=s3_poll,
                )
                run_entry["s3_sync"] = {
                    "status": s3_sync.get("status"),
                    "reason": s3_sync.get("reason") or s3_sync.get("error", ""),
                    "local_path": s3_sync.get("local_path", ""),
                    "s3_prefix": s3_sync.get("s3_prefix", ""),
                }
                if s3_sync.get("status") == "AUTH":
                    print(
                        "  s3 sync: AUTH — refresh AWS creds in .env.local",
                        flush=True,
                    )
                else:
                    print(
                        "  s3 sync: status=%s %s"
                        % (s3_sync.get("status"), s3_sync.get("reason") or s3_sync.get("local_path", "")),
                        flush=True,
                    )
            except Exception as exc:
                run_entry["s3_sync"] = {"status": "ERROR", "reason": str(exc)}
                print("  s3 sync failed: %s" % exc, flush=True)
            manifest["runs"].append(run_entry)
            print("  saved to %s" % os.path.join(output_dir, report_folder))
            _progress("whitebox", idx, total_branches, branch_name, "saved run %s" % run_id)
        except Exception as exc:
            print("  FAILED: %s" % exc)
            manifest["runs"].append({"branch": branch_name, "error": str(exc)})
            _progress("whitebox", idx, total_branches, branch_name, "failed: %s" % exc)
            if not continue_on_failure:
                break

    if old_s3_active is not None:
        os.environ["S3_SYNC_ACTIVE_BRANCHES"] = old_s3_active
    else:
        os.environ.pop("S3_SYNC_ACTIVE_BRANCHES", None)

    all_runs = []
    _progress("export", 0, 1, "", "exporting taxonomy HTML")
    for classification, cls_manifest in manifests.items():
        cls_output_dir = output_dirs[classification]
        manifest_path = os.path.join(cls_output_dir, "manifest.json")
        with open(manifest_path, "w", encoding="utf-8") as fh:
            json.dump(cls_manifest, fh, indent=2)
        all_runs.extend(cls_manifest["runs"])
        cls_successful = [r for r in cls_manifest["runs"] if r.get("run_id")]
        if args.export_html and cls_successful:
            if export_html_reports(cls_output_dir) and args.html_only:
                prune_to_html_only(cls_output_dir)
    _progress("export", 1, 1, "", "HTML export complete")

    if len(output_dirs) == 1:
        primary_dir = next(iter(output_dirs.values()))
    else:
        primary_dir = os.path.join(ROOT, output_root)

    successful = [r for r in all_runs if r.get("run_id")]
    print("\n=== Done ===")
    print("Reports: %s" % primary_dir)
    _progress("done", total_branches, total_branches, "", "%d/%d runs saved" % (len(successful), total_branches))
    if not successful:
        return 1, primary_dir
    failed = [r for r in all_runs if r.get("error")]
    return (1 if failed else 0), primary_dir


if __name__ == "__main__":
    sys.exit(main())
