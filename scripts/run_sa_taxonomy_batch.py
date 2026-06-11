#!/usr/bin/env python3
"""
Run SA Structural Analysis branches sequentially on Testable platform
and collect taxonomy gate reports (JSON + XML) per branch.

Usage:
  py -3 scripts/run_sa_taxonomy_batch.py
  py -3 scripts/run_sa_taxonomy_batch.py --dry-run
  py -3 scripts/run_sa_taxonomy_batch.py --branches SA_bug_2.6,SA_CC_2.6
"""

from __future__ import print_function

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TERMINAL_STATUSES = frozenset(["completed", "failed", "partial", "cancelled"])


def load_env(path):
    if not os.path.isfile(path):
        return
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            os.environ.setdefault(key.strip(), val.strip())


class PlatformClient(object):
    def __init__(self, identity_url, runtime_url, views_url, session_token):
        self.identity_url = identity_url.rstrip("/")
        self.runtime_url = runtime_url.rstrip("/")
        self.views_url = views_url.rstrip("/")
        self.session_token = session_token

    def _request(self, method, url, body=None, accept=None):
        req = urllib.request.Request(url, method=method)
        req.add_header("Content-Type", "application/json")
        if accept:
            req.add_header("Accept", accept)
        if self.session_token:
            req.add_header("Cookie", "session_token=%s" % self.session_token)
        if body is not None:
            req.data = json.dumps(body).encode("utf-8")
        try:
            resp = urllib.request.urlopen(req, timeout=120)
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


def login(identity_url, email, password):
    url = "%s/api/v1/auth/login" % identity_url.rstrip("/")
    req = urllib.request.Request(url, method="POST")
    req.add_header("Content-Type", "application/json")
    req.data = json.dumps({"identifier": email, "password": password}).encode("utf-8")
    try:
        resp = urllib.request.urlopen(req, timeout=60)
    except urllib.error.HTTPError as e:
        raise RuntimeError("Login failed: %s" % e.read().decode("utf-8", errors="replace")) from e
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


def dev_verify(identity_url, email):
    url = "%s/v1/auth/dev-verify" % identity_url.rstrip("/")
    req = urllib.request.Request(url, method="POST")
    req.add_header("Content-Type", "application/json")
    req.data = json.dumps({"email": email}).encode("utf-8")
    try:
        urllib.request.urlopen(req, timeout=30)
    except urllib.error.HTTPError:
        pass


def resolve_commit_sha(branch_name, branch_row, repository_match):
    for key in ("head_commit_sha", "headCommitSha", "commit_sha", "tip_sha"):
        val = branch_row.get(key)
        if val:
            return val
    # Fallback: public GitHub API for branch tip
    repo = repository_match.strip().strip("/")
    if repo.endswith(".git"):
        repo = repo[:-4]
    parts = repo.split("/")
    if len(parts) >= 2:
        owner, name = parts[-2], parts[-1]
        api_url = "https://api.github.com/repos/%s/%s/git/ref/heads/%s" % (
            owner, name, urllib.parse.quote(branch_name))
        req = urllib.request.Request(api_url, headers={"Accept": "application/vnd.github+json"})
        try:
            resp = urllib.request.urlopen(req, timeout=30)
            data = json.loads(resp.read().decode("utf-8"))
            sha = data.get("object", {}).get("sha")
            if sha:
                print("  resolved commit via GitHub API: %s" % sha[:12])
                return sha
        except Exception as exc:
            print("  GitHub SHA lookup failed: %s" % exc)
    # Fallback: local git ls-remote (works when repo is cloned and remote configured)
    try:
        proc = subprocess.Popen(
            ["git", "ls-remote", "origin", "refs/heads/%s" % branch_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=ROOT,
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


def refresh_branches(client, repository_id):
    url = "%s/v1/repositories/%s/branches/refresh" % (client.runtime_url, repository_id)
    return client.post_json(url, {})


def wait_for_branches(client, repository_id, required_names, poll_interval=10, timeout_sec=300):
    started = time.time()
    branch_map = {}
    while time.time() - started < timeout_sec:
        branches_resp = client.get_json(
            "%s/v1/repositories/%s/branches" % (client.runtime_url, repository_id))
        branch_list = branches_resp.get("branches") or branches_resp.get("items") or []
        branch_map = {b.get("name"): b for b in branch_list if b.get("name")}
        missing = [n for n in required_names if n not in branch_map]
        if not missing:
            return branch_map
        print("  waiting for branches (missing: %s)..." % missing)
        time.sleep(poll_interval)
    return branch_map


def resolve_catalog(client, project_id, repository_match):
    projects = client.get_json("%s/v1/projects" % client.runtime_url)
    project_list = projects.get("projects") or []
    if not project_list:
        raise RuntimeError("No projects found for this user")
    project = None
    if project_id:
        for p in project_list:
            if p.get("id") == project_id:
                project = p
                break
        if not project:
            raise RuntimeError("PROJECT_ID not found: %s" % project_id)
    else:
        project = project_list[0]
    pid = project["id"]
    repos = client.get_json("%s/v1/projects/%s/repositories" % (client.runtime_url, pid))
    repo_list = repos.get("repositories") or repos.get("items") or []
    repository = None
    needle = repository_match.lower()
    for r in repo_list:
        label = normalize_repo_label(r.get("clone_url") or r.get("url") or "")
        name = (r.get("name") or "").lower()
        if needle in label.lower() or needle in name or label.lower() == needle:
            repository = r
            break
    if not repository:
        available = [normalize_repo_label(r.get("clone_url")) for r in repo_list]
        raise RuntimeError("Repository '%s' not found. Available: %s" % (repository_match, available))
    rid = repository["id"]
    branches_resp = client.get_json("%s/v1/repositories/%s/branches" % (client.runtime_url, rid))
    branch_list = branches_resp.get("branches") or branches_resp.get("items") or []
    branch_map = {}
    for b in branch_list:
        name = b.get("name")
        if name:
            branch_map[name] = b
    return {
        "project_id": pid,
        "project_name": project.get("name"),
        "repository_id": rid,
        "repository_label": normalize_repo_label(repository.get("clone_url")),
        "branches": branch_map,
    }


def create_run(client, project_id, repository_id, branch_id, commit_sha):
    body = {
        "project_id": project_id,
        "repository_id": repository_id,
        "branch_id": branch_id,
        "commit_sha": commit_sha,
        "trigger_type": "manual",
    }
    return client.post_json("%s/v1/runs" % client.runtime_url, body)


def wait_for_terminal(client, run_id, tenant_id, poll_interval, timeout_sec):
    started = time.time()
    while True:
        if time.time() - started > timeout_sec:
            raise RuntimeError("Timeout waiting for run %s" % run_id)
        params = urllib.parse.urlencode({"tenant_id": tenant_id})
        summary = client.get_json("%s/v1/runs/%s/summary?%s" % (client.views_url, run_id, params))
        status = (summary.get("status") or "").lower()
        print("    poll status=%s" % status)
        if status in TERMINAL_STATUSES:
            return summary
        time.sleep(poll_interval)


def fetch_taxonomy(client, run_id, tenant_id):
    params = urllib.parse.urlencode({"tenant_id": tenant_id})
    json_url = "%s/v1/runs/%s/taxonomy-gate?%s" % (client.views_url, run_id, params)
    xml_url = "%s/v1/runs/%s/taxonomy-gate.xml?%s" % (client.views_url, run_id, params)
    taxonomy_json = client.get_json(json_url)
    taxonomy_xml = client._request("GET", xml_url, accept="application/xml")
    return taxonomy_json, taxonomy_xml


def ensure_dir(path):
    if not os.path.isdir(path):
        os.makedirs(path)


def save_report(output_dir, branch_name, run_id, summary, taxonomy_json, taxonomy_xml):
    branch_dir = os.path.join(output_dir, branch_name)
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
    return parser.parse_args()


def main():
    args = parse_args()
    load_env(args.env_file)

    identity_url = os.environ.get("IDENTITY_URL", "http://localhost:8000")
    runtime_url = os.environ.get("RUNTIME_URL", "http://localhost:8002")
    views_url = os.environ.get("VIEWS_URL", "http://localhost:8003")
    email = os.environ.get("AUTH_EMAIL")
    password = os.environ.get("AUTH_PASSWORD")
    tenant_id = os.environ.get("TENANT_ID")
    project_id = os.environ.get("PROJECT_ID") or None
    repository_match = os.environ.get("REPOSITORY_MATCH", "Mohammed-shihaf/Metric_eveluation")
    branches = (args.branches or os.environ.get(
        "BRANCHES", "SA_bug_2.6,SA_bugFX_2.6,SA_TCC_2.6,SA_CC_2.6")).split(",")
    branches = [b.strip() for b in branches if b.strip()]
    output_root = os.environ.get("OUTPUT_DIR", "taxonomy_reports")
    poll_interval = int(os.environ.get("POLL_INTERVAL_SEC", "30"))
    poll_timeout = int(os.environ.get("POLL_TIMEOUT_SEC", "3600"))
    continue_on_failure = os.environ.get("CONTINUE_ON_FAILURE", "true").lower() == "true"

    if not tenant_id:
        print("ERROR: TENANT_ID is required", file=sys.stderr)
        return 1

    print("=== Authenticate ===", flush=True)
    if args.skip_login:
        token = os.environ.get("SESSION_TOKEN")
        if not token:
            print("ERROR: SESSION_TOKEN required with --skip-login", file=sys.stderr)
            return 1
    else:
        if not email or not password:
            print("ERROR: AUTH_EMAIL and AUTH_PASSWORD required", file=sys.stderr)
            return 1
        dev_verify(identity_url, email)
        token = login(identity_url, email, password)
        print("  logged in as %s" % email)

    client = PlatformClient(identity_url, runtime_url, views_url, token)

    if args.ensure_project:
        clone_url = os.environ.get(
            "CLONE_URL", "https://github.com/%s.git" % repository_match)
        ensure_project(
            client,
            os.environ.get("PROJECT_NAME", "Metric Evaluation SA"),
            clone_url,
            branches[0],
        )

    print("\n=== Resolve catalog ===")
    catalog = resolve_catalog(client, project_id, repository_match)

    if args.refresh_branches:
        print("  refreshing branch catalog...")
        try:
            refresh_branches(client, catalog["repository_id"])
        except Exception as exc:
            print("  refresh trigger: %s" % exc)
        catalog["branches"] = wait_for_branches(
            client, catalog["repository_id"], branches)
    print("  project: %s (%s)" % (catalog.get("project_name"), catalog["project_id"]))
    print("  repository: %s (%s)" % (catalog.get("repository_label"), catalog["repository_id"]))
    print("  branches in catalog: %s" % sorted(catalog["branches"].keys()))

    missing = [b for b in branches if b not in catalog["branches"]]
    if missing:
        if args.allow_partial_branches:
            print("  WARNING: skipping missing branches: %s" % missing)
            branches = [b for b in branches if b in catalog["branches"]]
        else:
            print(
                "ERROR: Branches missing from catalog. Push branches, connect GitHub SCM, "
                "then run with --refresh-branches or --allow-partial-branches. Missing: %s"
                % missing,
                file=sys.stderr,
            )
            return 1
    if not branches:
        print("ERROR: no branches available to run", file=sys.stderr)
        return 1

    if args.dry_run:
        print("\nDry run complete — catalog resolved, no runs started.")
        return 0

    batch_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir = os.path.join(ROOT, output_root, batch_id)
    ensure_dir(output_dir)
    manifest = {
        "batch_id": batch_id,
        "tenant_id": tenant_id,
        "repository": catalog.get("repository_label"),
        "project_id": catalog["project_id"],
        "repository_id": catalog["repository_id"],
        "runs": [],
    }

    print("\n=== Sequential branch runs ===")
    for idx, branch_name in enumerate(branches, start=1):
        print("\n[%d/%d] %s" % (idx, len(branches), branch_name))
        branch = catalog["branches"][branch_name]
        branch_id = branch.get("id") or branch.get("branch_id")
        commit_sha = resolve_commit_sha(branch_name, branch, catalog.get("repository_label"))
        if not branch_id or not commit_sha:
            print("  ERROR: branch missing id or commit sha: %s" % branch)
            if not continue_on_failure:
                return 1
            continue

        started = time.time()
        try:
            print("  creating run commit=%s" % commit_sha[:12])
            run_resp = create_run(
                client, catalog["project_id"], catalog["repository_id"], branch_id, commit_sha)
            run_id = run_resp["run_id"]
            if run_resp.get("existing_run"):
                print("  reused existing run")
            print("  run_id=%s" % run_id)
            print("  waiting for terminal status...")
            summary = wait_for_terminal(client, run_id, tenant_id, poll_interval, poll_timeout)
            print("  fetching taxonomy gate...")
            taxonomy_json, taxonomy_xml = fetch_taxonomy(client, run_id, tenant_id)
            save_report(output_dir, branch_name, run_id, summary, taxonomy_json, taxonomy_xml)
            elapsed = int(time.time() - started)
            entry = {
                "branch": branch_name,
                "run_id": run_id,
                "status": summary.get("status"),
                "duration_sec": elapsed,
                "gate_score": extract_gate_score(taxonomy_json),
                "existing_run": bool(run_resp.get("existing_run")),
            }
            manifest["runs"].append(entry)
            print("  saved to %s (status=%s, gate=%s)" % (
                os.path.join(output_dir, branch_name), entry["status"], entry["gate_score"]))
        except Exception as exc:
            print("  FAILED: %s" % exc)
            manifest["runs"].append({"branch": branch_name, "error": str(exc)})
            if not continue_on_failure:
                break

    manifest_path = os.path.join(output_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
    print("\n=== Done ===")
    print("Manifest: %s" % manifest_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
