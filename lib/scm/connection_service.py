"""GitHub OAuth connection orchestration for the Streamlit app."""

from __future__ import print_function

import os
from dataclasses import dataclass

from lib.github_auth import check_app_repo_access
from lib.scm import github_oauth
from lib.scm.github_repos import list_user_repositories
from lib.scm.store import (
    connection_needs_refresh,
    get_connection,
    refresh_token_expired,
    update_connection_repo,
    update_connection_tokens,
    upsert_connection,
)


@dataclass(frozen=True)
class ConnectInitResult:
    authorization_url: str
    state: str
    provider: str = "github"


@dataclass(frozen=True)
class ConnectCompleteResult:
    connection_id: int
    provider: str
    provider_username: str
    repo_slug: str
    repo_url: str
    scopes: str
    access_ok: bool = True
    needs_install: bool = False
    access_detail: str = ""


class GitHubConnectionService:
    """Initiate and complete GitHub OAuth App connections."""

    def __init__(self):
        self.client_id = os.getenv("GITHUB_OAUTH_CLIENT_ID", "").strip()
        self.client_secret = os.getenv("GITHUB_OAUTH_CLIENT_SECRET", "").strip()
        self.redirect_uri = os.getenv("GITHUB_OAUTH_REDIRECT_URI", "").strip()
        self.token_secret = os.getenv("SCM_TOKEN_SECRET", "").strip()

    def is_configured(self):
        return bool(
            self.client_id
            and self.client_secret
            and self.redirect_uri
            and self.token_secret
        )

    def _require_config(self):
        if not self.is_configured():
            raise RuntimeError(
                "GitHub OAuth is not configured. Set GITHUB_OAUTH_CLIENT_ID, "
                "GITHUB_OAUTH_CLIENT_SECRET, GITHUB_OAUTH_REDIRECT_URI, and "
                "SCM_TOKEN_SECRET in .env.local."
            )

    def initiate_connection(self, state, login_hint=None, account_picker=False):
        """Start OAuth — mirrors reference POST /v1/scm/github/connect."""
        self._require_config()
        url = github_oauth.build_authorization_url(
            client_id=self.client_id,
            redirect_uri=self.redirect_uri,
            state=state,
            scopes=github_oauth.default_scopes(),
            login_hint=login_hint,
            account_picker=account_picker,
        )
        return ConnectInitResult(authorization_url=url, state=state)

    def complete_connection(self, code, app_user, login_hint=None):
        """Finish OAuth — mirrors reference callback code exchange + persist."""
        del login_hint
        self._require_config()
        token_result = github_oauth.exchange_code(
            code=code,
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
        )
        try:
            user_info = github_oauth.get_user_info(token_result.access_token)
        except Exception:
            user_info = github_oauth.OAuthUserInfo(
                provider_user_id="",
                username="unknown",
            )
        connection_id = upsert_connection(
            app_user,
            provider="github",
            repo_slug="",
            provider_user_id=user_info.provider_user_id,
            provider_username=user_info.username,
            access_token=token_result.access_token,
            refresh_token=token_result.refresh_token,
            scopes=token_result.scopes,
            expires_in=token_result.expires_in,
            refresh_token_expires_in=token_result.refresh_token_expires_in,
        )
        return ConnectCompleteResult(
            connection_id=connection_id,
            provider="github",
            provider_username=user_info.username,
            repo_slug="",
            repo_url="",
            scopes=token_result.scopes or "",
            access_ok=True,
            needs_install=False,
            access_detail="",
        )

    def discover_repositories(self, app_user):
        """List repositories for the connected user — mirrors connection sync discovery."""
        conn = self.get_active_token(app_user)
        if not conn or not conn.access_token:
            return []
        return list_user_repositories(conn.access_token)

    def select_repository(self, app_user, repo_slug, default_branch="main"):
        """Persist user-selected repository and verify App write access."""
        conn = self.get_active_token(app_user)
        if not conn or not conn.access_token:
            raise ValueError("Connect GitHub before selecting a repository.")
        slug, branch = update_connection_repo(app_user, repo_slug, default_branch=default_branch)
        access_ok, needs_install, access_detail = check_app_repo_access(conn.access_token, slug)
        return {
            "repo_slug": slug,
            "repo_url": "https://github.com/%s" % slug,
            "default_branch": branch,
            "access_ok": access_ok,
            "needs_install": needs_install,
            "access_detail": access_detail,
        }

    def get_active_token(self, app_user):
        """Return connection with a valid access token, refreshing when needed."""
        conn = get_connection(app_user)
        if not conn or not conn.access_token:
            return None
        if not connection_needs_refresh(conn):
            return conn
        if refresh_token_expired(conn):
            raise ValueError("GitHub refresh token expired. Reconnect via OAuth.")
        if not conn.refresh_token:
            raise ValueError("GitHub access token expired. Reconnect via OAuth.")
        token_result = github_oauth.refresh_user_token(
            conn.refresh_token,
            self.client_id,
            self.client_secret,
        )
        update_connection_tokens(
            app_user,
            access_token=token_result.access_token,
            refresh_token=token_result.refresh_token or conn.refresh_token,
            scopes=token_result.scopes or conn.scopes or "",
            expires_in=token_result.expires_in,
            refresh_token_expires_in=token_result.refresh_token_expires_in,
        )
        return get_connection(app_user)
