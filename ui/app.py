"""Metric Evaluation pipeline UI — end-to-end with strong triggers."""

from __future__ import print_function

import os
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lib.branch_pipeline import (  # noqa: E402
    generate_branches,
    pipeline_work_dir,
    process_branches_sequentially,
    push_branches,
    validate_branches,
)
from lib.compare import summarize_comparisons  # noqa: E402
from lib.credentials import audit_credentials  # noqa: E402
from lib.github_auth import check_app_repo_access, github_app_install_url  # noqa: E402
from lib.scm.connection_service import GitHubConnectionService  # noqa: E402
from lib.scm.store import (  # noqa: E402
    consume_oauth_state,
    create_oauth_state,
    get_connection,
    revoke_connection,
)
from lib.generator import (  # noqa: E402
    remote_branch_status,
)
from lib.metrics import github_branch_url, infer_from_branch_name  # noqa: E402
from lib.pipeline_selection import (  # noqa: E402
    branch_type_options,
    csv_from_list,
    metric_options,
    selection_summary,
    technique_options,
)
from lib.proofs import (  # noqa: E402
    collect_comparison_proof,
    collect_local_batch,
    collect_s3_proof,
    collect_sonar_batch,
    compare_readiness,
    list_proof_branches,
    load_proof_bundle,
    whitebox_completion,
)
from lib.registry import load_registry  # noqa: E402
from lib.repo_state import ensure_repo_aligned  # noqa: E402
from lib.sa_qa import load_env, run_taxonomy_batch, verify_login  # noqa: E402
from lib.tool_map import python_tool  # noqa: E402
from lib.sonar_runner import sonar_server_status  # noqa: E402
from lib.ui_run_panel import RunPanel  # noqa: E402

LOGO = Path(__file__).parent / "assets" / "logo.png"

st.set_page_config(
    page_title="Testable Assurance Studio",
    page_icon=str(LOGO),
    layout="wide",
    initial_sidebar_state="expanded",
)


def _app_header():
    logo_col, title_col = st.columns([1, 11], vertical_alignment="center")
    with logo_col:
        st.image(str(LOGO), width=52)
    with title_col:
        st.title("Testable Assurance Studio")
        st.caption("Generate → assert → GitHub · Whitebox + S3 · Local tools · SonarQube · Compare")


_app_header()


def _skip_detail(report):
    if not report:
        return ""
    extra = report.get("extra") or {}
    return extra.get("skip_reason") or report.get("raw_summary") or report.get("message", "")


def _branches_on_github(branch_names):
    """In-scope branches that exist on the connected GitHub repo."""
    if not _github_creds_ready():
        return []
    rows, _ = _branch_push_status(branch_names)
    return [r["branch"] for r in rows if r.get("on_github") == "yes"]


def _local_tool_preview(branches):
    rows = []
    for bname in branches:
        tech, metric, bt, _ = infer_from_branch_name(bname)
        if not tech:
            continue
        info = python_tool(tech, metric)
        rows.append({
            "branch": bname,
            "metric": info.get("l5_metric") or metric,
            "branch_type": bt,
            "primary_tool": info.get("primary") or "—",
            "family": info.get("family") or "—",
        })
    return rows


def _readiness():
    audit = audit_credentials(str(ROOT / ".env.local"), root=str(ROOT))
    return audit


def _qa_session_creds():
    """Return (email, password) saved from the login form, or (None, None)."""
    email = st.session_state.get("qa_email_saved", "").strip()
    password = st.session_state.get("qa_password_saved", "")
    if email and password:
        return email, password
    return None, None


def _qa_creds_ready(audit):
    """QA ready when URLs configured and creds from session or .env.local."""
    urls_ok = audit.get("testable_urls_ok", False)
    env_creds = any(
        r["configured"] for r in audit.get("testable", [])
        if r["key"] in ("AUTH_EMAIL", "AUTH_PASSWORD")
    )
    session_creds = _qa_session_creds()[0] is not None
    return urls_ok and (env_creds or session_creds)


def _app_user_email(audit=None):
    """Per-user key for SCM connections (QA session email or .env.local AUTH_EMAIL)."""
    email, _ = _qa_session_creds()
    if email:
        return email.strip()
    audit = audit or _readiness()
    for row in audit.get("testable", []):
        if row.get("key") == "AUTH_EMAIL" and row.get("configured"):
            return os.environ.get("AUTH_EMAIL", "").strip()
    return ""


def _oauth_service():
    return GitHubConnectionService()


def _oauth_connection(app_user=None):
    """Load OAuth connection with refresh-aware token for the current app user."""
    app_user = (app_user or _app_user_email()).strip()
    if not app_user:
        return None
    svc = _oauth_service()
    if not svc.is_configured():
        return get_connection(app_user)
    try:
        return svc.get_active_token(app_user)
    except ValueError as exc:
        st.session_state["github_oauth_error"] = str(exc)
        return None
    except Exception:
        return get_connection(app_user)



def _build_oauth_authorize_url(app_user, login_hint=None):
    """Create OAuth state and authorization URL — mirrors POST /v1/scm/github/connect."""
    state = create_oauth_state(app_user, login_hint=login_hint)
    init = _oauth_service().initiate_connection(state, login_hint=login_hint)
    return init.authorization_url


def _ensure_oauth_authorize_url(app_user, login_hint=None):
    """Cache authorize URL per app user + login hint (avoids orphan states on every rerun)."""
    hint_key = (login_hint or "").strip().lower()
    client_id = os.getenv("GITHUB_OAUTH_CLIENT_ID", "").strip()
    key = "%s:%s" % (app_user.strip(), hint_key)
    cache = st.session_state.get("github_oauth_url_cache") or {}
    if (
        cache.get("key") == key
        and cache.get("url")
        and cache.get("client_id") == client_id
    ):
        return cache["url"]
    url = _build_oauth_authorize_url(app_user, login_hint=login_hint)
    st.session_state["github_oauth_url_cache"] = {
        "key": key,
        "url": url,
        "client_id": client_id,
    }
    return url


def _resolved_repo_slug():
    """Per-user target repo from Streamlit session or SCM connection DB only."""
    repo_slug = st.session_state.get("github_repo_slug", "").strip()
    app_user = _app_user_email()
    if app_user:
        conn = _oauth_connection(app_user)
        if conn:
            repo_slug = repo_slug or (conn.repo_slug or "").strip()
    return repo_slug


def _sync_github_session_from_db():
    """Hydrate Streamlit session from encrypted OAuth connection for current app user."""
    app_user = _app_user_email()
    if not app_user:
        return None
    conn = _oauth_connection(app_user)
    if not conn or not conn.access_token:
        return None
    st.session_state["github_login_ok"] = True
    st.session_state["github_user_login"] = conn.provider_username or ""
    st.session_state["github_token_saved"] = conn.access_token
    st.session_state["github_push_method"] = "oauth"
    repo_slug = (conn.repo_slug or "").strip()
    if repo_slug:
        st.session_state["github_repo_slug"] = repo_slug
        st.session_state["github_repo_url"] = "https://github.com/%s" % repo_slug
        st.session_state.setdefault("github_default_branch", "main")
    else:
        st.session_state.pop("github_repo_slug", None)
        st.session_state.pop("github_repo_url", None)
        st.session_state["github_needs_install"] = False
        st.session_state.pop("github_access_detail", None)
    return conn


def _github_session():
    """Return GitHub push config from session after OAuth DB sync."""
    if not st.session_state.get("github_login_ok"):
        return None
    token = st.session_state.get("github_token_saved", "").strip()
    repo_slug = st.session_state.get("github_repo_slug", "").strip()
    if token and repo_slug:
        return {
            "token": token,
            "repo_slug": repo_slug,
            "login": st.session_state.get("github_user_login", ""),
            "default_branch": st.session_state.get("github_default_branch", "main"),
            "push_method": st.session_state.get("github_push_method", "oauth"),
        }
    return None


def _github_push_config():
    """Push config: prefer per-user OAuth; GITHUB_TOKEN is last-resort fallback."""
    repo_slug = _resolved_repo_slug()

    app_user = _app_user_email()
    if app_user:
        conn = _oauth_connection(app_user)
        if conn and conn.access_token and repo_slug:
            return {
                "token": conn.access_token,
                "repo_slug": repo_slug,
                "login": conn.provider_username or "",
                "default_branch": st.session_state.get("github_default_branch", "main"),
                "push_method": "oauth",
            }

    pat = os.environ.get("GITHUB_TOKEN", "").strip()
    if pat and repo_slug:
        return {
            "token": pat,
            "repo_slug": repo_slug,
            "login": st.session_state.get("github_user_login", ""),
            "default_branch": st.session_state.get("github_default_branch", "main"),
            "push_method": "pat",
        }

    session = _github_session()
    if session:
        return session
    return None


def _github_install_prompt(repo_slug, detail=None):
    """Show install guidance when the GitHub App lacks repo access."""
    repo_slug = (repo_slug or "").strip()
    if detail:
        st.warning(detail)
    if repo_slug:
        st.caption(
            "Install **Testable Assurance Studio** on `%s` with **Contents: Read & write**."
            % repo_slug
        )
    st.link_button(
        "Install GitHub App on repository",
        github_app_install_url(),
        width="stretch",
    )


def _recheck_github_access():
    """Re-run install/write checks and refresh session flags."""
    cfg = _github_push_config()
    if not cfg or not cfg.get("token") or not cfg.get("repo_slug"):
        st.session_state["github_needs_install"] = False
        st.session_state.pop("github_access_detail", None)
        return False, "GitHub is not fully configured."

    if cfg.get("push_method") == "pat":
        access_ok, needs_install, access_detail = check_app_repo_access(
            cfg["token"],
            cfg["repo_slug"],
        )
        st.session_state["github_needs_install"] = False
        st.session_state.pop("github_access_detail", None)
        return access_ok, access_detail

    access_ok, needs_install, access_detail = check_app_repo_access(
        cfg["token"],
        cfg["repo_slug"],
    )
    st.session_state["github_needs_install"] = needs_install and not access_ok
    st.session_state["github_access_detail"] = (
        access_detail if (needs_install and not access_ok) else ""
    )
    return access_ok, access_detail


def _github_creds_ready():
    return _github_push_config() is not None


def _github_repo_for_links():
    return _resolved_repo_slug()


def _active_repo_slug():
    return _resolved_repo_slug()


def _reset_session_pipeline_state():
    for key in (
        "push_status_cache",
        "last_whitebox_branches",
        "last_qa_rc",
        "last_qa_batch",
        "last_local_run",
        "last_local_log",
        "last_sonar_run",
        "last_sonar_log",
    ):
        st.session_state.pop(key, None)


def _sync_repo_artifacts(show_notice=True):
    """Clear stale proofs/taxonomy/S3 when this user's GitHub repo changes."""
    repo = _active_repo_slug()
    if not repo:
        return None
    result = ensure_repo_aligned(repo, root=str(ROOT), app_user=_app_user_email())
    if result.get("changed"):
        _reset_session_pipeline_state()
        if show_notice and "repo_switch_notice" not in st.session_state:
            old = result.get("old_repo") or "(none)"
            cleared = ", ".join(result.get("cleared") or []) or "none"
            st.session_state["repo_switch_notice"] = (
                "Switched GitHub target from **%s** to **%s**. "
                "Cleared local artifacts: %s."
                % (old, result["new_repo"], cleared)
            )
    return result


def _github_connected_status():
    """Connected integration banner — mirrors reference SCM integrations status."""
    login = st.session_state.get("github_user_login", "")
    repo = st.session_state.get("github_repo_slug", "")
    url = st.session_state.get("github_repo_url", "")
    method = st.session_state.get("github_push_method", "oauth")
    if url and repo:
        st.success("GitHub connected as **@%s** → [%s](%s) (%s)" % (login, repo, url, method))
    elif repo:
        st.success("GitHub connected as **@%s** → `%s` (%s)" % (login, repo, method))
    else:
        st.success("GitHub connected as **@%s** — select a repository to continue." % login)

    if st.session_state.get("github_needs_install"):
        _github_install_prompt(
            repo,
            st.session_state.get("github_access_detail")
            or "GitHub App is authorized but cannot write to this repository yet.",
        )

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("View repositories", width="stretch"):
            st.session_state["scm_view"] = "repos"
            st.rerun()
    with c2:
        if repo and st.button("Change repository", width="stretch"):
            st.session_state["scm_view"] = "repos"
            st.rerun()
    with c3:
        if st.button("Disconnect GitHub", width="stretch"):
            app_user = _app_user_email()
            if app_user:
                revoke_connection(app_user)
            for key in (
                "github_token_saved", "github_repo_slug", "github_user_login",
                "github_login_ok", "github_login_msg", "github_repo_url",
                "github_default_branch", "github_push_method", "github_oauth_url_cache",
                "github_needs_install", "github_access_detail", "scm_view", "scm_callback",
                "scm_discovered_repos", "scm_discovery_error",
            ):
                st.session_state.pop(key, None)
            st.session_state.pop("push_status_cache", None)
            st.rerun()


def _scm_run_discovery(app_user, force=False):
    """Discover repos and cache in session — mirrors reference ConnectionSyncWorkflow."""
    if not force and "scm_discovered_repos" in st.session_state:
        return st.session_state.get("scm_discovered_repos") or []
    st.session_state.pop("scm_discovery_error", None)
    svc = _oauth_service()
    with st.spinner("Discovering repositories…"):
        try:
            repos = svc.discover_repositories(app_user)
            st.session_state["scm_discovered_repos"] = repos
            return repos
        except Exception as exc:
            st.session_state["scm_discovered_repos"] = []
            st.session_state["scm_discovery_error"] = str(exc)
            return []


def _handle_oauth_callback():
    """Process GitHub OAuth redirect (?code=&state=) — reference callback handler."""
    qp = st.query_params
    if qp.get("error"):
        st.session_state["scm_callback"] = {
            "status": "error",
            "provider": "github",
            "error_code": qp.get("error") or "provider_denied",
            "error_description": (
                qp.get("error_description") or qp.get("error") or "GitHub authorization denied"
            ),
        }
        st.session_state["scm_view"] = "callback"
        st.query_params.clear()
        return

    code = qp.get("code")
    state = qp.get("state")
    if not code and not state:
        return
    if not code or not state:
        st.session_state["scm_callback"] = {
            "status": "error",
            "provider": "github",
            "error_code": "missing_params",
            "error_description": "Missing OAuth code or state. Try connecting again.",
        }
        st.session_state["scm_view"] = "callback"
        st.query_params.clear()
        return

    app_user = _app_user_email()
    if not app_user:
        st.session_state["scm_callback"] = {
            "status": "error",
            "provider": "github",
            "error_code": "auth_required",
            "error_description": "Log in with QA email/password before completing GitHub OAuth.",
        }
        st.session_state["scm_view"] = "callback"
        st.query_params.clear()
        return

    try:
        oauth_session = consume_oauth_state(state)
        if oauth_session.app_user != app_user:
            raise ValueError(
                "OAuth session belongs to %s but you are logged in as %s. Connect again."
                % (oauth_session.app_user, app_user)
            )
        svc = _oauth_service()
        result = svc.complete_connection(
            code,
            app_user,
            login_hint=oauth_session.login_hint,
        )
        conn = svc.get_active_token(app_user) or get_connection(app_user)
        st.session_state["github_login_ok"] = True
        st.session_state["github_user_login"] = result.provider_username
        st.session_state["github_token_saved"] = (conn.access_token if conn else "")
        st.session_state["github_push_method"] = "oauth"
        st.session_state.pop("github_repo_slug", None)
        st.session_state.pop("github_repo_url", None)
        st.session_state.pop("scm_discovered_repos", None)
        st.session_state.pop("scm_discovery_error", None)
        st.session_state.pop("push_status_cache", None)
        st.session_state.pop("repo_switch_notice", None)
        st.session_state["scm_callback"] = {
            "status": "success",
            "provider": result.provider,
            "integration_id": str(result.connection_id),
            "scm_username": result.provider_username,
        }
        st.session_state["scm_view"] = "callback"
    except Exception as exc:
        st.session_state["scm_callback"] = {
            "status": "error",
            "provider": "github",
            "error_code": "complete_failed",
            "error_description": str(exc),
        }
        st.session_state["scm_view"] = "callback"
    st.query_params.clear()


def _scm_callback_view():
    """Post-OAuth callback page — mirrors reference /scm/callback."""
    data = st.session_state.get("scm_callback") or {}
    provider = data.get("provider") or "github"
    provider_name = "GitHub" if provider == "github" else provider.replace("_", " ").title()
    st.markdown("### SCM connection")

    if data.get("status") == "success":
        st.caption("Step 2 of 3: Connect → Discover → Select")
        st.success("%s connected!" % provider_name)
        username = data.get("scm_username") or st.session_state.get("github_user_login", "")
        if username:
            st.info("Connected as **@%s**" % username)

        app_user = _app_user_email()
        repos = []
        if app_user:
            repos = _scm_run_discovery(app_user)

        discovery_error = st.session_state.get("scm_discovery_error")
        if discovery_error:
            st.warning("Repository discovery failed: %s" % discovery_error)
        elif repos:
            st.caption("Discovered **%d** repositories." % len(repos))
        else:
            st.warning("No repositories discovered for this GitHub account.")

        if discovery_error or not repos:
            if st.button("Refresh discovery", width="stretch"):
                if app_user:
                    _scm_run_discovery(app_user, force=True)
                st.rerun()

        c1, c2 = st.columns(2)
        with c1:
            if st.button("View my repositories", type="primary", width="stretch"):
                st.session_state["scm_view"] = "repos"
                st.rerun()
        with c2:
            if st.button("Continue to branches", width="stretch"):
                st.session_state.pop("scm_view", None)
                st.session_state.pop("scm_callback", None)
                st.rerun()
        return

    error_code = data.get("error_code") or "unknown"
    st.error(data.get("error_description") or "Could not connect your %s account." % provider_name)
    st.caption("Error: `%s`" % error_code)
    if st.button("Try again", type="primary", width="stretch"):
        st.session_state.pop("scm_view", None)
        st.session_state.pop("scm_callback", None)
        st.session_state.pop("github_oauth_url_cache", None)
        st.rerun()


def _scm_repo_picker_view():
    """Repository discovery + picker — mirrors reference repo browse after OAuth."""
    app_user = _app_user_email()
    if not app_user or not st.session_state.get("github_login_ok"):
        st.warning("Connect GitHub before selecting a repository.")
        if st.button("Back"):
            st.session_state.pop("scm_view", None)
            st.rerun()
        return

    st.markdown("### Select repository")
    st.caption("Step 3 of 3: Connect → Discover → Select")
    st.caption("Choose the GitHub repository for branch generation and push.")

    if "scm_discovered_repos" not in st.session_state:
        _scm_run_discovery(app_user)

    repos = st.session_state.get("scm_discovered_repos") or []
    discovery_error = st.session_state.get("scm_discovery_error")
    if not repos:
        if discovery_error:
            st.warning("Could not list repositories: %s" % discovery_error)
        else:
            st.warning("No repositories found for this GitHub account.")
        if st.button("Refresh list", width="stretch"):
            _scm_run_discovery(app_user, force=True)
            st.rerun()
        if st.button("Back", width="stretch"):
            st.session_state["scm_view"] = "callback"
            st.rerun()
        return

    labels = []
    repo_by_label = {}
    conn = _oauth_connection(app_user)
    default_repo = (
        st.session_state.get("github_repo_slug", "").strip()
        or ((conn.repo_slug or "").strip() if conn else "")
    )
    default_index = 0
    for idx, repo in enumerate(repos):
        label = "%s%s" % (repo["full_name"], " (private)" if repo.get("private") else "")
        labels.append(label)
        repo_by_label[label] = repo
        if repo["full_name"] == default_repo:
            default_index = idx

    picked_label = st.selectbox("Repository", labels, index=default_index)
    picked = repo_by_label[picked_label]

    svc = _oauth_service()
    c1, c2 = st.columns(2)
    with c1:
        use_repo = st.button("Use this repository", type="primary", width="stretch")
    with c2:
        refresh = st.button("Refresh list", width="stretch")

    if refresh:
        _scm_run_discovery(app_user, force=True)
        st.rerun()

    if use_repo:
        try:
            selected = svc.select_repository(
                app_user,
                picked["full_name"],
                default_branch=picked.get("default_branch") or "main",
            )
            st.session_state["github_repo_slug"] = selected["repo_slug"]
            st.session_state["github_repo_url"] = selected["repo_url"]
            st.session_state["github_default_branch"] = selected["default_branch"]
            st.session_state["github_needs_install"] = selected.get("needs_install", False)
            st.session_state["github_access_detail"] = selected.get("access_detail") or ""
            st.session_state.pop("scm_view", None)
            st.session_state.pop("scm_callback", None)
            _sync_repo_artifacts(show_notice=False)
            if selected.get("access_ok"):
                st.success("Repository **%s** selected." % selected["repo_slug"])
            else:
                st.warning(
                    "Repository selected, but the GitHub App still needs install permissions."
                )
            st.rerun()
        except Exception as exc:
            st.error(str(exc))

    if st.button("Back to connection status", width="stretch"):
        st.session_state["scm_view"] = "callback"
        st.rerun()


def _render_scm_flow():
    """Full-page SCM OAuth flow views (callback / repo picker)."""
    view = st.session_state.get("scm_view")
    if view == "callback":
        _scm_callback_view()
        return True
    if view == "repos":
        _scm_repo_picker_view()
        return True
    return False


def _github_connect_oauth():
    """GitHub connect entry — mirrors reference ScmProviderAuthModal."""
    if _render_scm_flow():
        return

    if st.session_state.get("github_login_ok"):
        if not st.session_state.get("github_repo_slug"):
            st.info("GitHub is connected. Select a repository to enable branch push.")
            if st.button("View my repositories", type="primary", width="stretch"):
                st.session_state["scm_view"] = "repos"
                st.rerun()
            if st.button("Disconnect GitHub", width="stretch"):
                app_user = _app_user_email()
                if app_user:
                    revoke_connection(app_user)
                for key in list(st.session_state.keys()):
                    if key.startswith("github_") or key.startswith("scm_"):
                        st.session_state.pop(key, None)
                st.rerun()
            return
        if _github_creds_ready():
            _github_connected_status()
            return

    env_token = os.environ.get("GITHUB_TOKEN", "").strip()
    if env_token and not _oauth_service().is_configured():
        st.info(
            "Server PAT is configured. Connect GitHub below so each user can pick their own "
            "target repository."
        )

    st.subheader("Connect to GitHub")
    svc = _oauth_service()
    if not svc.is_configured():
        st.error(
            "GitHub OAuth is not configured. Set `GITHUB_OAUTH_CLIENT_ID`, "
            "`GITHUB_OAUTH_CLIENT_SECRET`, `GITHUB_OAUTH_REDIRECT_URI`, `GITHUB_APP_SLUG`, "
            "and `SCM_TOKEN_SECRET` in `.env.local`. See README.md."
        )
        return

    app_user = _app_user_email()
    if not app_user:
        st.warning("Verify QA login on the Whitebox tab before connecting GitHub.")
        return

    st.caption(
        "You will authorize Testable with access to your repositories. "
        "After connecting, you can discover and pick a target repository."
    )
    login_hint = st.text_input(
        "GitHub username (optional)",
        placeholder="Mohammed-shihaf",
        help="Pre-selects the GitHub account on the authorize page when multiple sessions exist.",
        key="scm_login_hint",
    )
    try:
        authorize_url = _ensure_oauth_authorize_url(app_user, login_hint=login_hint)
        st.link_button("Connect GitHub", authorize_url, type="primary", width="stretch")
        st.caption("Opens GitHub to authorize — you will return here automatically.")
    except Exception as exc:
        st.error("Could not start GitHub OAuth: %s" % exc)

    if st.session_state.get("github_oauth_error"):
        st.error(st.session_state.pop("github_oauth_error"))


def _sidebar_filters():
    st.sidebar.image(str(LOGO), width=120)
    st.sidebar.header("Selection")
    registry = load_registry()
    tech_opts = technique_options(registry)
    tech_codes = [c for c, _ in tech_opts]

    use_all = st.sidebar.checkbox("All techniques (412)", value=False)
    if use_all:
        techniques, selected_techniques = "all", tech_codes
    else:
        selected_techniques = st.sidebar.multiselect(
            "Techniques", tech_codes, default=["SA"],
            format_func=lambda c: next(l for code, l in tech_opts if code == c),
        )
        techniques = csv_from_list(selected_techniques) if selected_techniques else "SA"

    use_all_metrics = st.sidebar.checkbox("All metrics", value=False)
    if use_all_metrics:
        metrics = "all"
    else:
        metric_choices = []
        techs_for_metrics = tech_codes if use_all else selected_techniques
        for tc in techs_for_metrics:
            for m in metric_options(tc, registry):
                metric_choices.append("%s:%s" % (tc, m))
        picked = st.sidebar.multiselect("Metrics", sorted(set(metric_choices)))
        if picked and len({p.split(":")[0] for p in picked}) == 1:
            metrics = csv_from_list([p.split(":")[1] for p in picked])
        elif picked:
            metrics = csv_from_list([p.split(":")[1] for p in picked])
        else:
            metrics = "DOV" if techniques == "SA" else "all"

    type_opts = branch_type_options(registry)
    types = st.sidebar.multiselect("Branch types", type_opts, default=type_opts) or type_opts
    version = st.sidebar.text_input("Version", "2.6")

    summary = selection_summary(techniques, metrics, types, version, registry)
    st.sidebar.metric("In scope", summary["branch_count"])

    audit = _readiness()
    qa_ok = _qa_creds_ready(audit)
    c1, c2, c3 = st.sidebar.columns(3)
    c1.metric("QA", "OK" if qa_ok else "—")
    c2.metric("S3", "OK" if audit["s3_ready"] else "—")
    c3.metric("GitHub", "OK" if _github_creds_ready() else "—")

    return {
        "techniques": techniques,
        "metrics": metrics,
        "types": types,
        "version": version,
        "language": "python",
        "summary": summary,
        "env_file": str(ROOT / ".env.local"),
        "audit": audit,
        "qa_ready": qa_ok,
    }


def _push_status_cache_key(branches):
    repo_slug = _github_repo_for_links()
    return (repo_slug, tuple(branches))


def _branch_push_status(branches, force_refresh=False):
    """GitHub push readiness for in-scope branches.

    The remote check (git ls-remote) is cached in session state and only runs
    when forced (explicit refresh or after a push). Streamlit reruns on every
    sidebar change, so calling git on each rerun would hammer the remote and,
    with bad auth, open a browser tab per call.
    """
    key = _push_status_cache_key(branches)
    cache = st.session_state.get("push_status_cache")
    if not force_refresh and cache and cache.get("key") == key:
        return cache["rows"], cache["all_pushed"]

    github_config = _github_push_config()
    repo_slug = _github_repo_for_links()
    if not github_config:
        # No credentials: never touch git (origin fallback can trigger a
        # credential-manager browser prompt). Report everything as not pushed.
        rows = [{
            "branch": name, "on_github": "no", "remote_sha": "—",
            "repository": repo_slug or "—",
        } for name in branches]
        return rows, False

    remote = remote_branch_status(branches, str(ROOT), github_config=github_config)
    rows = []
    for name in branches:
        info = remote.get(name, {})
        rows.append({
            "branch": name,
            "on_github": "yes" if info.get("pushed") else "no",
            "remote_sha": info.get("sha") or "—",
            "repository": repo_slug or "—",
        })
    all_pushed = bool(branches) and all(info.get("pushed") for info in remote.values())
    st.session_state["push_status_cache"] = {
        "key": key, "rows": rows, "all_pushed": all_pushed,
    }
    return rows, all_pushed


def _tab_branches(filters):
    st.header("1 — Generate branches")
    total = filters["summary"]["branch_count"]

    _github_connect_oauth()

    github_ready = _github_creds_ready()
    cfg_push = _github_push_config() if github_ready else None
    using_pat = bool(cfg_push and cfg_push.get("push_method") == "pat")
    needs_install = bool(st.session_state.get("github_needs_install")) and not using_pat
    repo_slug = st.session_state.get("github_repo_slug", "")

    if total == 0:
        st.warning("No branches in scope — adjust the sidebar selection (techniques, metrics, types).")
    if not github_ready:
        if st.session_state.get("github_login_ok") and not st.session_state.get("github_repo_slug"):
            st.warning(
                "GitHub is connected — click **View my repositories** above and select a target repo "
                "before generating branches."
            )
        else:
            st.warning(
                "Step 1: Click **Connect GitHub** above and authorize. "
                "Step 2: Pick a repository. Then you can generate branches."
            )
    else:
        cfg = cfg_push or _github_push_config()
        login = cfg.get("login") or "configured account"
        repo_slug = cfg.get("repo_slug", "—")
        push_method = cfg.get("push_method", "oauth")
        method_label = "classic PAT (.env.local)" if push_method == "pat" else "GitHub App OAuth"
        st.caption(
            "Three steps: **Generate** (write branches locally) -> **Validate** (registry strength asserts, "
            "fix-until-pass) -> **Push** to **%s** as **@%s** via **%s**."
            % (repo_slug, login, method_label)
        )
        if using_pat:
            st.info(
                "Using shared **GITHUB_TOKEN** fallback — connect GitHub OAuth above so pushes go as "
                "your own account."
            )
        if needs_install:
            _github_install_prompt(
                repo_slug,
                st.session_state.get("github_access_detail")
                or "Install the GitHub App on this repository before generating branches.",
            )
            if st.button("Re-check GitHub access", key="recheck_github_access_branches", width="stretch"):
                with st.spinner("Checking GitHub App install and write access…"):
                    access_ok, access_detail = _recheck_github_access()
                if access_ok:
                    st.success("GitHub App has read/write access — you can generate branches now.")
                    st.session_state.pop("push_status_cache", None)
                else:
                    st.warning(access_detail or "GitHub App still cannot write to this repository.")
                st.rerun()

    max_fix_attempts = st.number_input(
        "Max fix attempts per branch",
        min_value=0,
        max_value=5,
        value=2,
        help="After a failed validation, regenerate and optionally install tools, then re-assert.",
    )
    auto_install = st.checkbox(
        "Auto-install tools to fix validation",
        value=True,
        help="Installs the metric's primary tool into this app's Python environment when validation fails.",
    )

    work_root = pipeline_work_dir(str(ROOT), app_user=_app_user_email())
    gen_rows = st.session_state.get("gen_rows") or []
    validate_rows = st.session_state.get("validate_rows") or []
    all_validated = bool(validate_rows) and bool(st.session_state.get("validate_ok"))

    btn_gen, btn_val, btn_push = st.columns(3)
    with btn_gen:
        run_generate = st.button(
            "1 — Generate branches",
            type="primary",
            width="stretch",
            disabled=total == 0,
        )
    with btn_val:
        run_validate = st.button(
            "2 — Validate branches",
            type="primary",
            width="stretch",
            disabled=not gen_rows,
        )
    with btn_push:
        run_push = st.button(
            "3 — Push to GitHub",
            type="primary",
            width="stretch",
            disabled=not all_validated or not github_ready or needs_install,
        )

    def _assert_table(rows, pushed_col=False):
        display = []
        for r in rows:
            row = {
                "branch": r.get("branch_name"),
                "attempts": r.get("attempts"),
                "structure": r.get("structure"),
                "tool_support": r.get("tool_support"),
                "metric_behavior": r.get("metric_behavior"),
                "strength": r.get("strength_score"),
                "threshold": (r.get("expected_threshold") or "")[:50],
                "overall": r.get("overall"),
                "detail": r.get("failure_reason") or r.get("messages") or r.get("error", ""),
            }
            if pushed_col:
                row["pushed"] = "yes" if r.get("pushed") else "no"
            display.append(row)
        if display:
            st.dataframe(display, width="stretch")

    if run_generate:
        with RunPanel("Generating %d branches" % total) as panel:
            with panel.stdout_redirect():
                gen_result = generate_branches(
                    filters["techniques"],
                    filters["metrics"],
                    filters["types"],
                    filters["version"],
                    filters["language"],
                    work_root,
                    progress_callback=panel.progress,
                )
            st.session_state["gen_rows"] = gen_result.get("rows", [])
            st.session_state.pop("validate_rows", None)
            st.session_state.pop("validate_ok", None)
            st.session_state.pop("last_branch_pipeline", None)
            if gen_result.get("success"):
                st.success("Generated %d branch(es) in `%s`." % (len(gen_result.get("generated", [])), work_root))
                panel.set_result("complete", "complete")
                st.toast("Generated %d branches" % len(gen_result.get("generated", [])), icon="✅")
            else:
                st.error("Generate stopped at **%s**: %s" % (
                    gen_result.get("stopped_at"), gen_result.get("stop_reason")))
                panel.set_result("error", "stopped")
                st.toast("Generate failed", icon="⚠️")
            _assert_table(gen_result.get("rows", []))

    if run_validate:
        with RunPanel("Validating %d branches (strength asserts)" % len(gen_rows)) as panel:
            with panel.stdout_redirect():
                val_result = validate_branches(
                    gen_rows,
                    filters["version"],
                    filters["language"],
                    max_fix_attempts=int(max_fix_attempts),
                    auto_install=auto_install,
                    progress_callback=panel.progress,
                    block_strict=True,
                )
            st.session_state["validate_rows"] = val_result.get("rows", [])
            st.session_state["validate_ok"] = val_result.get("success", False)
            st.session_state["last_asserts"] = val_result.get("rows", [])
            st.session_state["last_branch_pipeline"] = val_result
            _assert_table(val_result.get("rows", []))
            if val_result.get("success"):
                scores = [r.get("strength_score") for r in val_result.get("rows", []) if r.get("strength_score") is not None]
                avg = sum(scores) / len(scores) if scores else 0
                st.success(
                    "All %d branch(es) passed strength validation (avg strength %.1f)."
                    % (len(val_result.get("validated", [])), avg)
                )
                panel.set_result("complete", "complete")
                st.toast("Validation passed", icon="✅")
            else:
                st.error("Validation blocked at **%s**: %s" % (
                    val_result.get("stopped_at"), val_result.get("stop_reason")))
                panel.set_result("error", "blocked")
                st.toast("Validation blocked", icon="⚠️")

    if run_push:
        pipeline_toast = ("warning", "Push finished with issues")
        with RunPanel("Pushing %d branches to GitHub" % len(validate_rows)) as panel:
            with panel.stdout_redirect():
                push_result = push_branches(
                    validate_rows,
                    _github_push_config(),
                    progress_callback=panel.progress,
                )
            st.session_state["last_branch_pipeline"] = push_result
            _assert_table(push_result.get("rows", []), pushed_col=True)
            if push_result.get("success"):
                st.success("Pushed %d branch(es) to GitHub." % len(push_result.get("completed", [])))
                st.session_state["last_pushed"] = push_result.get("completed", [])
                st.session_state.pop("push_status_cache", None)
                panel.set_result("complete", "complete")
                pipeline_toast = ("success", "Pushed %d branch(es)" % len(push_result.get("completed", [])))
            elif push_result.get("stop_reason"):
                st.error(push_result.get("stop_reason"))
                if push_result.get("needs_install"):
                    _github_install_prompt(repo_slug, push_result.get("stop_reason"))
                panel.set_result("error", "blocked")
            elif push_result.get("stopped_at"):
                st.error("Push stopped at **%s**: %s" % (
                    push_result["stopped_at"], push_result.get("stop_reason")))
                panel.set_result("error", "stopped")
            else:
                panel.set_result("error", "finished with issues")
        kind, msg = pipeline_toast
        if kind == "success":
            st.toast(msg, icon="✅")
        else:
            st.toast(msg, icon="⚠️")

    if st.session_state.get("gen_rows"):
        st.subheader("Generated branches")
        _assert_table(st.session_state["gen_rows"])
    if st.session_state.get("validate_rows"):
        st.subheader("Assert validation (strength)")
        _assert_table(st.session_state["validate_rows"])

    in_scope = filters["summary"]["branches"]
    st.subheader("GitHub push status")
    refresh = st.button("Refresh GitHub status", key="refresh_push_branches")
    if refresh:
        st.session_state.pop("push_status_cache", None)
    if not github_ready:
        st.info("Connect GitHub to check push status.")
        push_rows, all_pushed = _branch_push_status(in_scope)
    else:
        push_rows, all_pushed = _branch_push_status(in_scope, force_refresh=refresh)
    st.dataframe(push_rows, width="stretch")
    if all_pushed:
        st.success("All in-scope branches are on GitHub — whitebox can run.")
    else:
        not_pushed = [r["branch"] for r in push_rows if r["on_github"] != "yes"]
        st.warning(
            "Whitebox is blocked until these branches are pushed: %s"
            % ", ".join(not_pushed)
        )

    if st.session_state.get("last_asserts"):
        st.subheader("Last assert results")
        st.dataframe(st.session_state["last_asserts"], width="stretch")


def _tab_whitebox(filters):
    st.header("2 — Whitebox QA + taxonomy + S3")
    if not filters.get("qa_ready"):
        st.warning("Enter QA email/password below or configure AUTH_EMAIL/AUTH_PASSWORD in .env.local")

    st.caption("Credentials are session-only and are not saved to disk.")
    with st.form("qa_login_form", clear_on_submit=False):
        c1, c2 = st.columns(2)
        with c1:
            qa_email = st.text_input(
                "QA email",
                value=st.session_state.get("qa_email_saved", ""),
            )
        with c2:
            qa_password = st.text_input("QA password", type="password")
        verify_clicked = st.form_submit_button("Verify login", width="stretch")

    if verify_clicked:
        email = qa_email.strip()
        password = qa_password
        if not email or not password:
            st.error("Enter both QA email and password.")
        else:
            st.session_state["qa_email_saved"] = email
            st.session_state["qa_password_saved"] = password
            ok, msg = verify_login(
                filters["env_file"],
                email,
                password,
            )
            if ok:
                st.session_state["qa_login_msg"] = msg
                st.session_state["qa_login_ok"] = True
                st.success(msg)
            else:
                st.session_state["qa_login_ok"] = False
                st.session_state["qa_login_msg"] = msg
                st.error(msg)
    elif st.session_state.get("qa_login_msg"):
        if st.session_state.get("qa_login_ok"):
            st.success(st.session_state["qa_login_msg"])
        else:
            st.error(st.session_state["qa_login_msg"])

    email_for_auth, password_for_auth = _qa_session_creds()

    branches = filters["summary"]["branches"]
    branches_csv = ",".join(branches)
    st.code(branches_csv, language=None)

    st.subheader("GitHub push gate")
    wb_refresh = st.button("Refresh GitHub status", key="refresh_push_whitebox")
    if wb_refresh:
        st.session_state.pop("push_status_cache", None)
    push_rows, all_pushed = _branch_push_status(branches, force_refresh=wb_refresh)
    st.dataframe(push_rows, width="stretch")
    if not all_pushed:
        not_pushed = [r["branch"] for r in push_rows if r["on_github"] != "yes"]
        st.error(
            "Push all in-scope branches on the Branches tab before running whitebox. "
            "Missing on GitHub: %s" % ", ".join(not_pushed)
        )

    # Show current whitebox status for in-scope branches
    wb_status = whitebox_completion(branches, root=str(ROOT))
    if wb_status:
        st.subheader("Whitebox status")
        st.dataframe(
            [{
                "branch": b,
                "status": wb_status[b]["status"],
                "detail": wb_status[b]["detail"],
                "gate_score": wb_status[b].get("gate_score"),
            } for b in branches],
            width="stretch",
        )

    allow_partial = st.checkbox(
        "Allow partial catalog (skip branches not yet in Testable)",
        value=True,
        help="When unchecked, the batch fails if any branch is missing from the Testable catalog.",
    )
    catalog_wait = st.number_input(
        "Catalog sync wait (seconds)",
        min_value=30,
        max_value=600,
        value=int(os.environ.get("PARTIAL_BRANCH_SYNC_SEC", "60")),
        help="How long to wait for GitHub branches to appear in the Testable catalog.",
    )

    if st.button(
        "Run whitebox batch",
        type="primary",
        width="stretch",
        disabled=not all_pushed,
    ):
        if not all_pushed:
            st.error("Push all in-scope branches to GitHub before running whitebox.")
            return
        if not email_for_auth or not password_for_auth:
            st.error("Enter credentials and click Verify login before running whitebox.")
            return
        with RunPanel("Whitebox QA") as panel:
            gh_repo = _github_repo_for_links()
            if not gh_repo:
                st.error("Select a GitHub repository on the Branches tab before running whitebox.")
                return
            old_partial_sync = os.environ.get("PARTIAL_BRANCH_SYNC_SEC")
            old_branch_sync = os.environ.get("BRANCH_SYNC_TIMEOUT_SEC")
            os.environ["PARTIAL_BRANCH_SYNC_SEC"] = str(int(catalog_wait))
            if not allow_partial:
                os.environ["BRANCH_SYNC_TIMEOUT_SEC"] = str(max(int(catalog_wait), 300))
            batch_meta = {}
            try:
                with panel.stdout_redirect():
                    rc, batch_dir = run_taxonomy_batch(
                        env_file=filters["env_file"],
                        branches_csv=branches_csv,
                        dry_run=False,
                        refresh_branches=True,
                        allow_partial_branches=allow_partial,
                        export_html=True,
                        html_only=False,
                        auth_email=email_for_auth,
                        auth_password=password_for_auth,
                        repository_match=gh_repo,
                        progress_callback=panel.progress,
                        result_meta=batch_meta,
                    )
            finally:
                if old_partial_sync is not None:
                    os.environ["PARTIAL_BRANCH_SYNC_SEC"] = old_partial_sync
                else:
                    os.environ.pop("PARTIAL_BRANCH_SYNC_SEC", None)
                if old_branch_sync is not None:
                    os.environ["BRANCH_SYNC_TIMEOUT_SEC"] = old_branch_sync
                else:
                    os.environ.pop("BRANCH_SYNC_TIMEOUT_SEC", None)
            st.session_state["last_qa_rc"] = rc
            st.session_state["last_qa_batch"] = batch_dir
            st.session_state["last_whitebox_branches"] = branches
            skipped_catalog = batch_meta.get("catalog_skipped") or []
            if skipped_catalog:
                st.warning(
                    "Skipped %d branch(es) not yet in Testable catalog: %s. "
                    "Wait for catalog sync and re-run, or increase catalog sync wait."
                    % (len(skipped_catalog), ", ".join(skipped_catalog))
                )

            wb_after = whitebox_completion(branches, root=str(ROOT))
            proof_rows = []
            panel.progress("proofs", 0, len(branches), "", "collecting taxonomy + S3 proofs")
            for idx, bname in enumerate(branches, 1):
                info = wb_after.get(bname, {})
                row = {
                    "branch": bname,
                    "whitebox": info.get("status", "NOT_COMPLETED"),
                    "detail": info.get("detail", ""),
                    "taxonomy_detail": info.get("detail", "") if info.get("status") != "COMPLETED" else "",
                    "s3_detail": "—",
                }
                if info.get("status") == "COMPLETED":
                    try:
                        with panel.stdout_redirect():
                            s3_report = collect_s3_proof(
                                bname, meta=info.get("meta"), root=str(ROOT)
                            )
                        row["taxonomy_report"] = "yes"
                        row["s3_report"] = s3_report.get("status", "?")
                        row["taxonomy_detail"] = "taxonomy report produced"
                        row["s3_detail"] = _skip_detail(s3_report) if s3_report.get("status") == "SKIPPED" else s3_report.get("raw_summary", "")
                    except Exception as exc:
                        row["taxonomy_report"] = "error"
                        row["s3_report"] = str(exc)
                        row["s3_detail"] = str(exc)
                else:
                    row["taxonomy_report"] = "—"
                    row["s3_report"] = "—"
                proof_rows.append(row)
                panel.progress("proofs", idx, len(branches), bname, row["whitebox"])

            st.session_state["last_whitebox_status"] = proof_rows
            st.session_state["last_whitebox_log"] = panel.log_lines
            st.dataframe(proof_rows, width="stretch")
            completed = sum(1 for r in proof_rows if r["whitebox"] == "COMPLETED")
            if rc != 0 or completed == 0:
                st.warning(
                    "Whitebox finished with issues: %d/%d branches completed with taxonomy reports"
                    % (completed, len(branches))
                )
            else:
                st.success("Whitebox completed for all %d branches" % completed)
        st.toast("Whitebox batch finished", icon="✅")

    if st.session_state.get("last_whitebox_status"):
        st.subheader("Last whitebox run")
        st.dataframe(
            [{
                "branch": r["branch"],
                "whitebox": r.get("whitebox"),
                "taxonomy": r.get("taxonomy_report"),
                "s3": r.get("s3_report"),
                "taxonomy_detail": r.get("taxonomy_detail", r.get("detail", "")),
                "s3_detail": r.get("s3_detail", ""),
            } for r in st.session_state["last_whitebox_status"]],
            width="stretch",
        )
        if st.session_state.get("last_whitebox_log"):
            with st.expander("Whitebox run logs"):
                st.code("\n".join(st.session_state["last_whitebox_log"]), language=None)


def _tab_local_tools(filters):
    st.header("3 — Local tool execution")
    branches = filters["summary"]["branches"]
    if not _github_creds_ready():
        st.info("Connect GitHub on the Branches tab before running local tools.")
        return
    on_github = _branches_on_github(branches)
    if not on_github:
        st.info("No in-scope branches on GitHub yet. Generate and push branches first.")
        return

    default_pick = st.session_state.get("last_whitebox_branches", on_github)
    default_pick = [b for b in default_pick if b in on_github] or on_github

    st.caption(
        "Fetches each branch from GitHub into a temp dir, runs the metric's primary tool, "
        "saves reports, then deletes the temp copy."
    )
    isolated_default = os.environ.get("LOCAL_TOOL_ISOLATED", "true").lower() in ("1", "true", "yes")
    run_isolated = st.checkbox(
        "Run in isolated throwaway session (recommended)",
        value=isolated_default,
        help="Creates a temporary virtual environment, installs tools there, runs all branches, "
        "saves reports, then deletes the venv and installed tools.",
    )
    preview = _local_tool_preview(on_github)
    if preview:
        st.subheader("Metric → tool mapping (in scope)")
        st.dataframe(preview, width="stretch")

    selected = st.multiselect(
        "Branches to run locally",
        on_github,
        default=default_pick,
        help="Defaults to in-scope branches pushed to GitHub.",
    )
    if not selected:
        st.warning("Select at least one branch.")
        return

    st.code(", ".join(selected), language=None)

    if st.button("Install tools + run locally", type="primary", width="stretch"):
        st.session_state["last_whitebox_branches"] = selected
        with RunPanel("Local tool execution") as panel:
            with panel.stdout_redirect():
                results = collect_local_batch(
                    selected,
                    install=True,
                    root=str(ROOT),
                    progress_callback=panel.progress,
                    require_whitebox=False,
                    isolated=run_isolated,
                    github_config=_github_push_config(),
                )
            st.session_state["last_local_run"] = results
            st.session_state["last_local_log"] = panel.log_lines
            st.dataframe(
                [{
                    "branch": r["branch_name"],
                    "status": r.get("status"),
                    "tool": r.get("tool", ""),
                    "local_status": (r.get("local_report") or {}).get("status"),
                    "skip_reason": r.get("skip_reason") or r.get("error", ""),
                    "summary": (r.get("local_report") or {}).get("raw_summary", ""),
                } for r in results],
                width="stretch",
            )
            for r in results:
                log = r.get("tool_log") or ""
                install_msg = r.get("install_msg") or ""
                if log or install_msg:
                    with st.expander("Logs — %s" % r["branch_name"]):
                        if install_msg:
                            st.caption("Install: %s" % install_msg)
                        if log:
                            st.code(log, language=None)
        st.toast("Local tool run finished", icon="✅")

    if st.session_state.get("last_local_run"):
        st.subheader("Last local run")
        st.dataframe(st.session_state["last_local_run"], width="stretch")
        if st.session_state.get("last_local_log"):
            with st.expander("Local run logs"):
                st.code("\n".join(st.session_state["last_local_log"]), language=None)


def _tab_sonar(filters):
    st.header("4 — SonarQube (Community)")
    branches = filters["summary"]["branches"]
    if not _github_creds_ready():
        st.info("Connect GitHub on the Branches tab before running SonarQube.")
        return
    on_github = _branches_on_github(branches)
    if not on_github:
        st.info("No in-scope branches on GitHub yet. Generate and push branches first.")
        return

    status = sonar_server_status(root=str(ROOT))
    c1, c2, c3 = st.columns(3)
    c1.metric("Docker", "OK" if status["docker_ok"] else "—")
    c2.metric("Container", status["container_state"])
    c3.metric("SonarQube", status["system_status"])
    if not status["docker_ok"]:
        st.error(
            "Docker is required for SonarQube Community: %s\n\n"
            "1. Start **Docker Desktop** and wait until it shows *Running*\n"
            "2. Refresh this page — the SonarQube tab will enable the analyze button\n"
            "3. Click **Start SonarQube + analyze** (first run may take 1–2 minutes)"
            % status.get("docker_msg", "")
        )
        return
    if status["system_status"] != "UP":
        st.info(
            "SonarQube server is not UP yet. Click the button below to start the container "
            "(first run may take 1–2 minutes while images are pulled)."
        )
    else:
        st.success("SonarQube server ready at %s" % status["host_url"])

    default_pick = st.session_state.get("last_whitebox_branches", on_github)
    default_pick = [b for b in default_pick if b in on_github] or on_github

    st.caption(
        "Fetches each branch from GitHub into a temp dir, runs SonarQube Community analysis, "
        "then deletes the temp copy. Requires Docker; coverage.xml is generated automatically."
    )

    selected = st.multiselect(
        "Branches to analyze",
        on_github,
        default=default_pick,
        help="Defaults to branches pushed to GitHub.",
    )
    if not selected:
        st.warning("Select at least one branch.")
        return

    st.code(", ".join(selected), language=None)

    if st.button("Start SonarQube + analyze", type="primary", width="stretch"):
        st.session_state["last_sonar_branches"] = selected
        with RunPanel("SonarQube analysis") as panel:
            with panel.stdout_redirect():
                results = collect_sonar_batch(
                    selected,
                    root=str(ROOT),
                    progress_callback=panel.progress,
                    require_whitebox=False,
                    github_config=_github_push_config(),
                )
            st.session_state["last_sonar_run"] = results
            st.session_state["last_sonar_log"] = panel.log_lines
            st.dataframe(
                [{
                    "branch": r["branch_name"],
                    "status": r.get("status"),
                    "coverage_pct": r.get("coverage_pct"),
                    "skip_reason": r.get("skip_reason") or r.get("error", ""),
                    "summary": (r.get("sonar_report") or {}).get("raw_summary", ""),
                } for r in results],
                width="stretch",
            )
            for r in results:
                log = r.get("tool_log") or ""
                if log:
                    with st.expander("Logs — %s" % r["branch_name"]):
                        st.code(log, language=None)
        st.toast("SonarQube analysis finished", icon="✅")

    if st.session_state.get("last_sonar_run"):
        st.subheader("Last SonarQube run")
        st.dataframe(st.session_state["last_sonar_run"], width="stretch")
        if st.session_state.get("last_sonar_log"):
            with st.expander("SonarQube run logs"):
                st.code("\n".join(st.session_state["last_sonar_log"]), language=None)


def _tab_comparison(filters):
    st.header("5 — Compare taxonomy / S3 / local / sonar")
    branches = filters["summary"]["branches"]
    wb = whitebox_completion(branches, root=str(ROOT))
    completed = [b for b in branches if wb.get(b, {}).get("status") == "COMPLETED"]
    if not completed:
        st.info("No whitebox-completed branches. Run Page 2 first.")
        return

    readiness = compare_readiness(completed, root=str(ROOT))
    st.subheader("Report readiness (all four required)")
    st.dataframe(
        [{
            "branch": r["branch_name"],
            "taxonomy": r["taxonomy"],
            "s3": r["s3"],
            "local": r["local"],
            "sonar": r.get("sonar", False),
            "ready": r["ready"],
            "missing": ", ".join(r["missing"]) if r["missing"] else "",
        } for r in readiness],
        width="stretch",
    )

    all_ready = all(r["ready"] for r in readiness)
    not_ready = [r for r in readiness if not r["ready"]]
    if not_ready:
        st.warning(
            "Comparison blocked until all reports exist. Missing: "
            + "; ".join(
                "%s: %s" % (r["branch_name"], ", ".join(r["missing"]))
                for r in not_ready
            )
        )

    if st.button(
        "Run comparison",
        type="primary",
        width="stretch",
        disabled=not all_ready,
    ):
        with RunPanel("Comparison") as panel:
            results = []
            for idx, bname in enumerate(completed, 1):
                panel.progress("compare", idx - 1, len(completed), bname, "")
                try:
                    results.append(collect_comparison_proof(bname, root=str(ROOT)))
                except Exception as exc:
                    results.append({
                        "branch_name": bname,
                        "verdict": "ERROR",
                        "summary": str(exc),
                    })
                panel.progress("compare", idx, len(completed), bname, results[-1].get("verdict", ""))
            st.session_state["last_comparisons"] = results
            summary = summarize_comparisons(results)
            st.success(
                "MATCH=%d PARTIAL=%d MISMATCH=%d INCOMPLETE=%d"
                % (summary["match"], summary.get("partial", 0), summary["mismatch"], summary["incomplete"])
            )
        st.toast("Comparison done", icon="✅")

    proof_rows = list_proof_branches(str(ROOT))
    if proof_rows:
        st.dataframe(proof_rows, width="stretch")

    picks = completed
    if picks:
        branch_pick = st.selectbox("Inspect branch", picks)
        bundle = load_proof_bundle(branch_pick, root=str(ROOT))
        if bundle:
            t1, t2, t3, t4, t5 = st.tabs(["Taxonomy", "S3", "Local", "Sonar", "Comparison"])
            tax = bundle.get("taxonomy_report")
            s3 = bundle.get("s3_report")
            local = bundle.get("local_report")
            sonar = bundle.get("sonar_report")
            with t1:
                if tax and tax.get("status") == "SKIPPED":
                    st.warning("SKIPPED: %s" % _skip_detail(tax))
                st.json(tax or {"message": "taxonomy_report.json not found"})
            with t2:
                if s3 and s3.get("status") == "SKIPPED":
                    st.warning("SKIPPED: %s" % _skip_detail(s3))
                st.json(s3 or {"message": "s3_report.json not found"})
            with t3:
                if local and local.get("status") == "SKIPPED":
                    st.warning("SKIPPED: %s" % _skip_detail(local))
                extra = (local or {}).get("extra") or {}
                if extra.get("tool_log"):
                    with st.expander("Tool log"):
                        st.code(extra["tool_log"], language=None)
                st.json(local or {"message": "local_report.json not found — run Page 3"})
            with t4:
                if sonar and sonar.get("status") == "SKIPPED":
                    st.warning("SKIPPED: %s" % _skip_detail(sonar))
                extra = (sonar or {}).get("extra") or {}
                if extra.get("tool_log"):
                    with st.expander("Scanner log"):
                        st.code(extra["tool_log"], language=None)
                st.json(sonar or {"message": "sonar_report.json not found — run Page 4"})
            with t5:
                st.json(bundle.get("comparison") or {"message": "comparison.json not found — run comparison"})


def main():
    load_env(str(ROOT / ".env.local"))
    _handle_oauth_callback()
    _sync_github_session_from_db()
    _sync_repo_artifacts()
    if st.session_state.get("repo_switch_notice"):
        st.info(st.session_state.pop("repo_switch_notice"))

    if st.session_state.get("scm_view") in ("callback", "repos"):
        st.sidebar.image(str(LOGO), width=120)
        _render_scm_flow()
        return

    filters = _sidebar_filters()
    t1, t2, t3, t4, t5 = st.tabs(["Branches", "Whitebox", "Local tools", "SonarQube", "Compare"])
    with t1:
        _tab_branches(filters)
    with t2:
        _tab_whitebox(filters)
    with t3:
        _tab_local_tools(filters)
    with t4:
        _tab_sonar(filters)
    with t5:
        _tab_comparison(filters)


if __name__ == "__main__":
    main()
