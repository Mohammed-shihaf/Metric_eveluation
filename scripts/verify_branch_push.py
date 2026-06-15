#!/usr/bin/env python3
"""Verify generate+assert+push for SA/DOV branches (CLI, no Streamlit)."""

from __future__ import print_function

import os
import sqlite3
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from lib.branch_pipeline import process_branches_sequentially  # noqa: E402
from lib.generator import remote_branch_status  # noqa: E402
from lib.sa_qa import load_env  # noqa: E402


def _github_config():
    env_path = os.path.join(ROOT, ".env.local")
    if os.path.isfile(env_path):
        load_env(env_path)

    token = os.environ.get("GITHUB_TOKEN", "").strip()
    repo = os.environ.get("REPOSITORY_MATCH", "").strip()
    db = os.environ.get("SCM_DB_PATH", "scm_connections.db")
    db_path = db if os.path.isabs(db) else os.path.join(ROOT, db)

    scm_slug = ""
    scm_login = ""
    if os.path.isfile(db_path):
        conn = sqlite3.connect(db_path)
        row = conn.execute(
            """
            SELECT app_user, provider_username, repo_slug
            FROM scm_connections
            WHERE status = 'active'
            ORDER BY updated_at DESC
            LIMIT 1
            """
        ).fetchone()
        conn.close()
        if row:
            from lib.scm.store import get_connection

            scm = get_connection(row[0])
            if scm:
                scm_slug = (scm.repo_slug or "").strip()
                scm_login = scm.provider_username or ""

    slug = (scm_slug or repo or "").strip()
    if token and slug:
        return {
            "token": token,
            "repo_slug": slug,
            "login": scm_login,
            "default_branch": "main",
            "push_method": "pat",
        }

    if os.path.isfile(db_path):
        conn = sqlite3.connect(db_path)
        row = conn.execute(
            """
            SELECT app_user, provider_username, repo_slug
            FROM scm_connections
            WHERE status = 'active'
            ORDER BY updated_at DESC
            LIMIT 1
            """
        ).fetchone()
        conn.close()
        if row:
            from lib.scm.store import get_connection

            scm = get_connection(row[0])
            if scm and scm.access_token:
                slug = (scm.repo_slug or repo or "").strip()
                if slug:
                    return {
                        "token": scm.access_token,
                        "repo_slug": slug,
                        "login": scm.provider_username or "",
                        "default_branch": "main",
                        "push_method": "oauth",
                    }

    if token and repo:
        return {
            "token": token,
            "repo_slug": repo,
            "login": "",
            "default_branch": "main",
            "push_method": "pat",
        }
    return None


def main():
    cfg = _github_config()
    if not cfg:
        print("VERIFY: no GitHub config (.env.local PAT or scm_connections.db)")
        return 1

    print("VERIFY: repo=%s login=%s" % (cfg["repo_slug"], cfg.get("login") or "(pat)"))

    types = ["Bug", "BugFX", "TCC", "CC"]
    result = process_branches_sequentially(
        "SA",
        "DOV",
        types,
        "2.6",
        "python",
        ROOT,
        github_config=cfg,
        max_fix_attempts=2,
        auto_install=True,
    )

    print("success:", result.get("success"))
    print("stopped_at:", result.get("stopped_at"))
    print("stop_reason:", result.get("stop_reason"))
    for row in result.get("rows", []):
        detail = (row.get("failure_reason") or row.get("messages") or "")[:120]
        print(
            "  %s overall=%s pushed=%s %s"
            % (row["branch_name"], row.get("overall"), row.get("pushed"), detail)
        )

    branches = [r["branch_name"] for r in result.get("rows", [])]
    if not branches:
        from lib.registry import iter_branches

        branches = [b for _, _, _, b in iter_branches("SA", "DOV", types, "2.6")]

    remote = remote_branch_status(branches, ROOT, github_config=cfg)
    for bname in branches:
        info = remote.get(bname, {})
        print(
            "remote %s on_github=%s sha=%s"
            % (bname, info.get("pushed"), (info.get("remote_sha") or "")[:12])
        )

    all_pushed = bool(branches) and all(remote.get(b, {}).get("pushed") for b in branches)
    print("all_pushed:", all_pushed)
    return 0 if result.get("success") and all_pushed else 1


if __name__ == "__main__":
    sys.exit(main())
