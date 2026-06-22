"""Metric Evaluation pipeline UI — end-to-end with strong triggers."""

from __future__ import print_function

import json
import os
import secrets
import sys
import time
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

WHITEBOX_AUTO_PREVIEW_LIMIT = 12
LARGE_SCOPE_THRESHOLD = 48
TABLE_PAGE_SIZE = 50

from lib.branch_pipeline import (  # noqa: E402
    apply_current_scores,
    branch_materialized,
    ensure_local_branches,
    generate_branches,
    hydrate_gen_rows_from_work,
    build_regeneration_strength_map,
    pipeline_work_dir,
    process_branches_sequentially,
    push_branches,
    snapshot_previous_scores,
    sync_gen_rows_strength_from_work,
    update_regenerated_strength,
    validate_branches,
    validate_with_regeneration,
)
from lib.lang_support import (  # noqa: E402
    default_runtime,
    language_runtimes,
    normalize_language,
    normalize_runtime,
    sidebar_language_caption,
)
from lib.registry_tools import SUPPORTED_UI_LANGUAGES  # noqa: E402
from lib.compare_export import build_comparison_workbook  # noqa: E402
from lib.score_display import score_progress_display  # noqa: E402
from lib.credentials import audit_credentials  # noqa: E402
from lib.github_auth import check_app_repo_access, github_app_install_url, github_app_permissions_url  # noqa: E402
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
    full_scope_branch_count,
    metric_options,
    qualified_metric_choices,
    technique_options,
)
from lib.proofs import (  # noqa: E402
    collect_comparison_proof,
    collect_local_batch,
    collect_s3_proof,
    collect_sonar_batch,
    compare_readiness,
    format_branch_issues,
    load_proof_bundle,
    whitebox_completion,
)
from lib.report_sync_service import start as start_report_sync  # noqa: E402
from lib.report_sync_service import status as report_sync_status  # noqa: E402
from lib.report_sync_service import stop as stop_report_sync  # noqa: E402
from lib.report_sync_service import trigger_now as trigger_report_sync  # noqa: E402
from lib.s3_sync import s3_live_check  # noqa: E402
from lib.whitebox_history import branch_run_history, split_completed_pending  # noqa: E402
from lib.registry import load_registry  # noqa: E402
from lib.repo_state import ensure_repo_aligned  # noqa: E402
from lib.sa_qa import load_env, reload_s3_credentials, run_taxonomy_batch, verify_login  # noqa: E402
from lib.tool_map import python_tool  # noqa: E402
from lib.tool_doctor import load_capability_matrix, run_tool_doctor  # noqa: E402
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


def _friendly_run_error(exc):
    """Map backend exceptions to actionable UI messages."""
    msg = str(exc).strip()
    lower = msg.lower()
    transient_markers = (
        "error code: 520", "error code: 502", "error code: 503", "error code: 504",
        "temporarily unavailable", "try again shortly", "timed out", "connection reset",
    )
    if any(token in lower for token in transient_markers):
        return (
            "The Testable platform returned a temporary error — wait a moment and click **Run** again. "
            "Detail: %s" % msg
        )
    if "login failed" in lower:
        return "Authentication failed — check QA email/password in the sidebar **Account** panel. Detail: %s" % msg
    return msg


def _streamlit_key(prefix, branch_name):
    safe = branch_name.replace(" ", "_").replace(".", "_").replace("-", "_")
    return "%s_%s" % (prefix, safe)


def _report_path(bundle, report_key, filename):
    report = (bundle or {}).get(report_key) or {}
    path = report.get("_path")
    if path:
        return path
    proof_dir = (bundle or {}).get("proof_dir")
    if proof_dir:
        return str(Path(proof_dir) / filename)
    return ""


def _report_download(col, label, path, download_name, key):
    if path and Path(path).is_file():
        col.download_button(
            label,
            data=Path(path).read_bytes(),
            file_name=download_name,
            mime="application/json",
            key=key,
        )
    else:
        col.caption("pending")


def _diff_rows(diffs):
    rows = []
    for diff in diffs or []:
        row = {
            "field": diff.get("field", ""),
            "match": diff.get("match"),
        }
        if "delta" in diff:
            row["delta"] = diff["delta"]
        for key, value in diff.items():
            if key in ("field", "match", "delta"):
                continue
            row[key] = value
        rows.append(row)
    return rows


def _whitebox_preview_cached(branches):
    """True when Testable/GitHub preview caches match the current branch scope."""
    branch_key = ",".join(branches or [])
    push_key = _push_status_cache_key(branches)
    cache = st.session_state.get("push_status_cache") or {}
    return (
        st.session_state.get("_qa_connected_repos_branches") == branch_key
        and st.session_state.get("_wb_catalog_preview_branches") == branch_key
        and cache.get("key") == push_key
    )


def _should_auto_whitebox_preview(branches, force_refresh=False):
    if force_refresh:
        return True
    if len(branches or []) <= WHITEBOX_AUTO_PREVIEW_LIMIT:
        return True
    return _whitebox_preview_cached(branches)


def _split_diff_rows(diffs):
    """Split diff rows into matched and mismatched lists."""
    rows = _diff_rows(diffs)
    matched = [r for r in rows if r.get("match") is True]
    mismatched = [r for r in rows if r.get("match") is False]
    return matched, mismatched


def _styled_diff_dataframe(rows, highlight_mismatch=False):
    """Render diff rows with green/red row highlighting."""
    if not rows:
        return
    import pandas as pd

    df = pd.DataFrame(rows)
    if highlight_mismatch:
        def _row_style(row):
            if row.get("match") is False:
                return ["background-color: #FFC7CE"] * len(row)
            if row.get("match") is True:
                return ["background-color: #C6EFCE"] * len(row)
            return [""] * len(row)

        st.dataframe(df.style.apply(_row_style, axis=1), width="stretch")
    else:
        st.dataframe(df, width="stretch")


def _render_pair_diffs(title, pair):
    if not pair:
        st.caption("%s: not available" % title)
        return
    st.markdown("**%s** — `%s`" % (title, pair.get("verdict", "?")))
    if pair.get("summary"):
        st.caption(pair["summary"])
    field_matched, field_mismatched = _split_diff_rows(pair.get("field_diffs"))
    metric_matched, metric_mismatched = _split_diff_rows(pair.get("metric_diffs"))
    matched = field_matched + metric_matched
    mismatched = field_mismatched + metric_mismatched
    rename = {}
    for row in matched + mismatched:
        for key in list(row.keys()):
            if key in ("s3", "local", "sonar"):
                if key == "s3":
                    rename[key] = "S3 Data"
                elif key == "local":
                    rename[key] = "Local Data"
                elif key == "sonar":
                    rename[key] = "Sonar Data"
    def _rename_rows(rows):
        out = []
        for row in rows:
            item = dict(row)
            for old, new in rename.items():
                if old in item:
                    item[new] = item.pop(old)
            out.append(item)
        return out
    matched = _rename_rows(matched)
    mismatched = _rename_rows(mismatched)
    if matched:
        st.markdown("*Matched fields (%d)*" % len(matched))
        _styled_diff_dataframe(matched, highlight_mismatch=True)
    if mismatched:
        st.markdown("*Mismatched fields (%d)*" % len(mismatched))
        _styled_diff_dataframe(mismatched, highlight_mismatch=True)
    if not matched and not mismatched:
        st.caption("No field-level comparison (pair N/A or no overlapping metrics).")


_LOCAL_OUTCOME_LEGEND = (
    "**Bug** expects `tool_outcome=FAIL` (violation present). "
    "**BugFX / TCC / CC** expect `tool_outcome=PASS` (TCC also needs effective config). "
    "`assert_status=PASS` means the branch-type contract is satisfied. "
    "`status` mirrors raw tool measurement. "
    "Real failures show `status=ERROR/UNAVAILABLE` or `real_tool=False`."
)


def _normalize_outcome(value):
    text = str(value or "").upper()
    if text.startswith("FAIL"):
        return "FAIL"
    if text.startswith("PASS") or text.startswith("WARN"):
        return "PASS"
    return text


def _local_failure_layer(report):
    """Derive which verification layer failed for a local report."""
    if not report:
        return ""
    extra = report.get("extra") or {}
    branch_type = report.get("branch_type") or ""
    tool_outcome = _normalize_outcome(extra.get("tool_outcome"))
    assert_status = str(extra.get("assert_status") or report.get("status") or "").upper()
    strength_pass = extra.get("strength_pass")
    config_effective = extra.get("config_effective")
    actual = str(extra.get("actual_outcome") or "")

    if assert_status == "PASS":
        return "ok"
    if branch_type == "Bug" and tool_outcome == "PASS":
        return "tool"
    if branch_type != "Bug" and tool_outcome == "FAIL":
        return "tool"
    if branch_type == "TCC" and config_effective is False:
        return "config"
    if "isolation FAIL" in actual:
        return "isolation"
    if strength_pass is False:
        return "strength"
    if assert_status == "FAIL":
        return "branch_type"
    return ""


def _local_run_success(branch_type, tool_outcome, assert_status):
    """True when tool + assert outcomes match branch-type expectations."""
    tool = _normalize_outcome(tool_outcome)
    assert_st = str(assert_status or "").upper()
    if assert_st != "PASS":
        return False
    if branch_type == "Bug":
        return tool == "FAIL"
    return tool == "PASS"


def _render_local_report(report):
    """Render local execution report with outcome legend."""
    if not report:
        st.caption("Local report pending — run Local tools tab.")
        return
    extra = report.get("extra") or {}
    st.caption(_LOCAL_OUTCOME_LEGEND)
    tool_outcome = extra.get("tool_outcome") or extra.get("actual_outcome", "—")
    assert_status = extra.get("assert_status", "—")
    st.dataframe(
        [{
            "branch_type": report.get("branch_type", "—"),
            "status": report.get("status", "?"),
            "tool": report.get("tool_name", "?"),
            "tool_outcome": tool_outcome,
            "expected_outcome": extra.get("expected_outcome", "—"),
            "assert_status": assert_status,
            "strength_pass": extra.get("strength_pass", "—"),
            "config_effective": extra.get("config_effective", "—"),
            "failure_layer": _local_failure_layer(report) or "—",
            "strength_reason": extra.get("strength_reason", "—"),
            "summary": report.get("raw_summary", ""),
        }],
        width="stretch",
    )
    metric_values = report.get("metric_values") or {}
    if metric_values:
        st.markdown("*Metric values*")
        st.json(metric_values)


def _render_raw_report(label, report):
    """Render the raw data captured for a single report: tool output, raw metric values, full JSON."""
    if not report:
        return
    st.markdown("**%s — raw data**" % label)
    extra = report.get("extra") or {}
    raw_metrics = {}
    for key in ("raw_metric_value", "metric_value", "raw_value", "tool_outcome", "actual_outcome"):
        if extra.get(key) not in (None, ""):
            raw_metrics[key] = extra.get(key)
    metric_values = report.get("metric_values") or {}
    if metric_values:
        raw_metrics["metric_values"] = metric_values
    if raw_metrics:
        st.markdown("*Raw metric values*")
        st.json(raw_metrics)
    tool_log = extra.get("tool_log") or extra.get("tool_stderr") or ""
    if tool_log:
        st.markdown("*Raw tool output*")
        st.code(tool_log, language=None)
    st.markdown("*Full report JSON*")
    st.json(report)


def _whitebox_result_row(bname, info, proof_row=None):
    """Build a display row for whitebox run results."""
    proof_row = proof_row or {}
    total = info.get("total_tasks") or 0
    completed = info.get("completed_tasks") or 0
    failed = info.get("failed_tasks") or 0
    tasks = "%d/%d" % (completed, total) if total else "—"
    issues = proof_row.get("issues") or format_branch_issues(info, proof_row.get("s3_report_obj"))
    return {
        "branch": bname,
        "whitebox": info.get("status", "NOT_COMPLETED"),
        "run": info.get("run_status") or "—",
        "tasks": tasks,
        "failed": failed if total else "—",
        "run_health": info.get("run_health", "—"),
        "taxonomy": proof_row.get("taxonomy_report", "—"),
        "s3": proof_row.get("s3_report", "—"),
        "issues": "; ".join(issues) if issues else "—",
        "detail": proof_row.get("taxonomy_detail") or proof_row.get("s3_detail") or info.get("run_health_detail") or info.get("detail", ""),
    }


def _render_detailed_comparison(comparison):
    if not comparison:
        st.info("No comparison data — need at least S3 or local report.")
        return
    if comparison.get("verdict") == "INCOMPLETE":
        st.warning(comparison.get("summary", "Comparison incomplete"))
        return
    st.markdown("**Overall verdict:** `%s`" % comparison.get("verdict", "UNKNOWN"))
    if comparison.get("summary"):
        st.caption(comparison["summary"])
    tax_status = comparison.get("taxonomy_status", "—")
    tax_vs_s3 = comparison.get("taxonomy_vs_s3", "—")
    tax_vs_local = comparison.get("taxonomy_vs_local", "—")
    st.caption(
        "Taxonomy (reference only): `%s` — agrees with S3: **%s** — agrees with local: **%s**"
        % (tax_status, tax_vs_s3, tax_vs_local)
    )
    for label, key in (
        ("S3", "s3_status"),
        ("Local", "local_status"),
        ("SonarQube", "sonar_status"),
    ):
        status = comparison.get(key, "—")
        if status == "SKIPPED":
            st.caption("%s: N/A — report not produced" % label)
    st.dataframe(
        [{
            "s3": comparison.get("s3_status", "—"),
            "local": comparison.get("local_status", "—"),
            "sonar": comparison.get("sonar_status", "—"),
        }],
        width="stretch",
    )
    _render_pair_diffs("S3 vs Local", comparison.get("s3_vs_local"))
    _render_pair_diffs("Local vs SonarQube", comparison.get("local_vs_sonar"))


def _load_branch_comparison(bname, bundle, readiness_row):
    if bundle and bundle.get("comparison"):
        return bundle["comparison"]
    proof_dir = (bundle or {}).get("proof_dir")
    if proof_dir:
        comp_path = Path(proof_dir) / "comparison.json"
        if comp_path.is_file():
            return json.loads(comp_path.read_text(encoding="utf-8"))
    can_compare = readiness_row.get("can_compare")
    if can_compare is None:
        can_compare = readiness_row.get("s3") or readiness_row.get("local")
    if can_compare:
        try:
            return collect_comparison_proof(bname, root=str(ROOT))
        except Exception as exc:
            return {
                "branch_name": bname,
                "verdict": "ERROR",
                "summary": str(exc),
            }
    return None


def _comparison_results_for_branches(completed):
    results = []
    cached = st.session_state.get("last_comparisons") or []
    cached_by = {
        row.get("branch_name"): row
        for row in cached
        if row.get("branch_name")
    }
    for bname in completed:
        if bname in cached_by:
            results.append(cached_by[bname])
            continue
        bundle = load_proof_bundle(bname, root=str(ROOT)) or {}
        if bundle.get("comparison"):
            results.append(bundle["comparison"])
            continue
        proof_dir = bundle.get("proof_dir")
        if proof_dir:
            comp_path = Path(proof_dir) / "comparison.json"
            if comp_path.is_file():
                results.append(json.loads(comp_path.read_text(encoding="utf-8")))
    return results


def _branches_on_github(branch_names):
    """In-scope branches that exist on the connected GitHub repo."""
    if not _github_read_config():
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
    if not audit.get("s3_ready"):
        audit["s3_live_ok"] = False
        audit["s3_live_reason"] = "AWS credentials not configured"
        return audit

    ttl = 60
    now = time.time()
    cached_ts = st.session_state.get("_s3_live_check_ts") or 0.0
    if now - cached_ts < ttl and "_s3_live_ok" in st.session_state:
        audit["s3_live_ok"] = bool(st.session_state.get("_s3_live_ok"))
        audit["s3_live_reason"] = st.session_state.get("_s3_live_reason") or ""
    else:
        live = s3_live_check()
        st.session_state["_s3_live_check_ts"] = now
        st.session_state["_s3_live_ok"] = live.get("ok", False)
        st.session_state["_s3_live_reason"] = live.get("reason") or ""
        audit["s3_live_ok"] = live.get("ok", False)
        audit["s3_live_reason"] = live.get("reason") or ""
    return audit


def _qa_env_creds():
    """QA email/password from .env.local (AUTH_EMAIL / AUTH_PASSWORD)."""
    email = os.environ.get("AUTH_EMAIL", "").strip()
    password = os.environ.get("AUTH_PASSWORD", "")
    if email and password:
        return email, password
    return None, None


def _qa_session_creds():
    """Return (email, password) saved from the login form, or (None, None)."""
    if not st.session_state.get("qa_login_ok"):
        return None, None
    email = st.session_state.get("qa_email_saved", "").strip()
    password = st.session_state.get("qa_password_saved", "")
    if email and password:
        return email, password
    return None, None


def _qa_effective_creds():
    """Run identity = the sidebar-signed-in account only (no silent .env fallback)."""
    email, password = _qa_session_creds()
    if email and password:
        return email, password, "session"
    return None, None, None


def _qa_creds_ready(audit):
    """QA ready when Testable URLs are configured and credentials are available."""
    if not audit.get("testable_ready"):
        return False
    urls_ok = audit.get("testable_urls_ok", False)
    email, password, _ = _qa_effective_creds()
    return urls_ok and bool(email and password)


def _app_user_email(audit=None):
    """App identity — the connected GitHub account, decoupled from the QA password."""
    github_user = (st.session_state.get("github_user_login") or "").strip()
    if github_user:
        return github_user
    bound = (st.session_state.get("_bound_app_user") or "").strip()
    if bound:
        return bound
    return (st.session_state.get("qa_email_saved") or "").strip()


def _ensure_scm_identity():
    """Identity used to carry OAuth state before the GitHub username is known.

    Returns the established app identity when present, otherwise mints a stable
    per-browser-session token so GitHub connect works with no prior sign-in.
    """
    existing = _app_user_email()
    if existing:
        return existing
    token = (st.session_state.get("_scm_anon_user") or "").strip()
    if not token:
        token = "pending-%s" % secrets.token_urlsafe(12)
        st.session_state["_scm_anon_user"] = token
    return token


def _scm_app_user():
    """App user for GitHub/SCM — established identity or bootstrapped token."""
    return _ensure_scm_identity()


_GITHUB_SCOPED_SESSION_KEYS = (
    "github_token_saved", "github_repo_slug", "github_user_login",
    "github_login_ok", "github_login_msg", "github_repo_url",
    "github_default_branch", "github_push_method", "github_oauth_url_cache",
    "github_needs_install", "github_access_detail", "github_first_connect",
    "scm_view", "scm_callback", "scm_discovered_repos", "scm_discovery_error",
)

_PIPELINE_SCOPED_SESSION_KEYS = (
    "gen_rows", "validate_rows", "validate_ok", "last_branch_pipeline",
    "last_asserts", "last_pushed", "push_status_cache",
    "last_whitebox_branches", "last_qa_rc", "last_qa_batch",
    "last_local_run", "last_local_log", "last_sonar_run", "last_sonar_log",
    "last_gen_log", "last_validate_log", "last_push_log",
    "repo_switch_notice",
)

_USER_SCOPED_SESSION_KEYS = _GITHUB_SCOPED_SESSION_KEYS + _PIPELINE_SCOPED_SESSION_KEYS


def _clear_qa_session_caches():
    """Drop QA catalog/repo caches when the Testable account changes."""
    for key in (
        "_qa_connected_repos",
        "_qa_connected_repos_branches",
        "_wb_catalog_preview",
        "_wb_catalog_preview_slug",
        "_wb_catalog_preview_branches",
        "qa_repo_override",
        "qa_repo_select_rev",
        "_qa_best_repo",
    ):
        st.session_state.pop(key, None)


def _apply_qa_login(env_file, email, password):
    """Verify and persist QA credentials; invalidate caches on account switch."""
    email = (email or "").strip()
    prev = (st.session_state.get("qa_email_saved") or "").strip()
    ok, msg = verify_login(env_file, email, password)
    if not ok:
        st.session_state["qa_login_ok"] = False
        st.session_state["qa_login_msg"] = msg
        return False, msg
    if prev and prev.lower() != email.lower():
        _clear_qa_session_caches()
    st.session_state["qa_email_saved"] = email
    st.session_state["qa_password_saved"] = password
    st.session_state["qa_login_ok"] = True
    st.session_state["qa_login_msg"] = msg
    return True, msg


def _sign_out_qa_only():
    st.session_state.pop("qa_email_saved", None)
    st.session_state.pop("qa_password_saved", None)
    st.session_state.pop("qa_login_ok", None)
    st.session_state.pop("qa_login_msg", None)
    _clear_qa_session_caches()
    stop_report_sync(_app_user_email())


def _clear_pipeline_scoped_session():
    for key in _PIPELINE_SCOPED_SESSION_KEYS:
        st.session_state.pop(key, None)


def _clear_github_scoped_session():
    for key in _GITHUB_SCOPED_SESSION_KEYS:
        st.session_state.pop(key, None)


def _clear_user_scoped_session():
    for key in _USER_SCOPED_SESSION_KEYS:
        st.session_state.pop(key, None)


def _bind_github_identity(identity):
    """Bind app identity to GitHub account; clear pipeline state on switch."""
    identity = (identity or "").strip()
    prev = (st.session_state.get("_bound_app_user") or "").strip()
    if prev and identity and prev != identity:
        _clear_pipeline_scoped_session()
    if identity:
        st.session_state["_bound_app_user"] = identity
    else:
        st.session_state.pop("_bound_app_user", None)


def _bind_app_user(email):
    """Legacy bind helper — only used on full sign-out; does not touch GitHub."""
    del email
    st.session_state.pop("_bound_app_user", None)
    _clear_user_scoped_session()


def _sidebar_user_login(env_file):
    """Account status only — GitHub login lives on Branches, QA login on Whitebox."""
    del env_file
    st.sidebar.subheader("Account")
    github_connected = bool(st.session_state.get("github_login_ok"))
    github_user = (st.session_state.get("github_user_login") or "").strip()
    qa_signed_in = bool(st.session_state.get("qa_login_ok"))
    qa_email = (st.session_state.get("qa_email_saved") or "").strip()

    if github_connected and github_user:
        st.sidebar.caption("GitHub: **@%s**" % github_user)
    else:
        st.sidebar.caption("GitHub: connect on the **Branches** tab.")

    if qa_signed_in and qa_email:
        st.sidebar.caption("Testable QA: **%s**" % qa_email)
    else:
        st.sidebar.caption("Testable QA: sign in on the **Whitebox** tab.")

    if github_connected or qa_signed_in:
        if st.sidebar.button("Sign out", width="stretch", key="sidebar_sign_out"):
            _sign_out_qa_only()
            _disconnect_github()
            _bind_app_user("")
            st.rerun()


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



def _build_oauth_authorize_url(app_user, login_hint=None, account_picker=False):
    """Create OAuth state and authorization URL — mirrors POST /v1/scm/github/connect."""
    state = create_oauth_state(app_user, login_hint=login_hint)
    init = _oauth_service().initiate_connection(
        state,
        login_hint=login_hint,
        account_picker=account_picker,
    )
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


def _github_oauth_env_display():
    redirect_uri = os.getenv("GITHUB_OAUTH_REDIRECT_URI", "").strip()
    return {
        "client_id": os.getenv("GITHUB_OAUTH_CLIENT_ID", "").strip(),
        "redirect_uri": redirect_uri,
        "app_slug": os.getenv("GITHUB_APP_SLUG", "").strip() or "testable-assurance-studio",
        "callback_hint": redirect_uri or "http://localhost:8501/",
    }


def _format_stage_stop_cause(stop_cause):
    if stop_cause == "done":
        return "done"
    if stop_cause == "max_rounds":
        return "max rounds"
    if stop_cause == "stalled":
        return "stalled (no improvement)"
    if stop_cause == "errors":
        return "errors"
    return stop_cause or "unknown"


def _render_stage_status(label, status):
    if not status:
        return
    completed = status.get("completed") or []
    remaining = status.get("remaining") or []
    total = status.get("total") or (len(completed) + len(remaining))
    stop_cause = _format_stage_stop_cause(status.get("stop_cause"))
    rem_text = ", ".join(remaining) if remaining else "none"
    st.caption(
        "**%s** — Completed %d/%d. Remaining: %s. Stopped because: %s."
        % (label, len(completed), total, rem_text, stop_cause)
    )
    if status.get("stop_reason") and status.get("stop_cause") != "done":
        st.caption("Detail: %s" % status.get("stop_reason"))


def _render_github_oauth_diagnostics(app_user=None, sample_login_hint=None, key_prefix="oauth_diag"):
    """Show OAuth config, sample authorize URL, install link, and probe button."""
    from lib.scm import github_oauth

    cfg = _github_oauth_env_display()
    with st.expander("GitHub connection diagnostics", expanded=False):
        st.code(
            "client_id: %s\nredirect_uri: %s\napp_slug: %s"
            % (cfg["client_id"] or "(not set)", cfg["redirect_uri"] or "(not set)", cfg["app_slug"])
        )
        sample_url = None
        if app_user:
            try:
                sample_url = _build_oauth_authorize_url(app_user, login_hint=sample_login_hint)
                st.text_input("Sample authorize URL", value=sample_url, disabled=True, key="%s_url" % key_prefix)
            except Exception as exc:
                st.caption("Could not build sample URL: %s" % exc)
        st.markdown(
            "If GitHub shows **404** when you are already logged in, the App **Callback URL** must "
            "exactly equal `%s` (same as `redirect_uri` above)."
            % cfg["callback_hint"]
        )
        st.markdown(
            "[GitHub App settings](https://github.com/settings/apps/%s)" % cfg["app_slug"]
        )
        st.link_button(
            "Install / configure on GitHub",
            "https://github.com/apps/%s/installations/new" % cfg["app_slug"],
            key="%s_install" % key_prefix,
        )
        if sample_url and st.button("Test authorize URL", key="%s_probe" % key_prefix):
            ok, msg = github_oauth.probe_authorize_url(sample_url)
            if ok:
                st.success(msg)
            else:
                st.error(msg)


_GITHUB_DISCONNECT_KEYS = (
    "github_token_saved", "github_repo_slug", "github_user_login",
    "github_login_ok", "github_login_msg", "github_repo_url",
    "github_default_branch", "github_push_method", "github_oauth_url_cache",
    "github_needs_install", "github_access_detail", "github_oauth_error",
    "scm_view", "scm_callback", "scm_discovered_repos", "scm_discovery_error",
    "scm_login_hint",
)


def _disconnect_github():
    """Revoke DB connection (best effort) and clear all GitHub/SCM session state."""
    app_user = _app_user_email()
    if app_user:
        try:
            revoke_connection(app_user)
        except Exception:
            pass
    for key in _GITHUB_DISCONNECT_KEYS:
        st.session_state.pop(key, None)
    st.session_state.pop("push_status_cache", None)
    st.session_state["github_disconnect_notice"] = True


def _render_github_account_switch(app_user, key_prefix="github_switch"):
    """Switch GitHub account via OAuth authorize URL with optional login hint."""
    if not app_user:
        return
    with st.expander("Use a different GitHub account", expanded=False):
        st.caption(
            "Enter the GitHub username you want to use, then click below — GitHub will "
            "prompt you to sign in as that account and authorize. Leave blank to use "
            "the account already signed in to GitHub in this browser."
        )
        switch_hint = st.text_input(
            "GitHub username (optional)",
            placeholder="e.g. my-other-account",
            key="%s_hint" % key_prefix,
        )
        hint = (switch_hint or "").strip()
        try:
            st.session_state.pop("github_oauth_url_cache", None)
            switch_url = _build_oauth_authorize_url(app_user, login_hint=hint or None)
            st.link_button(
                "Log in / switch GitHub account",
                switch_url,
                width="stretch",
                key="%s_switch" % key_prefix,
            )
        except Exception as exc:
            st.caption("Could not build switch link: %s" % exc)


def _resolved_repo_slug():
    """Per-user target repo from Streamlit session, SCM DB, or .env.local fallback."""
    repo_slug = st.session_state.get("github_repo_slug", "").strip()
    app_user = _app_user_email()
    if app_user:
        conn = _oauth_connection(app_user)
        if conn:
            repo_slug = repo_slug or (conn.repo_slug or "").strip()
    if not repo_slug:
        repo_slug = os.environ.get("REPOSITORY_MATCH", "").strip()
    return repo_slug


def _github_pat_push_config(repo_slug=None):
    """Shared PAT push/read config from .env.local."""
    pat = os.environ.get("GITHUB_TOKEN", "").strip()
    repo_slug = (repo_slug or _resolved_repo_slug() or os.environ.get("REPOSITORY_MATCH", "")).strip()
    if not pat or not repo_slug:
        return None
    return {
        "token": pat,
        "repo_slug": repo_slug,
        "login": st.session_state.get("github_user_login", "") or repo_slug.split("/")[0],
        "default_branch": st.session_state.get("github_default_branch", "main"),
        "push_method": "pat",
    }


def _sync_github_session_from_db():
    """Hydrate Streamlit session from encrypted OAuth connection for current app user."""
    app_user = _scm_app_user()
    if not app_user:
        return None
    conn = _oauth_connection(app_user)
    if not conn or not conn.access_token:
        for key in (
            "github_login_ok", "github_token_saved", "github_user_login",
            "github_repo_slug", "github_repo_url", "github_push_method",
            "github_needs_install", "github_access_detail",
        ):
            st.session_state.pop(key, None)
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
    """Push config: per-user OAuth only when signed in; shared PAT if nobody is signed in."""
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
        session = _github_session()
        if session:
            return session
        return _github_pat_push_config(repo_slug)

    pat_cfg = _github_pat_push_config(repo_slug)
    if pat_cfg:
        return pat_cfg

    session = _github_session()
    if session:
        return session
    return None


def _github_read_config():
    """GitHub API config for read-only checks (branch status, whitebox repo).

    Signed-in users without OAuth still need branch presence checks; allow the
    shared PAT + REPOSITORY_MATCH fallback here only (push stays OAuth-only).
    """
    cfg = _github_push_config()
    if cfg:
        return cfg

    app_user = _app_user_email()
    if not app_user:
        return None

    repo_slug = _resolved_repo_slug() or os.environ.get("REPOSITORY_MATCH", "").strip()
    if not repo_slug:
        conn = get_connection(app_user)
        if conn:
            repo_slug = (conn.repo_slug or "").strip()

    return _github_pat_push_config(repo_slug)


def _github_pat_config():
    """Shared classic PAT push config — fallback when OAuth token cannot write."""
    return _github_pat_push_config()


def _github_install_prompt(repo_slug, detail=None):
    """Show install guidance when the GitHub App lacks repo access."""
    repo_slug = (repo_slug or "").strip()
    if detail:
        st.warning(detail)
    if repo_slug:
        st.caption(
            "1. Open [App permissions](%s) and set **Contents → Read and write**, then save. "
            "2. [Re-install the app](%s) on `%s`. "
            "3. Click **Connect GitHub** again on the Branches tab."
            % (github_app_permissions_url(), github_app_install_url(), repo_slug)
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
    return _github_read_config() is not None


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
        "last_gen_log",
        "last_validate_log",
        "last_push_log",
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

    if st.session_state.get("github_first_connect"):
        st.info(
            "Install the **Testable Assurance Studio** GitHub App on the repositories you will "
            "push to — this avoids push failures later."
        )
        st.link_button(
            "Install GitHub App",
            github_app_install_url(),
            width="stretch",
        )

    if st.session_state.get("github_needs_install"):
        _github_install_prompt(
            repo,
            st.session_state.get("github_access_detail")
            or "GitHub App is authorized but cannot write to this repository yet.",
        )

    app_user = _app_user_email()
    if app_user:
        _render_github_account_switch(app_user, key_prefix="github_switch_connected")
        _render_github_oauth_diagnostics(app_user, key_prefix="oauth_diag_connected")

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
            _disconnect_github()
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

    try:
        oauth_session = consume_oauth_state(state)
        app_user = (oauth_session.app_user or "").strip() or _scm_app_user()
        if not app_user:
            raise ValueError("OAuth state missing app user. Connect again.")

        svc = _oauth_service()
        result = svc.complete_connection(
            code,
            app_user,
            login_hint=oauth_session.login_hint,
        )
        identity = (result.app_identity or result.provider_username or app_user).strip()
        _bind_github_identity(identity)
        st.session_state.pop("_scm_anon_user", None)
        conn = svc.get_active_token(identity) or get_connection(identity)
        st.session_state["github_login_ok"] = True
        st.session_state["github_user_login"] = result.provider_username
        st.session_state["github_token_saved"] = (conn.access_token if conn else "")
        st.session_state["github_push_method"] = "oauth"
        st.session_state["github_first_connect"] = True
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

        app_user = _scm_app_user()
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
    if error_code in ("auth_required", "complete_failed"):
        st.info(
            "If you were signed in before GitHub redirected, your browser session may have expired. "
            "Use the **Account** panel in the sidebar to sign in again, then click **Try again**."
        )
    if st.button("Try again", type="primary", width="stretch"):
        st.session_state.pop("scm_view", None)
        st.session_state.pop("scm_callback", None)
        st.session_state.pop("github_oauth_url_cache", None)
        st.rerun()


def _scm_repo_picker_view():
    """Repository discovery + picker — mirrors reference repo browse after OAuth."""
    app_user = _scm_app_user()
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
            access_ok, access_detail = _recheck_github_access()
            if access_ok:
                st.session_state.pop("github_first_connect", None)
            elif st.session_state.get("github_first_connect"):
                st.session_state["github_needs_install"] = True
                st.session_state["github_access_detail"] = (
                    access_detail or selected.get("access_detail") or ""
                )
            _sync_repo_artifacts(show_notice=False)
            if access_ok or selected.get("access_ok"):
                st.success("Repository **%s** selected." % selected["repo_slug"])
            else:
                st.warning(
                    "Repository selected, but the GitHub App still needs install permissions."
                )
                _github_install_prompt(selected["repo_slug"], access_detail)
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
        app_user = _app_user_email()
        if not st.session_state.get("github_repo_slug"):
            st.info("GitHub is connected. Select a repository to enable branch push.")
            if st.button("View my repositories", type="primary", width="stretch"):
                st.session_state["scm_view"] = "repos"
                st.rerun()
            if app_user:
                _render_github_account_switch(app_user, key_prefix="github_switch_partial")
            if st.button("Disconnect GitHub", width="stretch"):
                _disconnect_github()
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

    app_user = _ensure_scm_identity()

    st.caption(
        "You will authorize Testable with access to your repositories. "
        "After connecting, you can discover and pick a target repository."
    )
    login_hint = st.text_input(
        "GitHub username (optional)",
        placeholder="Leave blank to pick at sign-in",
        help="Only fill this to pre-select a specific GitHub account. "
        "Leave blank and use **Switch GitHub account** to authorize a different user.",
        key="scm_login_hint",
    )
    hint = (login_hint or "").strip()
    try:
        if hint:
            authorize_url = _ensure_oauth_authorize_url(app_user, login_hint=hint)
        else:
            authorize_url = _build_oauth_authorize_url(app_user, login_hint=None)
        st.link_button("Connect GitHub", authorize_url, type="primary", width="stretch")
        st.caption(
            "If GitHub shows **404** after you click Connect, open "
            "**GitHub connection diagnostics** below — the App Callback URL must equal "
            "`%s`."
            % (_github_oauth_env_display().get("callback_hint") or "http://localhost:8501/")
        )
        _render_github_oauth_diagnostics(app_user, sample_login_hint=hint or None, key_prefix="oauth_diag_connect")
        _render_github_account_switch(app_user, key_prefix="github_switch_connect")
        st.caption(
            "Opens GitHub to authorize — you will return here automatically. "
            "Use **Use a different GitHub account** below if you need another GitHub user."
        )
    except Exception as exc:
        st.error("Could not start GitHub OAuth: %s" % exc)

    if st.session_state.get("github_oauth_error"):
        st.error(st.session_state.pop("github_oauth_error"))


def _cached_selection_summary(techniques, metrics, types_tuple, version):
    """Cached branch scope — avoids recomputing 412-branch lists on every rerun."""
    from lib.pipeline_selection import selection_summary
    from lib.registry import load_registry

    reg = load_registry()
    types = list(types_tuple) if types_tuple else None
    return selection_summary(techniques, metrics, types, version, reg)


_cached_selection_summary = st.cache_data(show_spinner="Updating scope…")(_cached_selection_summary)


def _scoped_dataframe(rows, label, key_prefix, page_size=TABLE_PAGE_SIZE):
    """Render large tables with pagination to keep the UI responsive."""
    if not rows:
        st.caption("No %s rows." % label.lower())
        return
    total = len(rows)
    if total <= page_size:
        st.dataframe(rows, width="stretch")
        return
    pages = max(1, (total + page_size - 1) // page_size)
    page_key = "%s_page" % key_prefix
    page = st.number_input(
        "%s page" % label,
        min_value=1,
        max_value=pages,
        value=min(int(st.session_state.get(page_key, 1)), pages),
        key=page_key,
    )
    start = (page - 1) * page_size
    end = min(start + page_size, total)
    st.caption("Showing %d–%d of %d" % (start + 1, end, total))
    st.dataframe(rows[start:end], width="stretch")


def _render_run_log_expanders():
    """Persisted pipeline run logs (Generate / Validate / Push)."""
    st.subheader("Run logs")
    log_specs = (
        ("Generate", "last_gen_log"),
        ("Validate", "last_validate_log"),
        ("Push", "last_push_log"),
    )
    for label, state_key in log_specs:
        lines = st.session_state.get(state_key) or []
        with st.expander("%s run log (%d lines)" % (label, len(lines)), expanded=False):
            if lines:
                st.code("\n".join(lines), language=None)
            else:
                st.caption("No %s run recorded yet in this session." % label.lower())


def _resolve_repo_push_rows(in_scope, github_ready, force_refresh=False):
    """GitHub remote status — cached; auto-fetch only for small scopes."""
    if not github_ready or not in_scope:
        return [], False, True
    key = _push_status_cache_key(in_scope)
    cache = st.session_state.get("push_status_cache")
    if not force_refresh and cache and cache.get("key") == key:
        return cache["rows"], cache["all_pushed"], True
    if not force_refresh and len(in_scope) > LARGE_SCOPE_THRESHOLD:
        return [], False, False
    with st.spinner("Checking GitHub status for %d branches…" % len(in_scope)):
        rows, all_pushed = _branch_push_status(in_scope, force_refresh=True)
    return rows, all_pushed, True


def _sidebar_filters():
    st.sidebar.image(str(LOGO), width=120)
    env_file = str(ROOT / ".env.local")
    _sidebar_user_login(env_file)
    st.sidebar.header("Selection")
    registry = load_registry()
    tech_opts = technique_options(registry)
    tech_codes = [c for c, _ in tech_opts]
    type_opts = branch_type_options(registry)
    version = st.sidebar.text_input("Version", "2.6", key="sidebar_version")
    full_count = full_scope_branch_count(registry, version)

    use_all_techniques = st.sidebar.checkbox(
        "All techniques (%d)" % full_count,
        value=False,
        key="sidebar_use_all_techniques",
    )

    prev_all_techniques = st.session_state.get("_sidebar_prev_all_techniques", False)
    if use_all_techniques and not prev_all_techniques:
        st.session_state["sidebar_techniques_pick"] = list(tech_codes)
        _cached_selection_summary.clear()
    if not use_all_techniques and prev_all_techniques:
        st.session_state["sidebar_techniques_pick"] = ["SA"]
    st.session_state["_sidebar_prev_all_techniques"] = use_all_techniques

    if use_all_techniques:
        selected_techniques = list(tech_codes)
        techniques = "all"
        st.session_state["sidebar_techniques_all_display"] = list(tech_codes)
        st.sidebar.multiselect(
            "Techniques",
            tech_codes,
            format_func=lambda c: next(l for code, l in tech_opts if code == c),
            disabled=True,
            key="sidebar_techniques_all_display",
        )
    else:
        if "sidebar_techniques_pick" not in st.session_state:
            st.session_state["sidebar_techniques_pick"] = ["SA"]
        selected_techniques = st.sidebar.multiselect(
            "Techniques",
            tech_codes,
            format_func=lambda c: next(l for code, l in tech_opts if code == c),
            key="sidebar_techniques_pick",
        )
        techniques = csv_from_list(selected_techniques) if selected_techniques else "SA"

    techs_for_metrics = list(tech_codes) if use_all_techniques else selected_techniques
    metric_choices = qualified_metric_choices(techs_for_metrics, registry)

    use_all_metrics = st.sidebar.checkbox(
        "All metrics",
        value=False,
        key="sidebar_use_all_metrics",
    )
    prev_all_metrics = st.session_state.get("_sidebar_prev_all_metrics", False)
    if use_all_metrics and not prev_all_metrics:
        st.session_state["sidebar_metrics_pick"] = list(metric_choices)
        _cached_selection_summary.clear()
    if not use_all_metrics and prev_all_metrics and use_all_techniques:
        st.session_state["sidebar_metrics_pick"] = list(metric_choices)
    st.session_state["_sidebar_prev_all_metrics"] = use_all_metrics

    if use_all_metrics:
        metrics = "all"
        st.session_state["sidebar_metrics_all_display"] = list(metric_choices)
        st.sidebar.multiselect(
            "Metrics",
            metric_choices,
            disabled=True,
            key="sidebar_metrics_all_display",
        )
    else:
        if "sidebar_metrics_pick" not in st.session_state:
            st.session_state["sidebar_metrics_pick"] = list(metric_choices) if use_all_techniques else []
        picked = st.sidebar.multiselect(
            "Metrics",
            metric_choices,
            key="sidebar_metrics_pick",
        )
        if picked:
            metrics = csv_from_list(picked)
        else:
            metrics = "all"

    types = st.sidebar.multiselect("Branch types", type_opts, default=type_opts, key="sidebar_branch_types") or type_opts

    lang_opts = list(SUPPORTED_UI_LANGUAGES)
    language = st.sidebar.selectbox(
        "Language",
        lang_opts,
        index=lang_opts.index("python") if "python" in lang_opts else 0,
        format_func=lambda c: c.capitalize(),
    )
    language = normalize_language(language)
    runtime_opts = language_runtimes(language)
    runtime = st.sidebar.selectbox("Runtime version", runtime_opts, index=runtime_opts.index(default_runtime(language)) if default_runtime(language) in runtime_opts else 0)
    runtime = normalize_runtime(language, runtime)
    st.sidebar.caption(sidebar_language_caption(language))

    if use_all_techniques and use_all_metrics:
        st.sidebar.caption(
            "Scope: all **%d** techniques, all **%d** qualified metrics."
            % (len(tech_codes), len(metric_choices))
        )
    elif use_all_techniques:
        st.sidebar.caption("Scope: all **%d** techniques." % len(tech_codes))

    summary = _cached_selection_summary(techniques, metrics, tuple(types), version)
    st.sidebar.metric("In scope", summary["branch_count"])

    audit = _readiness()
    qa_ok = _qa_creds_ready(audit)
    s3_ok = audit.get("s3_live_ok") if audit.get("s3_ready") else False
    c1, c2, c3 = st.sidebar.columns(3)
    c1.metric("QA", "OK" if qa_ok else "—")
    c2.metric("S3", "OK" if s3_ok else ("expired" if audit.get("s3_ready") else "—"))
    c3.metric("GitHub", "OK" if _github_creds_ready() else "—")

    if audit.get("s3_ready") and not s3_ok:
        st.sidebar.caption(audit.get("s3_live_reason") or "S3 credentials rejected by AWS.")
        if st.sidebar.button("Reload credentials from .env.local", key="reload_env_creds"):
            env_path = str(ROOT / ".env.local")
            load_env(env_path, override=True)
            n = reload_s3_credentials(env_path, root=str(ROOT))
            st.session_state.pop("_s3_live_check_ts", None)
            st.session_state.pop("_s3_live_ok", None)
            st.sidebar.success("Reloaded %d S3/AWS key(s) from .env.local" % n)
            st.rerun()

    if qa_ok:
        sync_user = _app_user_email(audit)
        start_report_sync(sync_user, root=str(ROOT), scope_branches=summary["branches"])
        sync_st = report_sync_status(sync_user)
        if sync_st.get("running"):
            last_ts = sync_st.get("last_tick_ts") or 0.0
            if last_ts:
                ago = max(0, int(time.time() - last_ts))
                sync_line = "Auto-sync: on — last pull %ds ago, %d synced" % (
                    ago, sync_st.get("synced_count", 0),
                )
            else:
                sync_line = "Auto-sync: starting… (%d pending)" % sync_st.get("pending_count", 0)
            st.sidebar.caption(sync_line)
            if sync_st.get("last_error"):
                st.sidebar.caption("Sync note: %s" % sync_st["last_error"][:120])
            if st.sidebar.button("Sync S3 reports now", key="sidebar_sync_s3_now"):
                trigger_report_sync(sync_user)
                st.sidebar.success("Sync triggered.")
                st.rerun()

    return {
        "techniques": techniques,
        "metrics": metrics,
        "types": types,
        "version": version,
        "language": language,
        "runtime": runtime,
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

    github_config = _github_read_config()
    repo_slug = (github_config or {}).get("repo_slug") or _github_repo_for_links()
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


def _pipeline_scope_key(filters):
    """Stable key for sidebar selection — reset pipeline rows when this changes."""
    return (
        filters["techniques"],
        filters["metrics"],
        tuple(filters["types"]),
        filters["version"],
        filters["language"],
        filters["runtime"],
    )


def _resolve_pipeline_work_root(filters):
    """Pick the work dir for generate/validate; reuse pre-login default when user dir is empty."""
    scope_key = _pipeline_scope_key(filters)
    cache_key = "_pipeline_work_root_%s" % (scope_key,)
    if st.session_state.get("_pipeline_scope_key") != scope_key:
        st.session_state.pop(cache_key, None)
        st.session_state.pop("pipeline_work_fallback", None)

    if cache_key in st.session_state:
        return st.session_state[cache_key]

    app_user = _app_user_email()
    user_root = pipeline_work_dir(str(ROOT), app_user=app_user)
    if hydrate_gen_rows_from_work(
        user_root,
        filters["techniques"],
        filters["metrics"],
        filters["types"],
        filters["version"],
    ):
        st.session_state[cache_key] = user_root
        st.session_state.pop("pipeline_work_fallback", None)
        return user_root

    default_root = pipeline_work_dir(str(ROOT), app_user=None)
    if app_user and default_root != user_root and hydrate_gen_rows_from_work(
        default_root,
        filters["techniques"],
        filters["metrics"],
        filters["types"],
        filters["version"],
    ):
        st.session_state[cache_key] = default_root
        st.session_state["pipeline_work_fallback"] = True
        return default_root

    st.session_state[cache_key] = user_root
    st.session_state.pop("pipeline_work_fallback", None)
    return user_root


def _show_pipeline_flash():
    flash = st.session_state.pop("pipeline_flash", None)
    if not flash:
        return
    kind, message = flash
    if kind == "success":
        st.success(message)
    elif kind == "error":
        st.error(message)
    else:
        st.warning(message)


def _pipeline_state_path(work_root):
    return Path(work_root) / ".pipeline_state.json"


def _load_pipeline_validation(work_root):
    path = _pipeline_state_path(work_root)
    if not path.is_file():
        return [], False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return [], False
    return data.get("validate_rows") or [], bool(data.get("validate_ok"))


def _save_pipeline_validation(work_root, validate_rows, validate_ok):
    path = _pipeline_state_path(work_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"validate_rows": validate_rows, "validate_ok": validate_ok}, indent=2),
        encoding="utf-8",
    )


def _clear_pipeline_validation(work_root):
    path = _pipeline_state_path(work_root)
    if path.is_file():
        path.unlink()


def _score_history_path(work_root):
    return Path(work_root) / ".score_history.json"


def _load_score_history(work_root):
    path = _score_history_path(work_root)
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def _save_score_history(work_root, history):
    path = _score_history_path(work_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(history or {}, indent=2), encoding="utf-8")


def _fmt_score_value(val):
    if val is None:
        return "—"
    try:
        return "%.1f" % float(val)
    except (TypeError, ValueError):
        return str(val)


def _fmt_strength_value(val):
    if val is None:
        return "—"
    try:
        return str(int(val))
    except (TypeError, ValueError):
        return str(val)


def _pipeline_step_label(branches_available, gen_done, val_done, push_done):
    if push_done and val_done and gen_done:
        return 4, "All three steps complete for this scope."
    if val_done:
        return 3, "Step 3 of 3 — **Push** validated branches to GitHub."
    if branches_available:
        return 2, "Step 2 of 3 — **Validate** (run tools + strength asserts; required before Push)."
    return 1, "Step 1 of 3 — **Generate** branches locally first."


def _pending_branch_names(gen_rows, in_scope, incomplete_local=None):
    """Branches in scope that still need generation (failed, incomplete, or never started)."""
    incomplete = set(incomplete_local or [])
    generated_ok = {
        r["branch_name"]
        for r in gen_rows
        if r.get("branch_name") and r.get("generated") and r["branch_name"] not in incomplete
    }
    return [b for b in in_scope if b not in generated_ok]


def _execute_generate_run(
    filters,
    work_root,
    total,
    in_scope,
    repo_push_rows,
    pending_only,
    pending_branches,
    max_fix_attempts,
    auto_install,
    assert_table_fn,
):
    """Run full-scope or pending-only generate and update session state."""
    read_cfg = _github_read_config()
    strength_map = build_regeneration_strength_map(
        work_root,
        in_scope,
        github_config=read_cfg,
        push_rows=repo_push_rows,
        gen_rows=st.session_state.get("gen_rows") or [],
    )
    regenerated_branches = {b for b in in_scope if strength_map.get(b, 0) > 0}
    last_validate_rows = st.session_state.get("validate_rows") or []
    if not last_validate_rows:
        last_validate_rows, _ = _load_pipeline_validation(work_root)
    last_score_by_branch = {}
    for row in last_validate_rows:
        bname = row.get("branch_name")
        if bname and row.get("strength_score") is not None:
            last_score_by_branch[bname] = row.get("strength_score")
    last_strength_by_branch = {}
    for row in st.session_state.get("gen_rows") or []:
        bname = row.get("branch_name")
        if bname and row.get("strength") is not None:
            last_strength_by_branch[bname] = row.get("strength")
    score_history = snapshot_previous_scores(
        st.session_state.get("score_history") or _load_score_history(work_root),
        regenerated_branches,
        last_strength_by_branch=last_strength_by_branch,
        last_score_by_branch=last_score_by_branch,
    )
    st.session_state["score_history"] = score_history
    _save_score_history(work_root, score_history)

    n_run = len(pending_branches) if pending_only else total
    panel_title = (
        "Generating %d pending branches" % n_run
        if pending_only
        else "Generating %d branches" % total
    )
    gen_kwargs = dict(
        techniques=filters["techniques"],
        metrics=filters["metrics"],
        types=filters["types"],
        version=filters["version"],
        language=filters["language"],
        work_root=work_root,
        strength_map=strength_map,
        max_fix_attempts=int(max_fix_attempts),
        auto_install=auto_install,
        runtime=filters["runtime"],
    )

    with RunPanel(panel_title) as panel:
        with panel.stdout_redirect():
            if pending_only:
                gen_result = generate_branches(
                    branch_names_filter=pending_branches,
                    clear_existing=False,
                    progress_callback=panel.progress,
                    **gen_kwargs,
                )
            else:
                gen_result = generate_branches(
                    progress_callback=panel.progress,
                    **gen_kwargs,
                )

        if pending_only:
            by_name = {r["branch_name"]: r for r in st.session_state.get("gen_rows") or []}
            for row in gen_result.get("rows", []):
                by_name[row["branch_name"]] = row
            merged = [by_name[b] for b in in_scope if b in by_name]
            st.session_state["gen_rows"] = merged
            completed = sorted({r["branch_name"] for r in merged if r.get("generated")})
            remaining = [b for b in in_scope if b not in set(completed)]
            scope_success = not remaining
            gen_status = {
                "completed": completed,
                "remaining": remaining,
                "stop_cause": "done" if scope_success else gen_result.get("stop_cause", "errors"),
                "total": total,
                "stop_reason": gen_result.get("stop_reason"),
            }
        else:
            merged = gen_result.get("rows", [])
            st.session_state["gen_rows"] = merged
            scope_success = bool(gen_result.get("success"))
            gen_status = {
                "completed": gen_result.get("completed", []),
                "remaining": gen_result.get("remaining", []),
                "stop_cause": gen_result.get("stop_cause"),
                "total": gen_result.get("total", total),
                "stop_reason": gen_result.get("stop_reason"),
            }
            st.session_state.pop("validate_rows", None)
            st.session_state.pop("validate_ok", None)
            st.session_state.pop("last_branch_pipeline", None)
            _clear_pipeline_validation(work_root)

        score_history = update_regenerated_strength(
            st.session_state.get("score_history") or {},
            gen_result.get("rows", []),
        )
        st.session_state["score_history"] = score_history
        _save_score_history(work_root, score_history)
        st.session_state["pipeline_gen_status"] = gen_status
        st.session_state["last_gen_log"] = panel.log_lines

        if scope_success:
            if pending_only:
                st.session_state["pipeline_flash"] = (
                    "success",
                    "Generated all %d pending branch(es); %d/%d complete in `%s`. **Validate** when ready."
                    % (n_run, len(gen_status["completed"]), total, work_root),
                )
            else:
                st.session_state["pipeline_flash"] = (
                    "success",
                    "Generated %d branch(es) in `%s`. **Validate** is now enabled."
                    % (len(gen_result.get("generated", [])), work_root),
                )
            panel.set_result("complete", "complete")
            st.rerun()
        else:
            completed_count = len(gen_status.get("completed", []))
            remaining = gen_status.get("remaining", [])
            st.error(
                "Generated %d/%d branch(es). Could not generate: %s"
                % (completed_count, total, ", ".join(remaining[:20]) + ("…" if len(remaining) > 20 else "") or "none")
            )
            if gen_status.get("stop_reason"):
                st.caption("Detail: %s" % gen_status.get("stop_reason"))
            panel.set_result("error", "stopped")
        assert_table_fn(
            st.session_state.get("gen_rows") or merged,
            score_history=st.session_state.get("score_history"),
        )


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
                "Connect GitHub above (the connected account becomes your identity) "
                "or configure **GITHUB_TOKEN** + **REPOSITORY_MATCH** in `.env.local`."
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
                "Push uses the shared PAT from `.env.local`. Sign in via sidebar **Account** "
                "and connect GitHub OAuth if you want pushes under your own GitHub identity."
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

    _show_pipeline_flash()

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
    work_root = _resolve_pipeline_work_root(filters)

    scope_key = _pipeline_scope_key(filters)
    if st.session_state.get("_pipeline_scope_key") != scope_key:
        st.session_state["_pipeline_scope_key"] = scope_key
        st.session_state.pop("gen_rows", None)
        st.session_state.pop("validate_rows", None)
        st.session_state.pop("validate_ok", None)
        st.session_state.pop("score_history", None)
        for key in list(st.session_state.keys()):
            if key.startswith("_pipeline_work_root_"):
                st.session_state.pop(key, None)

    if not st.session_state.get("gen_rows"):
        hydrated = hydrate_gen_rows_from_work(
            work_root,
            filters["techniques"],
            filters["metrics"],
            filters["types"],
            filters["version"],
        )
        if hydrated:
            st.session_state["gen_rows"] = hydrated
    elif st.session_state.get("gen_rows"):
        sync_gen_rows_strength_from_work(st.session_state["gen_rows"], work_root)

    if not st.session_state.get("validate_rows"):
        saved_rows, saved_ok = _load_pipeline_validation(work_root)
        if saved_rows:
            st.session_state["validate_rows"] = saved_rows
            st.session_state["validate_ok"] = saved_ok

    gen_rows = st.session_state.get("gen_rows") or []
    validate_rows = st.session_state.get("validate_rows") or []

    incomplete_local = [
        r["branch_name"] for r in gen_rows
        if r.get("dir") and os.path.isdir(r.get("dir"))
        and not branch_materialized(r["dir"], r.get("technique_code", "SA"))
    ]
    if incomplete_local:
        st.session_state.pop("validate_rows", None)
        st.session_state.pop("validate_ok", None)
        validate_rows = []
        st.warning(
            "Repaired incomplete local copies (%d branch folder(s) had git metadata only). "
            "Click **2 — Validate branches** to repopulate and re-run asserts."
            % len(incomplete_local)
        )

    if "score_history" not in st.session_state:
        st.session_state["score_history"] = _load_score_history(work_root)

    validate_ok = bool(st.session_state.get("validate_ok"))
    n_generated = len([r for r in gen_rows if r.get("generated")])
    n_validated = len([r for r in validate_rows if r.get("overall") in ("PASS", "PARTIAL")])
    all_validated = validate_ok and n_validated > 0 and n_validated == n_generated
    n_pushed = len([r for r in validate_rows if r.get("pushed")])
    in_scope = filters["summary"]["branches"]
    pending_branches = _pending_branch_names(gen_rows, in_scope, incomplete_local)
    n_pending = len(pending_branches)
    push_status_loaded = False
    repo_push_rows = []
    n_on_github = 0
    all_pushed_remote = False
    if github_ready and in_scope:
        force_push_refresh = bool(st.session_state.pop("_force_push_status_refresh", False))
        repo_push_rows, all_pushed_remote, push_status_loaded = _resolve_repo_push_rows(
            in_scope, github_ready, force_refresh=force_push_refresh,
        )
        if push_status_loaded:
            n_on_github = len([r for r in repo_push_rows if r.get("on_github") == "yes"])

    gen_done = n_generated >= total and total > 0
    branches_available = gen_done or (n_on_github >= total and total > 0)
    val_done = all_validated
    push_done = n_pushed >= total and total > 0 and val_done
    step_no, step_msg = _pipeline_step_label(branches_available, gen_done, val_done, push_done)

    st.subheader("Pipeline progress")
    st_c1, st_c2, st_c3 = st.columns(3)
    with st_c1:
        st.metric("1 — Generate", "%d / %d" % (n_generated, total), "done" if gen_done else "pending")
    with st_c2:
        st.metric("2 — Validate", "%d / %d" % (n_validated, total), "done" if val_done else "pending")
    with st_c3:
        st.metric("3 — Push", "%d / %d" % (n_pushed, total), "done" if push_done else ("ready" if val_done else "pending"))
    st.caption("Work dir: `%s`" % work_root)
    if step_no == 4:
        st.success(step_msg)
    else:
        st.info(step_msg)

    pat_fallback = _github_pat_config()
    can_push = val_done and bool(_github_push_config() or pat_fallback)
    can_generate = total > 0 and github_ready
    can_validate = branches_available and github_ready

    gate_hints = []
    if total == 0:
        gate_hints.append("Select at least one technique, metric, and branch type in the sidebar.")
    elif not github_ready:
        gate_hints.append("Connect GitHub and select a repository above to enable **Generate**.")
    if not branches_available and can_generate:
        gate_hints.append("Complete **Generate** (all branches) before **Validate** unlocks.")
    elif branches_available and not gen_done and push_status_loaded and n_on_github >= total:
        gate_hints.append(
            "Branches exist on GitHub — **Validate** fetches them locally, or run **Generate** to escalate strength."
        )
    elif not push_status_loaded and github_ready and total > LARGE_SCOPE_THRESHOLD:
        gate_hints.append(
            "Large scope (%d branches) — click **Load GitHub status** below to check remote branches without slowing sidebar changes."
            % total
        )
    elif not can_validate and n_generated > 0 and n_generated < total:
        gate_hints.append(
            "Some branches missing locally — use **Generate pending** to resume, or push missing branches to GitHub."
        )
    if not can_push and validate_rows and not validate_ok:
        gate_hints.append("Fix validation failures, then **Push** unlocks.")
    elif not can_push and val_done and needs_install and not pat_fallback:
        gate_hints.append(
            "In **GitHub App Settings → Permissions & events → Contents**, set **Read & write** "
            "to enable **Push**."
        )

    if not val_done:
        if not branches_available:
            push_hint = "Complete **Generate** first (all %d branches)." % total
        elif not validate_rows:
            push_hint = (
                "Run **Validate** — tools execute per branch (expect several seconds each). "
                "Remote-only branches are fetched from GitHub first."
            )
        else:
            push_hint = "Validation did not pass for all branches — review the table and re-run **Validate**."
        st.warning("Push locked: %s" % push_hint)
    elif not can_push and needs_install and pat_fallback:
        st.info(
            "GitHub App OAuth lacks **Contents: Read & write** — **Push** will try OAuth first, "
            "then fall back to the shared PAT in `.env.local`."
        )
    elif not can_push and needs_install:
        st.warning(
            "Push locked: in **GitHub App Settings → Permissions & events → Contents**, "
            "set **Read & write** (not just install the app)."
        )

    btn_gen, btn_gen_pending, btn_val, btn_push = st.columns(4)
    with btn_gen:
        run_generate = st.button(
            "1 — Generate branches",
            type="primary" if step_no == 1 else "secondary",
            width="stretch",
            disabled=not can_generate,
        )
    with btn_gen_pending:
        can_generate_pending = can_generate and 0 < n_pending < total
        run_generate_pending = st.button(
            "Generate pending (%d)" % n_pending,
            type="secondary",
            width="stretch",
            disabled=not can_generate_pending,
            help="Generate only the branches not yet completed; keeps existing branches intact.",
        )
    with btn_val:
        run_validate = st.button(
            "2 — Validate branches",
            type="primary" if step_no == 2 else "secondary",
            width="stretch",
            disabled=not can_validate,
        )
    with btn_push:
        run_push = st.button(
            "3 — Push to GitHub",
            type="primary" if step_no == 3 else "secondary",
            width="stretch",
            disabled=not can_push or (needs_install and not pat_fallback),
        )

    gen_status = st.session_state.get("pipeline_gen_status") or {}
    val_status = st.session_state.get("pipeline_val_status") or {}
    push_status = st.session_state.get("pipeline_push_status") or {}
    _render_stage_status("Generate", gen_status)
    _render_stage_status("Validate", val_status)
    _render_stage_status("Push", push_status)

    if gate_hints:
        st.caption(" ".join(gate_hints))

    if github_ready and in_scope and not push_status_loaded:
        if st.button(
            "Load GitHub status (%d branches)" % total,
            key="load_github_status_branches",
            width="stretch",
        ):
            st.session_state["_force_push_status_refresh"] = True
            st.rerun()

    if github_ready and in_scope and push_status_loaded:
        with st.expander("Your repository — planned actions", expanded=total <= LARGE_SCOPE_THRESHOLD):
            repo_status_cols = st.columns([3, 1])
            with repo_status_cols[1]:
                if st.button("Refresh repo status", key="refresh_repo_status_branches", width="stretch"):
                    st.session_state["_force_push_status_refresh"] = True
                    st.rerun()
            repo_status_display = []
            regen_strength = build_regeneration_strength_map(
                work_root,
                in_scope,
                github_config=_github_read_config(),
                push_rows=repo_push_rows,
                gen_rows=st.session_state.get("gen_rows") or [],
            )
            for prow in repo_push_rows:
                exists = prow.get("on_github") == "yes"
                bname = prow.get("branch")
                next_strength = regen_strength.get(bname, 0)
                local_exists = os.path.isdir(os.path.join(work_root, bname or ""))
                if next_strength > 0 or exists or local_exists:
                    action = "regenerate at strength %d" % next_strength
                else:
                    action = "create"
                repo_status_display.append({
                    "branch": bname,
                    "in your repo": "yes" if exists else "new",
                    "remote sha": prow.get("remote_sha") or "—",
                    "planned action": action,
                })
            _scoped_dataframe(repo_status_display, "Repository status", "repo_status")
            st.caption(
                "Branches already in **%s** will be regenerated with higher strength (more code) on **Generate**. "
                "**planned action** shows the next write strength (0 = brand-new branch). "
                "Run **Validate** to execute tools — that step takes longer than Generate."
                % (repo_slug or "your repo")
            )

    def _rows_have_asserts(rows):
        for r in rows or []:
            if r.get("overall") or r.get("structure"):
                return True
        return False

    def _assert_table(rows, pushed_col=False, score_history=None):
        if not rows:
            return
        history = score_history if score_history is not None else st.session_state.get("score_history") or {}
        has_asserts = _rows_have_asserts(rows)
        display = []
        for r in rows:
            bname = r.get("branch_name")
            hist = history.get(bname) or {}
            is_regen = bool(hist.get("regenerated"))
            prev_strength = hist.get("prev_strength") if is_regen else None
            prev_score = hist.get("prev_score") if is_regen else None
            if has_asserts:
                cur_strength = r.get("strength")
                if cur_strength is None:
                    cur_strength = hist.get("cur_strength")
                cur_score = r.get("strength_score")
                if cur_score is None:
                    cur_score = hist.get("cur_score")
                row = {
                    "branch": bname,
                    "type": r.get("branch_type"),
                    "attempts": r.get("attempts"),
                    "structure": r.get("structure"),
                    "tool_support": r.get("tool_support"),
                    "metric_behavior": r.get("metric_behavior"),
                    "prev strength": _fmt_strength_value(prev_strength) if is_regen else "—",
                    "gen strength": _fmt_strength_value(cur_strength),
                    "prev score": _fmt_score_value(prev_score) if is_regen else "—",
                    "current score": _fmt_score_value(cur_score),
                    "delta": score_progress_display(prev_score, cur_score) if is_regen else "—",
                    "threshold": (r.get("expected_threshold") or "")[:50],
                    "overall": r.get("overall"),
                    "detail": r.get("failure_reason") or r.get("messages") or r.get("error", ""),
                }
            else:
                cur_strength = r.get("strength")
                cur_score = hist.get("cur_score") if is_regen else None
                row = {
                    "branch": bname,
                    "type": r.get("branch_type"),
                    "generated": "yes" if r.get("generated") else "no",
                    "prev strength": _fmt_strength_value(prev_strength) if is_regen else "—",
                    "gen strength": _fmt_strength_value(cur_strength),
                    "prev score": _fmt_score_value(prev_score) if is_regen else "—",
                    "current score": _fmt_score_value(cur_score),
                    "delta": score_progress_display(prev_score, cur_score) if is_regen else "—",
                    "loc": r.get("loc"),
                    "dir": r.get("dir") or "",
                }
            if pushed_col:
                row["pushed"] = "yes" if r.get("pushed") else "no"
                if r.get("commit_sha"):
                    row["commit"] = r.get("commit_sha")
            display.append(row)
        _scoped_dataframe(display, "Branch results", "branch_results_%s" % ("val" if has_asserts else "gen"))

    if run_generate or run_generate_pending:
        _execute_generate_run(
            filters,
            work_root,
            total,
            in_scope,
            repo_push_rows,
            pending_only=bool(run_generate_pending),
            pending_branches=pending_branches,
            max_fix_attempts=max_fix_attempts,
            auto_install=auto_install,
            assert_table_fn=_assert_table,
        )

    if run_validate:
        gen_rows = st.session_state.get("gen_rows") or []
        read_cfg = _github_read_config()
        st.session_state.pop("validate_ok", None)
        n_to_validate = len([r for r in gen_rows if r.get("dir") and os.path.isdir(r.get("dir"))])
        with RunPanel("Validating %d branches (strength asserts)" % max(n_to_validate, total)) as panel:
            with panel.stdout_redirect():
                if read_cfg and n_on_github > 0:
                    refreshed, materialized, fetch_errors = ensure_local_branches(
                        work_root,
                        read_cfg,
                        filters["techniques"],
                        filters["metrics"],
                        filters["types"],
                        filters["version"],
                        push_rows=repo_push_rows,
                    )
                    if refreshed:
                        st.session_state["gen_rows"] = refreshed
                        gen_rows = refreshed
                    if materialized:
                        print(
                            "Fetched %d branch(es) from GitHub: %s"
                            % (len(materialized), ", ".join(materialized))
                        )
                    for bname, err in fetch_errors:
                        print("Could not fetch %s from GitHub: %s" % (bname, err))
                val_result = validate_with_regeneration(
                    gen_rows,
                    filters["version"],
                    filters["language"],
                    max_fix_attempts=int(max_fix_attempts),
                    auto_install=auto_install,
                    max_rounds=25,
                    progress_callback=panel.progress,
                    block_strict=True,
                )
            st.session_state["validate_rows"] = val_result.get("rows", [])
            validate_rows = st.session_state.get("validate_rows") or []
            gen_by_name = {
                r["branch_name"]: r for r in (st.session_state.get("gen_rows") or []) if r.get("branch_name")
            }
            enriched_validate_rows = []
            for row in validate_rows:
                enriched = dict(row)
                if enriched.get("strength") is None:
                    gen_row = gen_by_name.get(row.get("branch_name"))
                    if gen_row:
                        enriched["strength"] = gen_row.get("strength")
                enriched_validate_rows.append(enriched)
            score_history = apply_current_scores(
                st.session_state.get("score_history") or _load_score_history(work_root),
                enriched_validate_rows,
            )
            st.session_state["score_history"] = score_history
            _save_score_history(work_root, score_history)
            generated_names = {
                r["branch_name"] for r in (st.session_state.get("gen_rows") or []) if r.get("generated")
            }
            validated_names = {
                r["branch_name"] for r in validate_rows if r.get("overall") in ("PASS", "PARTIAL")
            }
            all_pass = (
                generated_names
                and generated_names <= validated_names
                and all(r.get("overall") == "PASS" for r in validate_rows if r["branch_name"] in generated_names)
            )
            st.session_state["validate_ok"] = all_pass
            st.session_state["last_asserts"] = validate_rows
            st.session_state["last_branch_pipeline"] = val_result
            completed_val = sorted(validated_names & generated_names)
            remaining_val = sorted(generated_names - validated_names)
            if remaining_val:
                stop_cause = val_result.get("stop_cause") or "errors"
            else:
                stop_cause = "done" if all_pass else (val_result.get("stop_cause") or "errors")
            st.session_state["pipeline_val_status"] = {
                "completed": completed_val,
                "remaining": remaining_val,
                "stop_cause": stop_cause,
                "total": len(generated_names),
                "stop_reason": val_result.get("stop_reason"),
            }
            _save_pipeline_validation(work_root, validate_rows, all_pass)
            st.session_state["last_validate_log"] = panel.log_lines
            _assert_table(validate_rows, score_history=st.session_state.get("score_history"))
            if all_pass:
                scores = [
                    r.get("strength_score") for r in validate_rows
                    if r.get("strength_score") is not None
                ]
                avg = sum(scores) / len(scores) if scores else 0
                st.session_state["pipeline_flash"] = (
                    "success",
                    "All %d branch(es) passed validation (avg strength %.1f). **Push** is now enabled."
                    % (len(completed_val), avg),
                )
                panel.set_result("complete", "complete")
                st.rerun()
            else:
                st.error(
                    "Validation incomplete — completed %d/%d. Remaining: %s."
                    % (
                        len(completed_val),
                        len(generated_names),
                        ", ".join(remaining_val) or "none",
                    )
                )
                if val_result.get("stop_reason"):
                    st.caption("Detail: %s" % val_result.get("stop_reason"))
                panel.set_result("error", "blocked")

    if run_push:
        validate_rows = st.session_state.get("validate_rows") or []
        pipeline_toast = ("warning", "Push finished with issues")
        with RunPanel("Pushing %d branches to GitHub" % len(validate_rows)) as panel:
            with panel.stdout_redirect():
                push_result = push_branches(
                    validate_rows,
                    _github_push_config(),
                    fallback_config=_github_pat_config(),
                    progress_callback=panel.progress,
                )
            st.session_state["last_branch_pipeline"] = push_result
            pushed_rows = push_result.get("rows", [])
            if pushed_rows:
                st.session_state["validate_rows"] = pushed_rows
            validate_rows = st.session_state.get("validate_rows") or []
            pushable_names = {
                r["branch_name"] for r in validate_rows if r.get("overall") in ("PASS", "PARTIAL")
            }
            completed_push = sorted(
                r["branch_name"] for r in validate_rows if r.get("pushed")
            )
            remaining_push = sorted(pushable_names - set(completed_push))
            st.session_state["pipeline_push_status"] = {
                "completed": completed_push,
                "remaining": remaining_push,
                "stop_cause": push_result.get("stop_cause"),
                "total": len(pushable_names),
                "stop_reason": push_result.get("stop_reason"),
                "failed": push_result.get("failed") or [],
            }
            _save_pipeline_validation(work_root, validate_rows, bool(st.session_state.get("validate_ok")))
            _assert_table(
                validate_rows,
                pushed_col=True,
                score_history=st.session_state.get("score_history"),
            )
            if push_result.get("success"):
                msg = "Pushed %d branch(es) to GitHub." % len(completed_push)
                if push_result.get("used_fallback"):
                    msg += " " + (push_result.get("fallback_note") or "Used PAT fallback.")
                st.success(msg)
                st.session_state["last_pushed"] = completed_push
                st.session_state.pop("push_status_cache", None)
                st.session_state.pop("_wb_push_reconciled", None)
                panel.set_result("complete", "complete")
                pipeline_toast = ("success", msg)
                st.rerun()
            elif push_result.get("completed"):
                st.warning(
                    "Pushed %d/%d branch(es). Remaining: %s. Failed: %s."
                    % (
                        len(completed_push),
                        len(pushable_names),
                        ", ".join(remaining_push) or "none",
                        ", ".join(push_result.get("failed") or []) or "none",
                    )
                )
                if push_result.get("stop_reason"):
                    st.caption("Detail: %s" % push_result.get("stop_reason"))
                if push_result.get("needs_install"):
                    _github_install_prompt(repo_slug, push_result.get("stop_reason"))
                panel.set_result("error", "partial")
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
            st.session_state["last_push_log"] = panel.log_lines
        kind, msg = pipeline_toast
        if kind == "success":
            st.toast(msg, icon="✅")
        else:
            st.toast(msg, icon="⚠️")

    branch_table_rows = validate_rows if validate_rows else gen_rows
    if branch_table_rows:
        table_title = "Branch validation (strength)" if validate_rows else "Generated branches (local)"
        st.subheader(table_title)
        _assert_table(
            branch_table_rows,
            pushed_col=bool(validate_rows and any(r.get("pushed") for r in validate_rows)),
            score_history=st.session_state.get("score_history"),
        )

    _render_run_log_expanders()

    st.subheader("GitHub push status")
    refresh = st.button("Refresh GitHub status", key="refresh_push_branches")
    if refresh:
        st.session_state["_force_push_status_refresh"] = True
        st.rerun()
    if not github_ready:
        st.info("Connect GitHub to check push status.")
        push_rows, all_pushed = _branch_push_status(in_scope)
        push_status_loaded = True
    elif not push_status_loaded:
        st.info(
            "GitHub status not loaded for %d branches — click **Load GitHub status** above "
            "or **Refresh GitHub status** here to fetch remote branch SHAs."
            % total
        )
        push_rows, all_pushed = [], False
    else:
        push_rows, all_pushed = repo_push_rows, all_pushed_remote
    if push_rows:
        with st.expander("GitHub push status table", expanded=total <= LARGE_SCOPE_THRESHOLD):
            _scoped_dataframe(push_rows, "GitHub push status", "github_push")
    if push_status_loaded and all_pushed:
        st.success("All in-scope branches are on GitHub — whitebox can run.")
    elif push_status_loaded:
        not_pushed = [r["branch"] for r in push_rows if r.get("on_github") != "yes"]
        st.warning(
            "Whitebox is blocked until these branches are pushed: %s"
            % ", ".join(not_pushed[:20]) + ("…" if len(not_pushed) > 20 else "")
        )

    if st.session_state.get("last_asserts"):
        with st.expander("Previous validation details (full assert table)"):
            _scoped_dataframe(
                st.session_state["last_asserts"],
                "Validation details",
                "last_asserts",
            )


def _render_whitebox_qa_login(env_file, show_header=True, switch_mode=False):
    """QA (Testable) email/password sign-in form, scoped to the Whitebox stage."""
    if show_header:
        st.subheader("Testable QA sign-in")
        st.caption(
            "Whitebox runs under your Testable account — sign in here. This is separate "
            "from your GitHub connection on the **Branches** tab."
        )
    elif switch_mode:
        st.caption(
            "Enter a different Testable QA account below. The active account above is what "
            "whitebox runs will use until you sign in again."
        )
    with st.form("whitebox_qa_login", clear_on_submit=False):
        qa_email = st.text_input(
            "QA email",
            value="" if switch_mode else st.session_state.get("qa_email_saved", ""),
            key="whitebox_qa_login_email",
        )
        qa_password = st.text_input("QA password", type="password")
        submitted = st.form_submit_button(
            "Sign in as this account" if switch_mode else "Sign in",
            width="stretch",
        )
    if submitted:
        email = qa_email.strip()
        if not email or not qa_password:
            st.error("Enter email and password.")
        else:
            ok, msg = _apply_qa_login(env_file, email, qa_password)
            if ok:
                st.rerun()
            else:
                st.error(msg)


def _fetch_qa_connected_repositories(env_file, branch_names=None, force_refresh=False):
    """List repositories connected in Testable QA for the signed-in account."""
    email, password, _source = _qa_effective_creds()
    if not email or not password:
        return [], None
    cache_key = "_qa_connected_repos"
    cache_branches = "_qa_connected_repos_branches"
    branch_key = ",".join(branch_names or [])
    if (
        not force_refresh
        and st.session_state.get(cache_key) is not None
        and st.session_state.get(cache_branches) == branch_key
    ):
        return st.session_state.get(cache_key), None
    try:
        from lib.sa_qa import (
            PlatformClient,
            list_connected_repositories,
            login,
            rank_qa_repos_for_branches,
        )

        load_env(env_file)
        identity = os.environ.get("IDENTITY_URL")
        runtime = os.environ.get("RUNTIME_URL")
        views = os.environ.get("VIEWS_URL")
        token = login(identity, email, password)
        client = PlatformClient(identity, runtime, views, token)
        repos = list_connected_repositories(client)
        ranked = rank_qa_repos_for_branches(client, repos, branch_names)
        st.session_state[cache_key] = ranked
        st.session_state[cache_branches] = branch_key
        return ranked, None
    except Exception as exc:
        st.session_state[cache_key] = []
        st.session_state[cache_branches] = branch_key
        return [], str(exc)


def _qa_repo_option_label(row, branch_count):
    label = row.get("label") or "?"
    ready = row.get("ready_count", 0)
    if branch_count:
        return "%s (%d/%d branches ready)" % (label, ready, branch_count)
    return label


def _qa_repo_ready_count(connected_repos, label):
    row = next((row for row in (connected_repos or []) if row.get("label") == label), None)
    if not row:
        return 0
    return int(row.get("ready_count") or 0)


def _best_ready_qa_repo(connected_repos):
    for row in connected_repos or []:
        if int(row.get("ready_count") or 0) > 0:
            return row
    return None


def _resolve_qa_repo(gh_repo, connected_repos, branch_names=None, list_error=None):
    """Pick the Testable QA target repo (may differ from Stage 1 GitHub push repo)."""
    ranked = list(connected_repos or [])
    branch_names = list(branch_names or [])
    branch_count = len(branch_names)
    repo_labels = [row.get("label") for row in ranked if row.get("label")]
    best_row = _best_ready_qa_repo(ranked)
    gh_row = next(
        (row for row in ranked if (row.get("label") or "").lower() == (gh_repo or "").lower()),
        None,
    )

    saved = (st.session_state.get("qa_repo_override") or "").strip()
    if saved and saved not in repo_labels:
        saved = ""
        st.session_state.pop("qa_repo_override", None)

    saved_ready = _qa_repo_ready_count(ranked, saved) if saved else 0
    best_ready = int((best_row or {}).get("ready_count") or 0)
    should_auto_switch = bool(
        best_row
        and best_ready > 0
        and (
            not saved
            or saved_ready == 0
            or (
                saved.lower() == (gh_repo or "").lower()
                and gh_row
                and saved_ready < best_ready
            )
        )
    )
    if should_auto_switch:
        saved = best_row.get("label", "")
        st.session_state["qa_repo_override"] = saved
        st.session_state["qa_repo_select_rev"] = int(st.session_state.get("qa_repo_select_rev", 0)) + 1

    default_label = saved if saved in repo_labels else ""
    if not default_label and best_row:
        default_label = best_row.get("label", "")
    elif not default_label and gh_row:
        default_label = gh_row.get("label", "")
    elif not default_label and ranked:
        default_label = ranked[0].get("label", "")

    st.subheader("Testable QA repository")
    st.caption(
        "Stage 1 pushes branches to GitHub repo **%s**. Stage 2 triggers whitebox on the "
        "Testable QA-connected repo below (often a different slug)."
        % (gh_repo or "—")
    )

    selected_label = default_label
    if ranked:
        labels = [row.get("label") for row in ranked if row.get("label")]
        select_rev = int(st.session_state.get("qa_repo_select_rev", 0))
        selected_label = st.selectbox(
            "Connected repository",
            options=labels,
            index=labels.index(default_label) if default_label in labels else 0,
            format_func=lambda label: _qa_repo_option_label(
                next(row for row in ranked if row.get("label") == label),
                branch_count,
            ),
            help="Choose the repo you see in the Testable QA web UI where your branches are connected.",
            key="qa_repo_select_%s_%d" % (_app_user_email() or "anon", select_rev),
        )
        st.session_state["qa_repo_override"] = selected_label
    elif list_error:
        st.warning("Could not list connected QA repos: %s" % list_error)
    else:
        st.warning("No connected QA repositories found for this account — enter slug manually below.")

    manual_repo = st.text_input(
        "Manual QA repo override",
        value=st.session_state.get("qa_repo_manual", ""),
        placeholder=(best_row or {}).get("label") or gh_repo or "owner/repo",
        help="Use when the connected repo differs from the GitHub push repo or is missing from the list.",
        key="qa_repo_manual_input",
    ).strip()

    qa_repo = (manual_repo or selected_label or default_label or gh_repo or "").strip()
    if qa_repo:
        st.session_state["qa_repo_override"] = qa_repo
    if best_row:
        st.session_state["_qa_best_repo"] = best_row.get("label")

    selected_row = next((row for row in ranked if row.get("label") == qa_repo), None)
    if selected_row and branch_count and selected_row.get("ready_count", 0) == 0:
        if best_row:
            st.error(
                "QA repo **%s** has **0/%d** scoped branches in Testable. "
                "Select **%s** (%d/%d ready) in the dropdown above."
                % (
                    qa_repo,
                    branch_count,
                    best_row.get("label"),
                    best_row.get("ready_count", 0),
                    branch_count,
                )
            )
        else:
            st.error(
                "QA repo **%s** has **0/%d** scoped branches in its Testable catalog."
                % (qa_repo, branch_count)
            )
    elif qa_repo and gh_repo and qa_repo.lower() != gh_repo.lower():
        st.info(
            "Stage 2 will query Testable QA repo **%s** (not the GitHub push repo **%s**). "
            "Commit SHAs come from the QA catalog for that repo."
            % (qa_repo, gh_repo)
        )
    return qa_repo


def _whitebox_testable_catalog_preview(env_file, repository_match, branch_names, force_refresh=False):
    """Query Testable QA for branch catalog readiness (Stage 2 whitebox)."""
    email, password, _source = _qa_effective_creds()
    if not email or not password or not repository_match:
        return None
    cache_key = "_wb_catalog_preview"
    cache_slug = "_wb_catalog_preview_slug"
    cache_branches = "_wb_catalog_preview_branches"
    branch_key = ",".join(branch_names or [])
    if (
        not force_refresh
        and st.session_state.get(cache_key)
        and st.session_state.get(cache_slug) == repository_match
        and st.session_state.get(cache_branches) == branch_key
    ):
        return st.session_state.get(cache_key)
    try:
        from lib.sa_qa import (
            PlatformClient,
            catalog_branch_hints,
            login,
            preview_catalog_status,
        )

        load_env(env_file)
        identity = os.environ.get("IDENTITY_URL")
        runtime = os.environ.get("RUNTIME_URL")
        views = os.environ.get("VIEWS_URL")
        token = login(identity, email, password)
        client = PlatformClient(identity, runtime, views, token)
        preview = preview_catalog_status(
            client,
            repository_match,
            branch_names,
            project_name=os.environ.get("PROJECT_NAME"),
        )
        github_branch_names = None
        pat = os.environ.get("GITHUB_TOKEN", "").strip()
        if pat:
            from lib.github_api import list_repo_branches

            github_branch_names = list_repo_branches(pat, repository_match)
        ready_map = {name: {} for name in preview.get("ready") or []}
        preview["hints"] = catalog_branch_hints(
            client,
            repository_match,
            branch_names,
            catalog_branch_map=ready_map,
            github_branch_names=github_branch_names,
        )
        st.session_state[cache_key] = preview
        st.session_state[cache_slug] = repository_match
        st.session_state[cache_branches] = branch_key
        return preview
    except Exception as exc:
        return {"error": str(exc)}


def _tab_whitebox(filters):
    st.header("2 — Whitebox QA + taxonomy + S3")
    email_for_auth, password_for_auth, _cred_source = _qa_effective_creds()
    if not filters.get("qa_ready"):
        _render_whitebox_qa_login(filters["env_file"])
    else:
        st.success("Whitebox will run as **%s**." % email_for_auth)
        with st.expander("Switch Testable QA account", expanded=False):
            if st.button("Sign out QA only", key="whitebox_sign_out_qa"):
                _sign_out_qa_only()
                st.rerun()
            _render_whitebox_qa_login(
                filters["env_file"],
                show_header=False,
                switch_mode=True,
            )

    branches = filters["summary"]["branches"]
    n_in_scope = len(branches)

    read_cfg = _github_read_config()
    if read_cfg:
        st.caption(
            "GitHub repo: **%s** (%s) — %d branch(es) in sidebar scope."
            % (read_cfg.get("repo_slug", "—"), read_cfg.get("push_method", "oauth"), n_in_scope)
        )
    elif not _github_creds_ready():
        st.warning(
            "Connect GitHub on the **Branches** tab, or set **GITHUB_TOKEN** and "
            "**REPOSITORY_MATCH** in `.env.local` to check branch status."
        )

    gh_repo = (read_cfg or {}).get("repo_slug") or _resolved_repo_slug()

    hdr_cols = st.columns([3, 1])
    with hdr_cols[1]:
        wb_refresh = st.button("Refresh status", key="refresh_push_whitebox", width="stretch")
    if wb_refresh:
        st.session_state.pop("push_status_cache", None)
        st.session_state.pop("_wb_push_reconciled", None)
        st.session_state.pop("_wb_catalog_preview", None)
        st.session_state.pop("_qa_connected_repos", None)
        st.session_state.pop("_qa_connected_repos_branches", None)

    qa_repo = gh_repo
    auto_preview = _should_auto_whitebox_preview(branches, force_refresh=wb_refresh)
    if not auto_preview and n_in_scope > WHITEBOX_AUTO_PREVIEW_LIMIT:
        st.info(
            "Large selection (**%d** branches). Click **Refresh status** to load Testable catalog "
            "and GitHub state without blocking the page."
            % n_in_scope
        )
    if filters.get("qa_ready") and gh_repo and auto_preview:
        connected_repos, list_error = _fetch_qa_connected_repositories(
            filters["env_file"],
            branch_names=branches,
            force_refresh=wb_refresh,
        )
        qa_repo = _resolve_qa_repo(
            gh_repo,
            connected_repos,
            branch_names=branches,
            list_error=list_error,
        )

    catalog_preview = None
    if filters.get("qa_ready") and qa_repo and auto_preview:
        catalog_preview = _whitebox_testable_catalog_preview(
            filters["env_file"],
            qa_repo,
            branches,
            force_refresh=wb_refresh,
        )
        if catalog_preview and not catalog_preview.get("error"):
            ready_n = len(catalog_preview.get("ready") or [])
            missing = catalog_preview.get("missing") or []
            st.caption(
                "Testable catalog: project **%s** · QA repo **%s** · **%d/%d** scoped branches indexed (%d total in catalog)."
                % (
                    catalog_preview.get("project_name") or "—",
                    catalog_preview.get("repository_label") or qa_repo,
                    ready_n,
                    n_in_scope,
                    catalog_preview.get("catalog_total") or ready_n,
                )
            )
            if missing:
                st.warning(
                    "Testable catalog is missing **%d** branch(es) for QA repo **%s**: %s"
                    % (len(missing), qa_repo, ", ".join(missing))
                )
                for hint in catalog_preview.get("hints") or []:
                    st.info(hint)
        elif catalog_preview and catalog_preview.get("error"):
            st.caption("Testable catalog check: %s" % catalog_preview["error"])

    if auto_preview:
        push_rows, _ = _branch_push_status(branches, force_refresh=wb_refresh)
    else:
        push_rows = [{
            "branch": name, "on_github": "—", "remote_sha": "—",
            "repository": gh_repo or "—",
        } for name in branches]
    push_by_branch = {r["branch"]: r for r in push_rows}
    wb_status = whitebox_completion(branches, root=str(ROOT)) or {}

    readiness = []
    for bname in branches:
        push = push_by_branch.get(bname, {})
        wb = wb_status.get(bname, {})
        on_github_val = push.get("on_github")
        on_github = on_github_val == "yes"
        readiness.append({
            "branch": bname,
            "on_github": on_github_val if on_github_val in ("yes", "no") else "—",
            "whitebox": wb.get("status", "NOT_COMPLETED"),
            "run": wb.get("run_status") or "—",
            "tasks": (
                "%d/%d" % (wb.get("completed_tasks", 0), wb.get("total_tasks", 0))
                if wb.get("total_tasks") else "—"
            ),
            "failed": wb.get("failed_tasks") if wb.get("total_tasks") else "—",
            "run_health": wb.get("run_health", "—"),
            "gate_score": wb.get("gate_score"),
            "detail": wb.get("run_health_detail") or wb.get("detail") or ("on GitHub" if on_github else "not pushed"),
            "ready": "yes" if on_github else "no",
        })

    n_on_github = len([r for r in readiness if r["on_github"] == "yes"])
    n_completed = len([r for r in readiness if r["whitebox"] == "COMPLETED"])
    n_not_in_catalog = len([
        b for b in branches
        if wb_status.get(b, {}).get("status") == "SKIPPED"
        and "catalog" in (wb_status.get(b, {}).get("detail") or "").lower()
    ])
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("In scope", n_in_scope)
    with m2:
        st.metric("On GitHub", n_on_github)
    with m3:
        st.metric("Whitebox done", n_completed)

    st.subheader("Branch readiness")
    st.dataframe(readiness, width="stretch")

    history_rows = []
    for bname in branches:
        for run in branch_run_history(bname, root=str(ROOT))[:5]:
            history_rows.append({
                "branch": bname,
                "run_id": run.get("run_id") or "—",
                "status": run.get("run_status") or run.get("gate_status") or "—",
                "gate_score": run.get("gate_score"),
                "tasks": (
                    "%d/%d" % (run.get("completed_tasks", 0), run.get("total_tasks", 0))
                    if run.get("total_tasks") else "—"
                ),
                "when": run.get("timestamp") or "—",
                "has_html": "yes" if run.get("html_path") else "no",
            })
    with st.expander("Previous whitebox runs", expanded=False):
        if history_rows:
            st.dataframe(history_rows, width="stretch")
        else:
            st.caption("No prior whitebox runs found for in-scope branches.")

    if n_not_in_catalog:
        st.warning(
            "**%d of %d** branch(es) are not in the Testable catalog yet. "
            "The app cannot force platform discovery — ask a Testable administrator to "
            "trigger a branch sync, or wait and re-run with a longer catalog sync wait."
            % (n_not_in_catalog, n_in_scope)
        )

    on_github = [r["branch"] for r in readiness if r["on_github"] == "yes"]
    on_github_set = set(on_github)
    not_on_github = [b for b in branches if b not in on_github_set]

    session_pushed = set(st.session_state.get("last_pushed") or [])
    for row in st.session_state.get("validate_rows") or []:
        if row.get("pushed") and row.get("branch_name") in branches:
            session_pushed.add(row["branch_name"])
    if session_pushed - on_github_set and read_cfg and not wb_refresh:
        if not st.session_state.get("_wb_push_reconciled"):
            st.session_state["_wb_push_reconciled"] = True
            st.session_state.pop("push_status_cache", None)
            st.rerun()

    if not on_github and read_cfg:
        if not_on_github:
            st.info(
                "No in-scope branches on GitHub yet. Push these on the **Branches** tab first: **%s**"
                % ", ".join(not_on_github)
            )
        else:
            st.info("No in-scope branches on GitHub yet. Generate and push on the **Branches** tab first.")

    picker_key = "whitebox_branch_picker"
    if picker_key not in st.session_state or wb_refresh:
        last = st.session_state.get("last_whitebox_branches", branches)
        st.session_state[picker_key] = [b for b in last if b in branches] or list(on_github) or list(branches)
    else:
        st.session_state[picker_key] = [
            b for b in st.session_state[picker_key] if b in branches
        ]
    if branches and not st.session_state.get(picker_key):
        st.session_state[picker_key] = list(on_github) or list(branches)

    st.subheader("Branches to run")
    sel_cols = st.columns([1, 1, 4])
    with sel_cols[0]:
        if st.button(
            "Select all on GitHub",
            key="wb_select_all",
            disabled=not on_github,
            width="stretch",
        ):
            st.session_state[picker_key] = list(on_github)
            st.rerun()
    with sel_cols[1]:
        if st.button("Clear selection", key="wb_clear_sel", width="stretch"):
            st.session_state[picker_key] = []
            st.rerun()

    selected = st.multiselect(
        "Choose branches for this whitebox batch",
        options=branches,
        help=(
            "All in-scope branches are listed. Whitebox runs only branches that exist on GitHub — "
            "see the readiness table above for on_github status."
        ),
        key=picker_key,
    )
    selected_runnable = [b for b in selected if b in on_github_set]
    selected_not_pushed = [b for b in selected if b not in on_github_set]
    already_completed, pending = split_completed_pending(selected, root=str(ROOT))
    pending_runnable = [b for b in pending if b in on_github_set]

    if already_completed:
        st.success(
            "**%d** selected branch(es) already have a whitebox run with reports — "
            "you can proceed to the next stage without re-running: %s"
            % (len(already_completed), ", ".join(already_completed))
        )
        if st.button(
            "Proceed to Compare",
            key="wb_proceed_compare",
            type="primary",
            width="stretch",
        ):
            st.session_state["main_pipeline_tab"] = "Compare"
            st.rerun()
    if pending_runnable:
        st.info(
            "**%d** selected branch(es) still need whitebox execution: %s"
            % (len(pending_runnable), ", ".join(pending_runnable))
        )

    if not selected:
        st.warning("Select at least one branch to run whitebox.")
    elif selected_not_pushed:
        st.warning(
            "These selected branches are **not on GitHub yet** — push them on the **Branches** tab "
            "before running: **%s**"
            % ", ".join(selected_not_pushed)
        )
    elif len(selected_runnable) < len(on_github):
        st.caption(
            "Running **%d** of **%d** branches on GitHub."
            % (len(selected_runnable), len(on_github))
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
        value=int(os.environ.get("PARTIAL_BRANCH_SYNC_SEC", "120")),
        help="How long to wait for GitHub branches to appear in the Testable catalog.",
    )

    wb_can_run = bool(read_cfg) and bool(pending_runnable) and filters.get("qa_ready")
    wb_blockers = []
    if not filters.get("qa_ready"):
        wb_blockers.append(
            "sign in with your Testable QA account in the **Testable QA sign-in** form above"
        )
    if not read_cfg:
        wb_blockers.append("configure GitHub (OAuth on Branches tab or GITHUB_TOKEN + REPOSITORY_MATCH)")
    if not selected:
        wb_blockers.append("select at least one branch")
    elif not pending_runnable and not already_completed:
        wb_blockers.append("push selected branches on the **Branches** tab (none are on GitHub yet)")
    if filters.get("qa_ready") and qa_repo and pending_runnable:
        ready_for_run = 0
        if catalog_preview and not catalog_preview.get("error"):
            ready_set = set(catalog_preview.get("ready") or [])
            ready_for_run = sum(1 for b in pending_runnable if b in ready_set)
        if ready_for_run == 0:
            best_label = st.session_state.get("_qa_best_repo")
            if best_label and best_label != qa_repo:
                wb_blockers.append(
                    "no selected branches in Testable catalog for QA repo **%s** — select **%s** in **Testable QA repository** above"
                    % (qa_repo, best_label)
                )
            else:
                wb_blockers.append(
                    "no selected branches in Testable catalog for QA repo **%s** — pick the connected repo where branches appear"
                    % qa_repo
                )
    wb_can_run = wb_can_run and not wb_blockers
    wb_can_rerun = bool(read_cfg) and bool(selected_runnable) and filters.get("qa_ready")
    if wb_blockers and not pending_runnable:
        st.caption("Run blocked until: %s." % "; ".join(wb_blockers))
    elif wb_blockers and pending_runnable:
        st.caption("Run pending blocked until: %s." % "; ".join(wb_blockers))

    wb_run_targets = None
    if pending_runnable or (selected_runnable and not already_completed):
        btn_cols = st.columns(2 if (already_completed and pending_runnable) else 1)
        with btn_cols[0]:
            label = (
                "Run pending (%d)" % len(pending_runnable)
                if pending_runnable
                else "Run whitebox batch"
            )
            if st.button(
                label,
                type="primary",
                width="stretch",
                disabled=not wb_can_run,
                key="wb_run_pending_btn",
            ):
                wb_run_targets = list(pending_runnable or selected_runnable)
        if already_completed and pending_runnable and len(btn_cols) > 1:
            with btn_cols[1]:
                if st.button(
                    "Re-run all selected (%d)" % len(selected_runnable),
                    width="stretch",
                    disabled=not wb_can_rerun,
                    key="wb_rerun_all_btn",
                ):
                    wb_run_targets = list(selected_runnable)
    elif already_completed and selected_runnable:
        if st.button(
            "Re-run all selected (%d)" % len(selected_runnable),
            width="stretch",
            disabled=not wb_can_rerun,
            key="wb_rerun_completed_btn",
        ):
            wb_run_targets = list(selected_runnable)

    if wb_run_targets:
        if not read_cfg:
            st.error("Connect GitHub or configure read credentials before running whitebox.")
            return
        if not email_for_auth or not password_for_auth:
            st.error("Sign in using the **Account** panel in the sidebar before running whitebox.")
            return
        branches_csv = ",".join(wb_run_targets)
        with RunPanel("Whitebox QA (%d branches)" % len(wb_run_targets)) as panel:
            gh_repo = (read_cfg or {}).get("repo_slug") or _github_repo_for_links()
            if not gh_repo:
                st.error(
                    "Select a GitHub repository on the Branches tab, or set "
                    "**REPOSITORY_MATCH** in `.env.local` before running whitebox."
                )
                return
            qa_repo = (st.session_state.get("qa_repo_override") or gh_repo or "").strip()
            if not qa_repo:
                st.error(
                    "Select the Testable QA repository above (connected repo where branches appear in QA)."
                )
                return
            old_partial_sync = os.environ.get("PARTIAL_BRANCH_SYNC_SEC")
            old_branch_sync = os.environ.get("BRANCH_SYNC_TIMEOUT_SEC")
            old_prefer_github = os.environ.get("PREFER_GITHUB_COMMIT")
            os.environ["PARTIAL_BRANCH_SYNC_SEC"] = str(int(catalog_wait))
            if not allow_partial:
                os.environ["BRANCH_SYNC_TIMEOUT_SEC"] = str(max(int(catalog_wait), 300))
            if qa_repo.lower() != gh_repo.lower():
                os.environ["PREFER_GITHUB_COMMIT"] = "false"
            batch_meta = {}
            rc = 1
            batch_dir = None
            try:
                try:
                    with panel.io_redirect():
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
                            repository_match=qa_repo,
                            progress_callback=panel.progress,
                            result_meta=batch_meta,
                        )
                except Exception as exc:
                    panel.set_result("error", "failed")
                    st.error(_friendly_run_error(exc))
                    st.session_state["last_whitebox_log"] = panel.log_lines
                    return
            finally:
                if old_partial_sync is not None:
                    os.environ["PARTIAL_BRANCH_SYNC_SEC"] = old_partial_sync
                else:
                    os.environ.pop("PARTIAL_BRANCH_SYNC_SEC", None)
                if old_branch_sync is not None:
                    os.environ["BRANCH_SYNC_TIMEOUT_SEC"] = old_branch_sync
                else:
                    os.environ.pop("BRANCH_SYNC_TIMEOUT_SEC", None)
                if old_prefer_github is not None:
                    os.environ["PREFER_GITHUB_COMMIT"] = old_prefer_github
                else:
                    os.environ.pop("PREFER_GITHUB_COMMIT", None)
            error_lines = [ln for ln in panel.log_lines if "ERROR:" in ln]
            if rc != 0:
                panel.set_result("error", "failed")
                if error_lines:
                    st.error(error_lines[-1])
                else:
                    st.error(
                        "Whitebox batch failed before saving taxonomy reports for QA repo **%s**."
                        % qa_repo
                    )
            st.session_state["last_qa_rc"] = rc
            st.session_state["last_qa_batch"] = batch_dir
            st.session_state["last_whitebox_branches"] = wb_run_targets
            skipped_catalog = batch_meta.get("catalog_skipped") or []
            if skipped_catalog:
                st.warning(
                    "Skipped **%d** branch(es) not in Testable catalog: %s. "
                    "Stage 2 queried QA repo **%s** — confirm that is the repo "
                    "you checked in the Testable QA UI. Increase catalog sync wait and re-run, or "
                    "enable partial catalog to process branches that are ready."
                    % (len(skipped_catalog), ", ".join(skipped_catalog), qa_repo)
                )

            wb_after = whitebox_completion(wb_run_targets, root=str(ROOT))
            st.session_state["last_whitebox_detail"] = wb_after
            proof_rows = []
            panel.progress("proofs", 0, len(wb_run_targets), "", "collecting taxonomy + S3 proofs")
            for idx, bname in enumerate(wb_run_targets, 1):
                info = wb_after.get(bname, {})
                row = {
                    "branch": bname,
                    "whitebox": info.get("status", "NOT_COMPLETED"),
                    "run": info.get("run_status") or "—",
                    "tasks": (
                        "%d/%d" % (info.get("completed_tasks", 0), info.get("total_tasks", 0))
                        if info.get("total_tasks") else "—"
                    ),
                    "failed": info.get("failed_tasks") if info.get("total_tasks") else "—",
                    "run_health": info.get("run_health", "—"),
                    "detail": info.get("detail", ""),
                    "taxonomy_detail": info.get("detail", "") if info.get("status") != "COMPLETED" else "",
                    "s3_detail": "—",
                    "failing_sections": info.get("failing_sections") or [],
                    "issues": format_branch_issues(info),
                }
                s3_report = None
                if info.get("status") == "COMPLETED":
                    try:
                        with panel.stdout_redirect():
                            s3_report = collect_s3_proof(
                                bname,
                                meta=info.get("meta"),
                                root=str(ROOT),
                                manifest_run=info.get("manifest_run"),
                                expects_s3=info.get("expects_s3"),
                            )
                        row["taxonomy_report"] = "yes"
                        row["s3_report"] = s3_report.get("status", "?")
                        row["s3_report_obj"] = s3_report
                        row["taxonomy_detail"] = "taxonomy report collected"
                        if s3_report.get("status") == "N/A":
                            row["s3_detail"] = _skip_detail(s3_report)
                        elif s3_report.get("status") in ("SKIPPED", "AUTH"):
                            row["s3_detail"] = _skip_detail(s3_report)
                        else:
                            row["s3_detail"] = s3_report.get("raw_summary", "")
                    except Exception as exc:
                        row["taxonomy_report"] = "error"
                        row["s3_report"] = "ERROR"
                        row["s3_detail"] = str(exc)
                        row["issues"] = format_branch_issues(info) + ["S3 proof collection failed: %s" % exc]
                else:
                    row["taxonomy_report"] = "—"
                    row["s3_report"] = "—"
                if s3_report:
                    row["issues"] = format_branch_issues(info, s3_report)
                proof_rows.append(row)
                panel.progress("proofs", idx, len(wb_run_targets), bname, row["whitebox"])

            st.session_state["last_whitebox_status"] = proof_rows
            st.session_state["last_whitebox_log"] = panel.log_lines
            st.subheader("Run results")
            st.dataframe(
                [_whitebox_result_row(r["branch"], wb_after.get(r["branch"], {}), r) for r in proof_rows],
                width="stretch",
            )
            for r in proof_rows:
                branch_issues = r.get("issues") or []
                if branch_issues:
                    with st.expander("Issues — %s" % r["branch"]):
                        for line in branch_issues:
                            st.markdown("- %s" % line)
                sections = r.get("failing_sections") or []
                if sections:
                    with st.expander("Failing sections — %s" % r["branch"]):
                        st.dataframe(sections, width="stretch")
            completed = sum(1 for r in proof_rows if r["whitebox"] == "COMPLETED")
            degraded = [
                r for r in proof_rows
                if wb_after.get(r["branch"], {}).get("run_health") == "DEGRADED"
            ]
            partial_tasks = [
                r for r in proof_rows
                if wb_after.get(r["branch"], {}).get("run_health") == "OK"
                and (wb_after.get(r["branch"], {}).get("failed_tasks") or 0) > 0
            ]
            if rc != 0 or completed == 0:
                st.warning(
                    "Whitebox finished with issues: %d/%d branches completed with taxonomy reports"
                    % (completed, len(selected))
                )
            elif degraded:
                st.warning(
                    "Taxonomy produced for all branches, but %d run(s) had failed/partial whitebox tasks: %s"
                    % (len(degraded), ", ".join(r["branch"] for r in degraded))
                )
            elif partial_tasks:
                st.info(
                    "Whitebox completed for all %d branches. %d had non-blocking platform task failures "
                    "(taxonomy reports were still produced)."
                    % (completed, len(partial_tasks))
                )
                panel.set_result("complete", "complete")
            else:
                st.success("Whitebox completed for all %d selected branches" % completed)
                panel.set_result("complete", "complete")
        st.toast("Whitebox batch finished", icon="✅")

    elif st.session_state.get("last_whitebox_status"):
        wb_detail = st.session_state.get("last_whitebox_detail") or {}
        with st.expander("Previous whitebox run results", expanded=False):
            st.dataframe(
                [
                    _whitebox_result_row(
                        r["branch"],
                        wb_detail.get(r["branch"], {}),
                        r,
                    )
                    for r in st.session_state["last_whitebox_status"]
                ],
                width="stretch",
            )
            for r in st.session_state["last_whitebox_status"]:
                sections = r.get("failing_sections") or wb_detail.get(r["branch"], {}).get("failing_sections") or []
                if sections:
                    with st.expander("Failing sections — %s" % r["branch"]):
                        st.dataframe(sections, width="stretch")
            if st.session_state.get("last_whitebox_log"):
                st.code("\n".join(st.session_state["last_whitebox_log"]), language=None)


def _tab_local_tools(filters):
    st.header("3 — Local tool execution")
    branches = filters["summary"]["branches"]
    work_root = _resolve_pipeline_work_root(filters)
    on_github = _branches_on_github(branches) if _github_creds_ready() else []
    local_ready = [b for b in branches if os.path.isdir(os.path.join(work_root, b))]
    available = list(dict.fromkeys(local_ready + on_github))
    if not available:
        if not _github_creds_ready():
            st.info(
                "Connect GitHub on the Branches tab, or generate branches first so copies exist under "
                "`%s`." % work_root
            )
        else:
            st.info("No in-scope branches locally or on GitHub yet. Generate branches first.")
        return

    default_pick = st.session_state.get("last_whitebox_branches", available)
    default_pick = [b for b in default_pick if b in available] or available

    st.caption(
        "Uses a **persistent pre-validated tool environment** (`.tool_env/`) when isolated mode is on. "
        "Runs each metric's **registry primary tool** against your branch copy (prefers locally generated files under "
        "`%s`, falls back to GitHub only when missing), and saves a separate report per branch under `proofs/`."
        % os.path.basename(work_root)
    )
    st.info(_LOCAL_OUTCOME_LEGEND)

    with st.expander("Tool environment (capability matrix)", expanded=False):
        cap = load_capability_matrix()
        if cap:
            st.caption("Env key: `%s` | all runnable: **%s**" % (cap.get("env_key", "?"), cap.get("all_runnable")))
            fam_rows = []
            for family, info in sorted((cap.get("families") or {}).items()):
                fam_rows.append({
                    "family": family,
                    "runnable": info.get("runnable"),
                    "version": (info.get("version") or "")[:80],
                    "error": (info.get("error") or "")[:120],
                })
            if fam_rows:
                st.dataframe(fam_rows, width="stretch")
        else:
            st.info("No capability matrix yet. Click **Run tool doctor** to build/validate the environment.")
        if st.button("Run tool doctor", key="run_tool_doctor"):
            with st.spinner("Building tool environment and running smoke checks..."):
                matrix = run_tool_doctor(persist=True)
                if matrix.get("session"):
                    matrix.pop("session", None)
                st.session_state["tool_doctor_matrix"] = matrix
            st.success("Tool doctor complete. Matrix saved to proofs/_doctor/capability.json")
            st.rerun()
        if st.session_state.get("tool_doctor_matrix"):
            st.json(st.session_state["tool_doctor_matrix"])

    sweep_report_path = ROOT / "proofs" / "_diagnostics" / "sweep_report.json"
    with st.expander("Branch-generation diagnostics (sweep report)", expanded=False):
        if sweep_report_path.is_file():
            import json as _json

            with open(sweep_report_path, encoding="utf-8") as fh:
                sweep_data = _json.load(fh)
            agg = sweep_data.get("aggregates") or {}
            st.caption(
                "Total **%d** | Correct **%d** (%.1f%%) — from `proofs/_diagnostics/sweep_report.json`"
                % (agg.get("total", 0), agg.get("correct", 0), agg.get("correct_pct", 0))
            )
            cat_rows = [
                {"category": k, "count": v}
                for k, v in sorted((agg.get("by_category") or {}).items())
            ]
            if cat_rows:
                st.dataframe(cat_rows, width="stretch")
            hotspots = agg.get("hotspots") or {}
            worst = (hotspots.get("techniques") or [])[:8]
            if worst:
                st.subheader("Worst techniques")
                st.dataframe(
                    [{"technique": h["key"], "issues": h["bad_count"], "breakdown": str(h["counts"])} for h in worst],
                    width="stretch",
                )
            worst_metrics = (hotspots.get("metrics") or [])[:8]
            if worst_metrics:
                st.subheader("Worst metrics")
                st.dataframe(
                    [{"metric": h["key"], "issues": h["bad_count"], "breakdown": str(h["counts"])} for h in worst_metrics],
                    width="stretch",
                )
            md_path = ROOT / "proofs" / "_diagnostics" / "sweep_summary.md"
            if md_path.is_file():
                st.caption("Summary: `%s`" % md_path)
        else:
            st.info(
                "No sweep report yet. Run: `py -3 scripts/run_all_tools_sweep.py --resume --skip-existing` "
                "to generate the full matrix, execute all tools, and build diagnostics."
            )

    isolated_default = os.environ.get("LOCAL_TOOL_ISOLATED", "true").lower() in ("1", "true", "yes")
    run_isolated = st.checkbox(
        "Run in isolated session (persistent env by default)",
        value=isolated_default,
        help="Uses a persistent validated venv under .tool_env/ (reused across runs). "
        "Uncheck to run tools in the current Python environment without worker isolation.",
    )
    preview = _local_tool_preview(available)
    if preview:
        st.subheader("Metric → tool mapping (in scope)")
        st.dataframe(preview, width="stretch")

    selected = st.multiselect(
        "Branches to run locally",
        available,
        default=default_pick,
        help="Prefers locally generated copies; GitHub is used only when a local copy is missing.",
    )
    if not selected:
        st.warning("Select at least one branch.")
        return

    st.code(", ".join(selected), language=None)

    if st.button("Install tools + run locally", type="primary", width="stretch"):
        st.session_state["last_whitebox_branches"] = selected
        with RunPanel("Local tool execution") as panel:
            try:
                with panel.stdout_redirect():
                    results = collect_local_batch(
                        selected,
                        install=True,
                        root=str(ROOT),
                        progress_callback=panel.progress,
                        require_whitebox=False,
                        isolated=run_isolated,
                        github_config=_github_push_config() if _github_creds_ready() else None,
                        local_root=work_root,
                        language=filters["language"],
                    )
            except Exception as exc:
                panel.set_result("error", "failed")
                st.error(_friendly_run_error(exc))
                st.session_state["last_local_log"] = panel.log_lines
                return
            st.session_state["last_local_run"] = results
            st.session_state["last_local_log"] = panel.log_lines
            st.dataframe(
                [{
                    "branch": r["branch_name"],
                    "branch_type": (r.get("local_report") or {}).get("branch_type", ""),
                    "status": r.get("status"),
                    "primary_tool": r.get("tool", ""),
                    "executed_tool": r.get("executed_tool", ""),
                    "real_tool": r.get("real_tool"),
                    "tool_outcome": ((r.get("local_report") or {}).get("extra") or {}).get("tool_outcome", "—"),
                    "assert_status": ((r.get("local_report") or {}).get("extra") or {}).get("assert_status", "—"),
                    "failure_layer": _local_failure_layer(r.get("local_report") or {}) or "—",
                    "local_status": (r.get("local_report") or {}).get("status"),
                    "summary": (r.get("local_report") or {}).get("raw_summary", ""),
                    "install_failed": ", ".join(r.get("install_failed") or []),
                    "report": r.get("report_path") or (r.get("local_report") or {}).get("_path") or "",
                } for r in results],
                width="stretch",
            )
            for r in results:
                log = r.get("tool_log") or r.get("tool_stderr") or ""
                install_msg = r.get("install_msg") or ""
                report_path = r.get("report_path") or ""
                local_report = r.get("local_report") or {}
                extra = local_report.get("extra") or {}
                branch_type = local_report.get("branch_type") or ""
                tool_outcome = extra.get("tool_outcome", "")
                assert_status = extra.get("assert_status", "")
                status = r.get("status", "")
                if status in ("ERROR", "UNAVAILABLE") or r.get("real_tool") is False:
                    st.error(
                        "%s — %s (executed: %s, real: %s)"
                        % (r["branch_name"], status, r.get("executed_tool") or "none", r.get("real_tool"))
                    )
                    stderr = r.get("tool_stderr") or ""
                    if stderr:
                        st.code(stderr[:2000], language=None)
                elif _local_run_success(branch_type, tool_outcome, assert_status):
                    st.success(
                        "%s — branch contract satisfied (%s tool_outcome=%s, assert=%s)"
                        % (r["branch_name"], branch_type, _normalize_outcome(tool_outcome), assert_status)
                    )
                elif assert_status == "PASS" and str(local_report.get("status", "")).upper() != _normalize_outcome(tool_outcome):
                    st.warning(
                        "%s — status/tool_outcome mismatch (status=%s, tool_outcome=%s)"
                        % (r["branch_name"], local_report.get("status"), tool_outcome)
                    )
                elif status == "FAIL" or assert_status == "FAIL":
                    layer = _local_failure_layer(local_report) or "unknown"
                    st.warning(
                        "%s — assert failed (layer=%s, executed: %s)"
                        % (r["branch_name"], layer, r.get("executed_tool") or "none")
                    )
                if log or install_msg or report_path or local_report:
                    with st.expander("Report — %s" % r["branch_name"]):
                        if install_msg:
                            st.caption("Install: %s" % install_msg)
                        if r.get("install_failed"):
                            st.caption("Install failed: %s" % ", ".join(r.get("install_failed")))
                        if report_path:
                            st.caption("Stored: `%s`" % report_path)
                        if local_report:
                            _render_local_report(local_report)
                        elif log:
                            st.code(log, language=None)
            comparable = [
                r["branch_name"] for r in results
                if (r.get("local_report") or {}).get("status") in ("PASS", "FAIL", "WARN")
            ]
            if comparable:
                comparisons = []
                for bname in comparable:
                    try:
                        comparisons.append(collect_comparison_proof(bname, root=str(ROOT)))
                    except Exception as exc:
                        comparisons.append({
                            "branch_name": bname,
                            "verdict": "ERROR",
                            "summary": str(exc),
                        })
                st.session_state["last_comparisons"] = comparisons
                cmp_summary = summarize_comparisons(comparisons)
                st.info(
                    "Auto-compared %d branch(es): MATCH=%d PARTIAL=%d MISMATCH=%d — see Compare tab"
                    % (
                        len(comparisons),
                        cmp_summary["match"],
                        cmp_summary.get("partial", 0),
                        cmp_summary["mismatch"],
                    )
                )
            panel.set_result("complete", "complete")
        st.toast("Local tool run finished", icon="✅")

    if st.session_state.get("last_local_run"):
        st.subheader("Last local run")
        for r in st.session_state["last_local_run"]:
            local_report = r.get("local_report") or {}
            if local_report and Path(
                r.get("report_path") or local_report.get("_path") or ""
            ).is_file() or local_report:
                with st.expander("Local execution report — %s" % r.get("branch_name", "?")):
                    _render_local_report(local_report)
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
            try:
                with panel.stdout_redirect():
                    results = collect_sonar_batch(
                        selected,
                        root=str(ROOT),
                        progress_callback=panel.progress,
                        require_whitebox=False,
                        github_config=_github_push_config(),
                    )
            except Exception as exc:
                panel.set_result("error", "failed")
                st.error(_friendly_run_error(exc))
                st.session_state["last_sonar_log"] = panel.log_lines
                return
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
    st.header("5 — Compare S3 / local / sonar (taxonomy reference)")
    branches = filters["summary"]["branches"]
    wb = whitebox_completion(branches, root=str(ROOT))
    completed = [b for b in branches if wb.get(b, {}).get("status") == "COMPLETED"]
    if not completed:
        st.info("No whitebox-completed branches. Run Page 2 first.")
        return

    readiness = compare_readiness(completed, root=str(ROOT))
    st.subheader("Report readiness")
    st.caption(
        "Comparison verdict uses **S3 vs local vs SonarQube**. Taxonomy is reference-only "
        "(cross-check: does S3 agree with taxonomy?). SonarQube and S3 may be N/A."
    )
    st.dataframe(
        [{
            "branch": r["branch_name"],
            "taxonomy_ref": r.get("taxonomy_label", r["taxonomy"]),
            "s3": r.get("s3_label", r["s3"]),
            "local": r.get("local_label", r["local"]),
            "sonar": r.get("sonar_label", r.get("sonar", False)),
            "can_compare": r.get("can_compare", False),
            "all_four": r["ready"],
            "missing": ", ".join(r["missing"]) if r["missing"] else "",
        } for r in readiness],
        width="stretch",
    )

    can_compare_any = any(r.get("can_compare") for r in readiness)
    not_comparable = [r for r in readiness if not r.get("can_compare")]
    if not_comparable:
        st.info(
            "Some branches need at least S3 or local report before comparison. Missing: "
            + "; ".join(
                "%s: %s" % (r["branch_name"], ", ".join(r["missing"]))
                for r in not_comparable
            )
        )

    if st.button(
        "Run comparison",
        type="primary",
        width="stretch",
        disabled=not can_compare_any,
    ):
        with RunPanel("Comparison") as panel:
            results = []
            comparable = [r["branch_name"] for r in readiness if r.get("can_compare")]
            for idx, bname in enumerate(comparable, 1):
                panel.progress("compare", idx - 1, len(comparable), bname, "")
                try:
                    results.append(collect_comparison_proof(bname, root=str(ROOT)))
                except Exception as exc:
                    results.append({
                        "branch_name": bname,
                        "verdict": "ERROR",
                        "summary": str(exc),
                    })
                panel.progress("compare", idx, len(comparable), bname, results[-1].get("verdict", ""))
            st.session_state["last_comparisons"] = results
            summary = summarize_comparisons(results)
            st.success(
                "MATCH=%d PARTIAL=%d MISMATCH=%d INCOMPLETE=%d"
                % (summary["match"], summary.get("partial", 0), summary["mismatch"], summary["incomplete"])
            )
        st.toast("Comparison done", icon="✅")

    st.subheader("Reports & comparison")
    h1, h2, h3, h4 = st.columns([4, 2, 2, 2])
    h1.markdown("**Branch**")
    h2.markdown("**S3 report**")
    h3.markdown("**Local report**")
    h4.markdown("**SonarQube**")

    readiness_by = {row["branch_name"]: row for row in readiness}
    for bname in completed:
        bundle = load_proof_bundle(bname, root=str(ROOT)) or {}
        row = readiness_by.get(bname, {})
        c1, c2, c3, c4 = st.columns([4, 2, 2, 2])
        with c1:
            st.write(bname)
        safe = bname.replace("/", "_")
        _report_download(
            c2,
            "Download S3",
            _report_path(bundle, "s3_report", "s3_report.json"),
            "%s_s3.json" % safe,
            _streamlit_key("dl_s3", bname),
        )
        with c3:
            _report_download(
                c3,
                "Download local",
                _report_path(bundle, "local_report", "local_report.json"),
                "%s_local.json" % safe,
                _streamlit_key("dl_local", bname),
            )
            local_report = bundle.get("local_report")
            if local_report:
                with st.expander("View local report"):
                    _render_local_report(local_report)
        sonar_path = _report_path(bundle, "sonar_report", "sonar_report.json")
        if sonar_path and Path(sonar_path).is_file():
            _report_download(
                c4,
                "Download SonarQube",
                sonar_path,
                "%s_sonar.json" % safe,
                _streamlit_key("dl_sonar", bname),
            )
        else:
            c4.caption("not run / Docker required")

        comparison = _load_branch_comparison(bname, bundle, row)
        with st.expander("Compare — %s" % bname, expanded=False):
            _render_detailed_comparison(comparison)
            comp_path = _report_path(bundle, "comparison", "comparison.json")
            if comp_path and Path(comp_path).is_file():
                st.download_button(
                    "Download comparison JSON",
                    data=Path(comp_path).read_bytes(),
                    file_name="%s_comparison.json" % safe,
                    mime="application/json",
                    key=_streamlit_key("dl_cmp", bname),
                )
        tax_path = _report_path(bundle, "taxonomy_report", "taxonomy_report.json")
        if tax_path and Path(tax_path).is_file():
            st.caption("Taxonomy reference: `%s`" % tax_path)

        raw_reports = [
            ("Local", bundle.get("local_report")),
            ("S3", bundle.get("s3_report")),
            ("SonarQube", bundle.get("sonar_report")),
        ]
        if any(rep for _, rep in raw_reports):
            with st.expander("Raw data — %s" % bname):
                for raw_label, raw_report in raw_reports:
                    if raw_report:
                        _render_raw_report(raw_label, raw_report)

    st.subheader("Overall comparison summary")
    comparison_results = _comparison_results_for_branches(completed)
    if not comparison_results:
        st.info(
            "No comparison results yet. Run comparison when S3 or local reports exist, "
            "or open a branch Compare expander to generate on demand."
        )
        return

    summary = summarize_comparisons(comparison_results)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("MATCH", summary["match"])
    m2.metric("PARTIAL", summary.get("partial", 0))
    m3.metric("MISMATCH", summary["mismatch"])
    m4.metric("INCOMPLETE", summary["incomplete"])
    st.dataframe(
        [{
            "branch": row.get("branch_name", "?"),
            "verdict": row.get("verdict", "?"),
            "taxonomy_vs_s3": row.get("taxonomy_vs_s3", "—"),
            "taxonomy_vs_local": row.get("taxonomy_vs_local", "—"),
            "s3_vs_local": (row.get("s3_vs_local") or {}).get("verdict", "—"),
            "local_vs_sonar": (row.get("local_vs_sonar") or {}).get("verdict", "—"),
            "summary": row.get("summary", ""),
        } for row in comparison_results],
        width="stretch",
    )
    try:
        xlsx_bytes = build_comparison_workbook(comparison_results, whitebox_by_branch=wb)
        st.download_button(
            "Download comparison (Excel)",
            data=xlsx_bytes,
            file_name="comparison_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="dl_comparison_xlsx",
        )
    except Exception as exc:
        st.warning("Excel export unavailable: %s" % exc)


def main():
    load_env(str(ROOT / ".env.local"))
    _handle_oauth_callback()
    if st.session_state.get("qa_login_ok"):
        _bind_app_user(st.session_state.get("qa_email_saved", ""))
    elif st.session_state.get("_bound_app_user"):
        _bind_app_user(st.session_state.get("_bound_app_user", ""))
    _sync_github_session_from_db()
    _sync_repo_artifacts()
    if st.session_state.get("repo_switch_notice"):
        st.info(st.session_state.pop("repo_switch_notice"))
    if st.session_state.pop("github_disconnect_notice", None):
        st.success("GitHub disconnected. Connect again when ready.")

    if st.session_state.get("scm_view") in ("callback", "repos"):
        st.sidebar.image(str(LOGO), width=120)
        _sidebar_user_login(str(ROOT / ".env.local"))
        _render_scm_flow()
        return

    filters = _sidebar_filters()
    tab = st.radio(
        "Pipeline stage",
        ["Branches", "Whitebox", "Local tools", "SonarQube", "Compare"],
        horizontal=True,
        label_visibility="collapsed",
        key="main_pipeline_tab",
    )
    if tab == "Branches":
        _tab_branches(filters)
    elif tab == "Whitebox":
        _tab_whitebox(filters)
    elif tab == "Local tools":
        _tab_local_tools(filters)
    elif tab == "SonarQube":
        _tab_sonar(filters)
    else:
        _tab_comparison(filters)


if __name__ == "__main__":
    main()
