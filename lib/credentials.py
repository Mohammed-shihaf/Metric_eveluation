"""Check which pipeline credentials are configured in .env.local."""

from __future__ import print_function

import os
from pathlib import Path

# QA-op Kubernetes ingress hosts (env: qa-op) → .env.local keys
QA_OP_TESTABLE_URLS = {
    "IDENTITY_URL": "https://qa-api.testable.cc",      # identity-service-ingress
    "RUNTIME_URL": "https://qa-runtime.testable.cc",   # runtime-api-ingress
    "VIEWS_URL": "https://qa-views.testable.cc",       # views-api-ingress
    "FRONTEND_URL": "https://qa-frontend.testable.cc",
}

CORE_TESTABLE_URL_KEYS = ("IDENTITY_URL", "RUNTIME_URL", "VIEWS_URL")

TESTABLE_REQUIRED = (
    ("IDENTITY_URL", "Testable identity API — qa-api.testable.cc (identity-service)"),
    ("RUNTIME_URL", "Testable runtime API — qa-runtime.testable.cc (runtime-api)"),
    ("VIEWS_URL", "Testable views API — qa-views.testable.cc (views-api)"),
    ("AUTH_EMAIL", "Login email"),
    ("AUTH_PASSWORD", "Login password"),
)

TESTABLE_OPTIONAL = (
    ("REPOSITORY_MATCH", "Optional CLI/notebook catalog repo slug (UI uses per-user OAuth selection)"),
    ("GITHUB_OAUTH_CLIENT_ID", "GitHub OAuth App client ID"),
    ("GITHUB_OAUTH_CLIENT_SECRET", "GitHub OAuth App client secret"),
    ("GITHUB_OAUTH_REDIRECT_URI", "OAuth callback URL (localhost or qa-assurance only)"),
    ("APP_PUBLIC_URL", "Public app root for hosted OAuth (https://qa-assurance.testable.cc/)"),
    ("ASSURANCE_STUDIO_ENV", "Set to hosted/production/qa-op on QA deployment"),
    ("SCM_TOKEN_SECRET", "Fernet secret for encrypted SCM tokens at rest"),
    ("SCM_DB_PATH", "SQLite path for SCM connections (default: scm_connections.db)"),
    ("GITHUB_TOKEN", "GitHub PAT fallback (optional if OAuth configured)"),
    ("PROJECT_ID", "Project UUID (auto-resolved if empty)"),
    ("TENANT_ID", "Tenant UUID (auto-resolved from session)"),
    ("OUTPUT_DIR", "Taxonomy report root (default: taxonomy_reports)"),
    ("POLL_INTERVAL_SEC", "Whitebox poll interval"),
    ("POLL_TIMEOUT_SEC", "Whitebox poll timeout"),
    ("BRANCH_DELAY_SEC", "Delay between branch runs"),
)

S3_REQUIRED = (
    ("AWS_ACCESS_KEY_ID", "AWS access key (or use ~/.aws/credentials)"),
    ("AWS_SECRET_ACCESS_KEY", "AWS secret key"),
)

S3_OPTIONAL = (
    ("AWS_SESSION_TOKEN", "AWS session token (STS)"),
    ("AWS_DEFAULT_REGION", "AWS region (default: us-east-2)"),
    ("S3_BUCKET", "Tool report bucket (default: us2-qa-testable)"),
    ("S3_SEARCH_PREFIX", "S3 prefix (default: qa-op/cell-001/)"),
    ("S3_DOWNLOAD_ROOT", "Local download dir (default: s3_downloads)"),
    ("S3_CELL_BATCH_ID", "Optional cell batch filter"),
)


def _is_set(key):
    return bool(str(os.environ.get(key, "")).strip())


def _url_matches_qa_op(key):
    expected = QA_OP_TESTABLE_URLS.get(key)
    if not expected:
        return None
    actual = str(os.environ.get(key, "")).strip().rstrip("/")
    return actual.lower() == expected.rstrip("/").lower()


def _aws_shared_credentials_path():
    """Return ~/.aws/credentials when home is resolvable, else a non-existent path."""
    try:
        return Path.home() / ".aws" / "credentials"
    except RuntimeError:
        return Path("/nonexistent/.aws/credentials")


def _testable_urls_ok(testable_rows):
    """True when core Testable API URLs are set (file or process env)."""
    core = [r for r in testable_rows if r["key"] in CORE_TESTABLE_URL_KEYS]
    if not all(r["configured"] for r in core):
        return False
    return all(r.get("url_matches_qa_op") is not False for r in core)


def audit_credentials(env_file=None, root=None):
    """Return credential checklist without exposing secret values."""
    repo_root = Path(root or Path(__file__).resolve().parents[1])
    env_path = Path(env_file) if env_file else repo_root / ".env.local"
    present = env_path.is_file()
    keys_in_file = set()
    if present:
        from lib.sa_qa import load_env

        load_env(str(env_path))
        with open(env_path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                keys_in_file.add(line.split("=", 1)[0].strip())

    def _row(items, group):
        rows = []
        for key, label in items:
            url_ok = _url_matches_qa_op(key)
            rows.append({
                "group": group,
                "key": key,
                "label": label,
                "in_file": key in keys_in_file,
                "configured": _is_set(key),
                "required": group.endswith("_required"),
                "expected_url": QA_OP_TESTABLE_URLS.get(key, ""),
                "url_matches_qa_op": url_ok,
            })
        return rows

    testable = _row(TESTABLE_REQUIRED, "testable_required") + _row(TESTABLE_OPTIONAL, "testable_optional")
    s3 = _row(S3_REQUIRED, "s3_required") + _row(S3_OPTIONAL, "s3_optional")

    testable_ok = all(r["configured"] for r in testable if r["group"] == "testable_required")
    urls_ok = _testable_urls_ok(testable)
    s3_ok = all(r["configured"] for r in s3 if r["group"] == "s3_required")
    # boto3 can use shared credentials file even when env vars unset
    if not s3_ok:
        aws_shared = _aws_shared_credentials_path().is_file()
        if aws_shared:
            s3_ok = True

    return {
        "env_file": str(env_path),
        "env_file_present": present,
        "testable_ready": testable_ok,
        "testable_urls_ok": urls_ok,
        "qa_op_urls": QA_OP_TESTABLE_URLS,
        "s3_ready": s3_ok,
        "testable": testable,
        "s3": s3,
    }
