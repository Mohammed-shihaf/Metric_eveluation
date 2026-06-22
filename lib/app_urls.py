"""Canonical public URLs for OAuth callbacks and app links."""

from __future__ import print_function

import os

LOCAL_APP_ROOT = "http://localhost:8501/"
HOSTED_APP_ROOT = "https://qa-assurance.testable.cc/"

ALLOWED_OAUTH_REDIRECT_URIS = frozenset(
    {
        LOCAL_APP_ROOT,
        HOSTED_APP_ROOT,
        LOCAL_APP_ROOT.rstrip("/"),
        HOSTED_APP_ROOT.rstrip("/"),
    }
)


def normalize_app_root(url):
    url = (url or "").strip()
    if not url:
        return ""
    if not url.endswith("/"):
        url += "/"
    return url


def _is_allowed_redirect(url):
    return normalize_app_root(url) in ALLOWED_OAUTH_REDIRECT_URIS


def _host_from_streamlit():
    try:
        import streamlit as st

        headers = getattr(getattr(st, "context", None), "headers", None) or {}
        return (headers.get("Host") or headers.get("host") or "").strip().lower()
    except Exception:
        return ""


def resolve_github_oauth_redirect_uri():
    """Return OAuth callback URL registered in the GitHub App.

    Priority:
    1. GITHUB_OAUTH_REDIRECT_URI when it matches localhost or qa-assurance
    2. APP_PUBLIC_URL when allowed
    3. ASSURANCE_STUDIO_ENV=hosted|production|qa-op → hosted URL
    4. Streamlit request Host header (qa-assurance vs localhost)
    5. Default localhost
    """
    explicit = normalize_app_root(os.getenv("GITHUB_OAUTH_REDIRECT_URI", ""))
    if explicit and _is_allowed_redirect(explicit):
        return normalize_app_root(explicit)

    public = normalize_app_root(os.getenv("APP_PUBLIC_URL", ""))
    if public and _is_allowed_redirect(public):
        return public

    env = os.getenv("ASSURANCE_STUDIO_ENV", "").strip().lower()
    if env in ("hosted", "production", "qa-op", "qa"):
        return HOSTED_APP_ROOT

    host = _host_from_streamlit()
    if "qa-assurance.testable.cc" in host:
        return HOSTED_APP_ROOT
    if host.startswith("localhost") or host.startswith("127.0.0.1"):
        return LOCAL_APP_ROOT

    return LOCAL_APP_ROOT


def apply_github_oauth_redirect_uri():
    """Set GITHUB_OAUTH_REDIRECT_URI in os.environ to the resolved callback."""
    os.environ["GITHUB_OAUTH_REDIRECT_URI"] = resolve_github_oauth_redirect_uri()
    return os.environ["GITHUB_OAUTH_REDIRECT_URI"]
