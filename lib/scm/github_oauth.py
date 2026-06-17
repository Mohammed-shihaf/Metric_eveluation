"""GitHub OAuth 2.0 provider — authorize URL, code exchange, user info, refresh."""

from __future__ import print_function

import os
import re
from dataclasses import dataclass
from urllib.parse import urlencode

import requests

_GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
_GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
_GITHUB_USER_URL = "https://api.github.com/user"
_DEFAULT_SCOPES = ["repo", "read:org"]


def _sanitize_github_login_hint(raw):
    """GitHub OAuth `login` param — letters, digits, hyphens; max 39 chars."""
    if not raw:
        return None
    cleaned = re.sub(r"[^A-Za-z0-9-]", "", raw.strip())[:39].strip("-")
    return cleaned or None


def _parse_token_response(data):
    if data.get("error"):
        raise ValueError(
            "GitHub token error: %s" % (data.get("error_description") or data["error"])
        )
    return OAuthTokenResult(
        access_token=data["access_token"],
        refresh_token=data.get("refresh_token"),
        expires_in=data.get("expires_in"),
        refresh_token_expires_in=data.get("refresh_token_expires_in"),
        scopes=data.get("scope", ""),
        token_type=data.get("token_type", "bearer"),
    )


@dataclass(frozen=True)
class OAuthTokenResult:
    access_token: str
    refresh_token: str | None = None
    expires_in: int | None = None
    refresh_token_expires_in: int | None = None
    scopes: str = ""
    token_type: str = "bearer"


@dataclass(frozen=True)
class OAuthUserInfo:
    provider_user_id: str
    username: str
    email: str | None = None
    avatar_url: str | None = None


def is_github_app_mode():
    """GitHub Apps ignore OAuth scope — permissions come from App settings."""
    return bool(os.getenv("GITHUB_APP_SLUG", "").strip())


def default_scopes():
    if is_github_app_mode():
        return []
    return list(_DEFAULT_SCOPES)


def build_authorization_url(
    client_id,
    redirect_uri,
    state,
    scopes=None,
    login_hint=None,
    account_picker=False,
):
    resolved_scopes = list(scopes) if scopes is not None else default_scopes()
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "state": state,
        "allow_signup": "false",
    }
    if resolved_scopes:
        params["scope"] = " ".join(resolved_scopes)
    hint = _sanitize_github_login_hint(login_hint)
    if hint and not account_picker:
        params["login"] = hint
    if account_picker:
        params["prompt"] = "select_account"
    return "%s?%s" % (_GITHUB_AUTH_URL, urlencode(params))


def exchange_code(code, client_id, client_secret, redirect_uri):
    resp = requests.post(
        _GITHUB_TOKEN_URL,
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "redirect_uri": redirect_uri,
        },
        headers={"Accept": "application/json"},
        timeout=30,
    )
    resp.raise_for_status()
    return _parse_token_response(resp.json())


def refresh_user_token(refresh_token, client_id, client_secret):
    """Refresh a GitHub App user-to-server access token (ghu_)."""
    resp = requests.post(
        _GITHUB_TOKEN_URL,
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        },
        headers={"Accept": "application/json"},
        timeout=30,
    )
    resp.raise_for_status()
    return _parse_token_response(resp.json())


def get_user_info(access_token):
    resp = requests.get(
        _GITHUB_USER_URL,
        headers={
            "Authorization": "Bearer %s" % access_token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    return OAuthUserInfo(
        provider_user_id=str(data["id"]),
        username=data["login"],
        email=data.get("email"),
        avatar_url=data.get("avatar_url"),
    )
