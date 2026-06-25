"""Background S3 report sync for whitebox-completed branches."""

from __future__ import print_function

import os
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

_LOCK = threading.Lock()
_WORKERS = {}


def _enabled():
    return str(os.environ.get("REPORT_SYNC_ENABLED", "1")).strip().lower() not in (
        "0", "false", "no", "off",
    )


def _interval_sec():
    return max(30, int(os.environ.get("REPORT_SYNC_INTERVAL_SEC", "120")))


def _max_per_tick():
    return max(1, int(os.environ.get("REPORT_SYNC_MAX_PER_TICK", "25")))


def _branches_needing_sync(scope_branches, root):
    from lib.proofs import whitebox_completion, WHITEBOX_DONE_STATUSES
    from lib.report_schema import find_s3_report_path

    repo_root = Path(root or ROOT)
    wb = whitebox_completion(scope_branches, root=str(repo_root))
    dl_root = os.environ.get("S3_DOWNLOAD_ROOT", str(repo_root / "s3_downloads"))
    pending = []
    for bname in scope_branches:
        info = wb.get(bname, {})
        if info.get("status") not in WHITEBOX_DONE_STATUSES:
            continue
        if not info.get("expects_s3", True):
            continue
        meta = info.get("meta") or {}
        commit_sha = info.get("commit_sha") or meta.get("commit_sha", "")
        run_id = info.get("run_id") or meta.get("run_id", "")
        if not commit_sha or not run_id:
            continue
        existing = find_s3_report_path(dl_root, bname, commit_sha, run_id)
        if existing and Path(existing).is_dir() and any(Path(existing).iterdir()):
            continue
        proof_s3 = repo_root / "proofs"
        from lib.metrics import infer_from_branch_name

        tech, _, _, _ = infer_from_branch_name(bname)
        if tech:
            s3_report = repo_root / "proofs" / tech / bname / "s3_report.json"
            if s3_report.is_file():
                continue
        pending.append(bname)
    return pending


def _sync_tick(state):
    from lib.proofs import collect_s3_proof

    scope = list(state.get("scope_branches") or [])
    if not scope:
        state["pending_count"] = 0
        return

    pending = _branches_needing_sync(scope, state.get("root") or ROOT)
    state["pending_count"] = len(pending)
    if not pending:
        return

    limit = state.get("max_per_tick") or _max_per_tick()
    synced = 0
    for bname in pending[:limit]:
        try:
            collect_s3_proof(bname, root=state.get("root") or ROOT)
            synced += 1
        except Exception as exc:
            state["last_error"] = "%s: %s" % (bname, exc)
    state["synced_count"] = int(state.get("synced_count") or 0) + synced
    state["last_tick_ts"] = time.time()


def _worker_loop(app_user):
    while True:
        with _LOCK:
            state = _WORKERS.get(app_user)
            if not state or not state.get("running"):
                break
            state["trigger_now"] = False
            interval = state.get("interval_sec") or _interval_sec()
        try:
            _sync_tick(state)
        except Exception as exc:
            with _LOCK:
                if app_user in _WORKERS:
                    _WORKERS[app_user]["last_error"] = str(exc)
        deadline = time.time() + interval
        while time.time() < deadline:
            with _LOCK:
                st = _WORKERS.get(app_user)
                if not st or not st.get("running"):
                    return
                if st.get("trigger_now"):
                    break
            time.sleep(0.5)


def start(app_user, root=None, scope_branches=None, interval_sec=None, max_per_tick=None):
    """Start or refresh the background sync worker for *app_user*."""
    if not _enabled():
        return
    app_user = (app_user or "").strip()
    if not app_user:
        return

    scope = list(scope_branches or [])
    with _LOCK:
        state = _WORKERS.get(app_user)
        if state is None:
            state = {
                "running": True,
                "root": str(root or ROOT),
                "scope_branches": scope,
                "interval_sec": interval_sec or _interval_sec(),
                "max_per_tick": max_per_tick or _max_per_tick(),
                "last_tick_ts": 0.0,
                "last_error": "",
                "synced_count": 0,
                "pending_count": 0,
                "trigger_now": False,
                "thread": None,
            }
            _WORKERS[app_user] = state
            thread = threading.Thread(
                target=_worker_loop,
                args=(app_user,),
                name="report-sync-%s" % app_user[:24],
                daemon=True,
            )
            state["thread"] = thread
            thread.start()
        else:
            state["running"] = True
            state["root"] = str(root or ROOT)
            state["scope_branches"] = scope
            if interval_sec is not None:
                state["interval_sec"] = interval_sec
            if max_per_tick is not None:
                state["max_per_tick"] = max_per_tick
            if not state.get("thread") or not state["thread"].is_alive():
                thread = threading.Thread(
                    target=_worker_loop,
                    args=(app_user,),
                    name="report-sync-%s" % app_user[:24],
                    daemon=True,
                )
                state["thread"] = thread
                thread.start()


def stop(app_user):
    app_user = (app_user or "").strip()
    with _LOCK:
        state = _WORKERS.pop(app_user, None)
        if state:
            state["running"] = False


def trigger_now(app_user):
    app_user = (app_user or "").strip()
    with _LOCK:
        state = _WORKERS.get(app_user)
        if state:
            state["trigger_now"] = True


def status(app_user):
    app_user = (app_user or "").strip()
    with _LOCK:
        state = _WORKERS.get(app_user)
        if not state:
            return {
                "running": False,
                "last_tick_ts": 0.0,
                "last_error": "",
                "synced_count": 0,
                "pending_count": 0,
            }
        return {
            "running": bool(state.get("running")),
            "last_tick_ts": float(state.get("last_tick_ts") or 0.0),
            "last_error": state.get("last_error") or "",
            "synced_count": int(state.get("synced_count") or 0),
            "pending_count": int(state.get("pending_count") or 0),
        }
