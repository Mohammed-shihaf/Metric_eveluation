"""Per-branch generate -> validate (fix-until-pass) -> push pipeline."""

from __future__ import print_function

import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

from lib.branch_asserts import assert_branch_full
from lib.branch_post_verify import verify_generated_branch
from lib.github_api import fetch_branch_source, push_branch_to_github, read_remote_text
from lib.github_auth import check_app_repo_access, _token_kind
from lib.lang_generators.base import effective_strength
from lib.lang_support import branch_language, default_runtime, normalize_language, normalize_runtime
from lib.lang_generators import write_branch
from lib.python_generator import generate_branch_files, read_gen_meta
from lib.registry import iter_branches, package_name
from lib.tool_map import metric_tool, pip_packages_for_family, pip_packages_for_primary
from lib.lang_tool_runners import packages_for_language


STALL_ROUNDS_LIMIT = 3


def _branch_language(branch_dir, language=None):
    return branch_language(branch_dir, fallback=language or "python")


def _branch_runtime(branch_dir, language=None, runtime=None):
    if runtime:
        lang = normalize_language(language or _branch_language(branch_dir))
        return normalize_runtime(lang, runtime)
    meta = read_gen_meta(branch_dir)
    lang = normalize_language(language or meta.get("language") or "python")
    return normalize_runtime(lang, meta.get("runtime") or default_runtime(lang))


def branch_materialized(branch_dir, technique_code, language=None):
    """True when a branch directory contains generated source (not just .git metadata)."""
    branch_dir = os.path.abspath(branch_dir or "")
    if not branch_dir or not os.path.isdir(branch_dir):
        return False
    lang = _branch_language(branch_dir, language)
    pkg = package_name(technique_code)
    paths = {
        "python": os.path.join(branch_dir, pkg, "config.py"),
        "java": os.path.join(branch_dir, "src/main/java/com/testable/%s/Config.java" % pkg.lower()),
        "javascript": os.path.join(branch_dir, pkg.lower(), "config.js"),
        "typescript": os.path.join(branch_dir, pkg.lower(), "config.ts"),
        "csharp": os.path.join(branch_dir, "src", pkg, "Config.cs"),
    }
    return os.path.isfile(paths.get(lang) or paths["python"])


def strip_incomplete_branch_dir(branch_dir):
    """Remove empty or git-only branch folders so fetch/generate can repopulate them."""
    branch_dir = os.path.abspath(branch_dir or "")
    if not branch_dir or not os.path.isdir(branch_dir):
        return False
    if branch_materialized(branch_dir, _technique_from_dir(branch_dir)):
        return False
    shutil.rmtree(branch_dir, ignore_errors=True)
    return True


def _technique_from_dir(branch_dir):
    """Best-effort technique code from a branch folder name."""
    from lib.metrics import parse_branch_name

    folder = os.path.basename(os.path.normpath(branch_dir))
    parsed = parse_branch_name(folder)
    return (parsed or {}).get("tech") or folder.split("_", 1)[0]


def _deadline_passed(deadline):
    return deadline is not None and time.time() >= deadline


def _user_work_key(app_user):
    email = (app_user or "").strip().lower()
    if not email:
        return "default"
    return hashlib.sha256(email.encode("utf-8")).hexdigest()[:16]


def pipeline_work_dir(repo_root, app_user=None):
    root = os.path.abspath(repo_root)
    key = _user_work_key(app_user)
    path = os.path.join(root, ".pipeline_work", key)
    os.makedirs(path, exist_ok=True)
    return path


def hydrate_gen_rows_from_work(work_root, techniques, metrics, types, version):
    """Rebuild gen_rows from on-disk branch dirs (survives Streamlit reruns)."""
    work_root = os.path.abspath(work_root)
    if not os.path.isdir(work_root):
        return []
    rows = []
    for tech, metric, bt, bname in iter_branches(techniques, metrics, types, version):
        branch_dir = os.path.join(work_root, bname)
        if not os.path.isdir(branch_dir):
            continue
        materialized = branch_materialized(branch_dir, tech)
        meta = read_gen_meta(branch_dir) if materialized else {}
        rows.append({
            "branch_name": bname,
            "technique_code": tech,
            "metric_code": metric,
            "branch_type": bt,
            "dir": branch_dir,
            "generated": materialized,
            "error": "" if materialized else "incomplete local copy (missing source files)",
            "strength": meta.get("strength", 0),
            "loc": meta.get("loc"),
        })
    return rows


def remote_branch_strength(github_config, branch_name):
    """Return the strength level recorded on a remote branch, or 0 if unknown."""
    if not github_config or not github_config.get("token") or not github_config.get("repo_slug"):
        return 0
    text = read_remote_text(
        github_config["token"],
        github_config["repo_slug"],
        branch_name,
        ".gen_meta.json",
    )
    if not text:
        return 0
    try:
        meta = json.loads(text)
        return int(meta.get("strength", 0))
    except (ValueError, TypeError, json.JSONDecodeError):
        return 0


def local_branch_strength(work_root, branch_name):
    """Return strength from a local work copy, or 0 if missing."""
    branch_dir = os.path.join(os.path.abspath(work_root), branch_name)
    if not os.path.isdir(branch_dir):
        return 0
    meta = read_gen_meta(branch_dir)
    try:
        return max(0, int(meta.get("strength", 0) or 0))
    except (TypeError, ValueError):
        return 0


def next_regen_strength(local_s, remote_s, session_s=0, exists=False):
    """Single source for the next write strength (display + generate)."""
    try:
        local_s = max(0, int(local_s or 0))
        remote_s = max(0, int(remote_s or 0))
        session_s = max(0, int(session_s or 0))
    except (TypeError, ValueError):
        local_s = remote_s = session_s = 0
    if not exists and local_s <= 0 and remote_s <= 0 and session_s <= 0:
        return 0
    current = max(local_s, remote_s, session_s)
    if current <= 0:
        return 1
    return current + 1


def build_regeneration_strength_map(
    work_root,
    branch_names,
    github_config=None,
    push_rows=None,
    gen_rows=None,
):
    """Next generate strength: max(local, remote, session) + 1 when the branch already exists."""
    push_by = {}
    for row in push_rows or []:
        if row.get("branch"):
            push_by[row["branch"]] = row
    session_by = {}
    for row in gen_rows or []:
        bname = (row.get("branch_name") or "").strip()
        if not bname:
            continue
        try:
            session_by[bname] = max(0, int(row.get("strength") or 0))
        except (TypeError, ValueError):
            session_by[bname] = 0
    out = {}
    work_root = os.path.abspath(work_root)
    for bname in branch_names:
        local_s = local_branch_strength(work_root, bname)
        remote_s = 0
        on_github = push_by.get(bname, {}).get("on_github") == "yes"
        if github_config and on_github:
            remote_s = remote_branch_strength(github_config, bname)
        exists = local_s > 0 or remote_s > 0 or os.path.isdir(
            os.path.join(work_root, bname)
        ) or on_github
        session_s = session_by.get(bname, 0)
        out[bname] = next_regen_strength(local_s, remote_s, session_s, exists=exists)
    return out


def sync_gen_rows_strength_from_work(gen_rows, work_root):
    """Refresh gen_rows strength/loc from on-disk .gen_meta.json."""
    work_root = os.path.abspath(work_root)
    for row in gen_rows or []:
        bname = row.get("branch_name")
        branch_dir = row.get("dir") or os.path.join(work_root, bname or "")
        if bname and os.path.isdir(branch_dir):
            meta = read_gen_meta(branch_dir)
            row["strength"] = meta.get("strength", row.get("strength", 0))
            row["loc"] = meta.get("loc", row.get("loc"))
    return gen_rows


def _empty_score_history_entry():
    return {
        "prev_strength": None,
        "prev_score": None,
        "cur_strength": None,
        "cur_score": None,
        "regenerated": False,
    }


def snapshot_previous_scores(
    history,
    regenerated_branches,
    last_strength_by_branch=None,
    last_score_by_branch=None,
):
    """Snapshot prior gen strength and validation score before regenerating branches."""
    history = dict(history or {})
    last_strength_by_branch = last_strength_by_branch or {}
    last_score_by_branch = last_score_by_branch or {}
    for bname in regenerated_branches or []:
        entry = dict(history.get(bname) or _empty_score_history_entry())
        prev_strength = entry.get("cur_strength")
        if prev_strength is None:
            prev_strength = last_strength_by_branch.get(bname)
        prev_score = entry.get("cur_score")
        if prev_score is None:
            prev_score = last_score_by_branch.get(bname)
        entry["prev_strength"] = prev_strength
        entry["prev_score"] = prev_score
        entry["cur_strength"] = None
        entry["cur_score"] = None
        entry["regenerated"] = True
        history[bname] = entry
    return history


def update_regenerated_strength(history, gen_rows):
    """Set cur_strength on regenerated branches from fresh generate rows."""
    history = dict(history or {})
    for row in gen_rows or []:
        bname = (row.get("branch_name") or "").strip()
        if not bname:
            continue
        entry = history.get(bname)
        if not entry or not entry.get("regenerated"):
            continue
        try:
            entry["cur_strength"] = max(0, int(row.get("strength") or 0))
        except (TypeError, ValueError):
            entry["cur_strength"] = 0
        history[bname] = entry
    return history


def apply_current_scores(history, validate_rows):
    """Fill cur_score (and cur_strength when present) from validation rows."""
    history = dict(history or {})
    for row in validate_rows or []:
        bname = (row.get("branch_name") or "").strip()
        if not bname:
            continue
        entry = dict(history.get(bname) or _empty_score_history_entry())
        if row.get("strength_score") is not None:
            try:
                entry["cur_score"] = float(row.get("strength_score"))
            except (TypeError, ValueError):
                pass
        if row.get("strength") is not None:
            try:
                entry["cur_strength"] = max(0, int(row.get("strength") or 0))
            except (TypeError, ValueError):
                pass
        history[bname] = entry
    return history


def ensure_local_branches(
    work_root,
    github_config,
    techniques,
    metrics,
    types,
    version,
    push_rows=None,
):
    """Fetch in-scope branches from GitHub into *work_root* when missing locally.

    Returns ``(gen_rows, materialized, errors)`` where *materialized* lists branch
    names downloaded from the remote repo and *errors* lists ``(branch, message)``
    pairs for fetch failures.
    """
    work_root = os.path.abspath(work_root)
    os.makedirs(work_root, exist_ok=True)

    push_by = {}
    for row in push_rows or []:
        if row.get("branch"):
            push_by[row["branch"]] = row

    token = (github_config or {}).get("token", "").strip()
    repo_slug = (github_config or {}).get("repo_slug", "").strip()
    materialized = []
    errors = []

    for tech, metric, bt, bname in iter_branches(techniques, metrics, types, version):
        branch_dir = os.path.join(work_root, bname)
        if os.path.isdir(branch_dir):
            if branch_materialized(branch_dir, tech):
                continue
            strip_incomplete_branch_dir(branch_dir)
        on_github = push_by.get(bname, {}).get("on_github") == "yes"
        if not on_github:
            continue
        if not token or not repo_slug:
            errors.append((bname, "GitHub credentials missing — cannot fetch remote branch"))
            continue
        try:
            fetch_branch_source(token, repo_slug, bname, branch_dir)
            materialized.append(bname)
        except Exception as exc:
            errors.append((bname, str(exc)))

    gen_rows = hydrate_gen_rows_from_work(work_root, techniques, metrics, types, version)
    return gen_rows, materialized, errors


def _failure_detail(assert_row):
    if not assert_row:
        return "validation failed"
    parts = []
    for key in ("structure", "tool_support", "metric_behavior"):
        if assert_row.get(key) not in ("PASS",):
            parts.append("%s=%s" % (key, assert_row.get(key)))
    if assert_row.get("strength_score") is not None:
        parts.append("strength=%.1f" % assert_row.get("strength_score"))
    for msg in assert_row.get("messages") or []:
        parts.append(msg)
    return "; ".join(parts) if parts else "overall=%s" % assert_row.get("overall")


def _result_row(bname, tech, metric, bt, attempts, assert_row, pushed, failure="", branch_dir=""):
    row = {
        "branch_name": bname,
        "technique_code": tech,
        "metric_code": metric,
        "branch_type": bt,
        "attempts": attempts,
        "pushed": pushed,
        "failure_reason": failure,
        "dir": branch_dir,
        "generated": bool(branch_dir and os.path.isdir(branch_dir)),
    }
    if assert_row:
        row.update({
            "structure": assert_row.get("structure"),
            "tool_support": assert_row.get("tool_support"),
            "metric_behavior": assert_row.get("metric_behavior"),
            "overall": assert_row.get("overall"),
            "strength_score": assert_row.get("strength_score"),
            "expected_threshold": assert_row.get("expected_threshold"),
            "strength_pass": assert_row.get("strength_pass"),
            "messages": "; ".join(assert_row.get("messages") or []),
        })
    else:
        row.update({
            "structure": "—",
            "tool_support": "—",
            "metric_behavior": "—",
            "overall": "FAIL",
            "strength_score": None,
            "expected_threshold": "",
            "strength_pass": False,
            "messages": failure,
        })
    return row


def _install_packages(packages):
    if not packages:
        return False, "no packages to install"
    cmd = [sys.executable, "-m", "pip", "install", "-q"] + list(packages)
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300, check=False)
        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout or "pip install failed").strip()
            return False, detail[:500]
        return True, "installed: %s" % ",".join(packages)
    except Exception as exc:
        return False, str(exc)


def _fix_branch(tech, metric, bt, version, language, branch_path, auto_install, strength=0, runtime=None):
    """Regenerate one branch with escalating strength and optionally install tools."""
    rt = _branch_runtime(branch_path, language, runtime)
    write_branch(branch_path, tech, metric, bt, version, language, strength=strength, runtime=rt)
    notes = ["regenerated strength=%d" % strength]
    if not auto_install:
        return "; ".join(notes)

    info = metric_tool(tech, metric, language)
    family = info["family"]
    if family == "unknown":
        return "; ".join(notes)

    pkgs = packages_for_language(family, info["primary"], language)
    if not pkgs and (language or "python").lower() == "python":
        pkgs = pip_packages_for_primary(info.get("primary", ""), family, tech)
    if not pkgs:
        pkgs = pip_packages_for_family(family, info["primary"])
    if (language or "python").lower() == "python":
        ok, msg = _install_packages(pkgs)
        notes.append(msg if ok else "install failed: %s" % msg)
    else:
        notes.append("lang=%s tools=%s" % (language, ",".join(pkgs) or "structural"))
    return "; ".join(notes)


def generate_branches(
    techniques,
    metrics,
    types,
    version,
    language,
    work_root,
    progress_callback=None,
    clear_existing=True,
    strength_map=None,
    deadline=None,
    branch_names_filter=None,
    max_fix_attempts=3,
    auto_install=True,
    runtime=None,
):
    """Write in-scope branches to work_root/<branch_name>."""
    work_root = os.path.abspath(work_root)
    planned = list(iter_branches(techniques, metrics, types, version))
    if branch_names_filter is not None:
        allow = set(branch_names_filter)
        planned = [item for item in planned if item[3] in allow]
    total = len(planned)
    branch_names = [bname for _, _, _, bname in planned]

    if strength_map is None:
        strength_map = build_regeneration_strength_map(work_root, branch_names)

    if clear_existing and branch_names_filter is None and os.path.isdir(work_root):
        shutil.rmtree(work_root, ignore_errors=True)
    os.makedirs(work_root, exist_ok=True)

    rows = []
    stopped_at = None
    stop_reason = None
    stop_cause = None

    lang = normalize_language(language)
    rt = normalize_runtime(lang, runtime or default_runtime(lang))

    for idx, (tech, metric, bt, bname) in enumerate(planned, start=1):
        if _deadline_passed(deadline):
            stop_cause = "time_budget"
            stop_reason = "Stage time budget reached before %s" % bname
            break

        branch_dir = os.path.join(work_root, bname)
        strength = 0
        if strength_map and bname in strength_map:
            try:
                strength = max(0, int(strength_map[bname]))
            except (TypeError, ValueError):
                strength = 0
        strength = effective_strength(strength)

        def _progress(step, msg):
            if progress_callback:
                progress_callback(step, idx - 1, total, bname, msg)

        _progress("generate", "writing branch files (strength=%d)" % strength)
        try:
            _bname, loc = write_branch(
                branch_dir, tech, metric, bt, version, lang, strength=strength, runtime=rt,
            )
            meta = read_gen_meta(branch_dir)
            _progress("verify", "structure, import, pytest")

            def _verify_cb(step, msg):
                _progress(step, msg)

            vr = verify_generated_branch(
                branch_dir, tech, metric, bt, version, lang,
                progress_callback=_verify_cb,
            )
            if not vr.get("ok") and max_fix_attempts:
                for attempt in range(1, int(max_fix_attempts) + 1):
                    fix_strength = strength + attempt
                    _progress(
                        "fix",
                        "verify failed, regenerating strength=%d (attempt %d/%d)"
                        % (fix_strength, attempt, int(max_fix_attempts)),
                    )
                    _fix_branch(
                        tech, metric, bt, version, lang, branch_dir,
                        auto_install, strength=fix_strength, runtime=rt,
                    )
                    meta = read_gen_meta(branch_dir)
                    strength = meta.get("strength", fix_strength)
                    vr = verify_generated_branch(
                        branch_dir, tech, metric, bt, version, lang,
                        progress_callback=_verify_cb,
                    )
                    if vr.get("ok"):
                        break
            if not vr.get("ok"):
                err = "verify failed: %s" % "; ".join(vr.get("messages") or ["unknown"])
                rows.append({
                    "branch_name": bname,
                    "technique_code": tech,
                    "metric_code": metric,
                    "branch_type": bt,
                    "dir": branch_dir,
                    "generated": False,
                    "error": err,
                    "strength": meta.get("strength", strength),
                    "loc": vr.get("loc") or meta.get("loc", loc),
                })
                if stopped_at is None:
                    stopped_at = bname
                    stop_reason = err
                _progress("verify", err[:120])
                continue
            verified_loc = vr.get("loc") or meta.get("loc", loc)
            rows.append({
                "branch_name": bname,
                "technique_code": tech,
                "metric_code": metric,
                "branch_type": bt,
                "dir": branch_dir,
                "generated": True,
                "error": "",
                "strength": meta.get("strength", strength),
                "loc": verified_loc,
                "language": lang,
                "runtime": meta.get("runtime") or rt,
            })
            _progress("verify", "strength=%d, %d LOC — %s" % (
                meta.get("strength", strength),
                verified_loc,
                (vr.get("messages") or [""])[-1],
            ))
        except Exception as exc:
            err = "generate failed: %s" % exc
            rows.append({
                "branch_name": bname,
                "technique_code": tech,
                "metric_code": metric,
                "branch_type": bt,
                "dir": branch_dir,
                "generated": False,
                "error": err,
                "strength": strength,
                "loc": None,
            })
            if stopped_at is None:
                stopped_at = bname
                stop_reason = err

    generated = [r for r in rows if r.get("generated")]
    generated_names = {r["branch_name"] for r in generated}
    remaining = [bname for _, _, _, bname in planned if bname not in generated_names]
    if total == 0:
        return {
            "rows": rows,
            "generated": generated,
            "stopped_at": None,
            "stop_reason": "No branches in scope",
            "success": False,
            "total": 0,
            "completed": [],
            "remaining": [],
            "stop_cause": "done",
        }
    if stop_cause is None:
        if len(generated_names) == total:
            stop_cause = "done"
        elif remaining:
            stop_cause = "errors"
        else:
            stop_cause = "done"
    return {
        "rows": rows,
        "generated": generated,
        "stopped_at": stopped_at,
        "stop_reason": stop_reason,
        "success": len(generated) == total,
        "total": total,
        "completed": sorted(generated_names),
        "remaining": remaining,
        "stop_cause": stop_cause,
    }


def validate_branches(
    gen_rows,
    version,
    language,
    max_fix_attempts=2,
    auto_install=True,
    progress_callback=None,
    block_strict=True,
    deadline=None,
):
    """Run assert validation with fix-until-pass loop per branch."""
    rows_in = []
    for r in (gen_rows or []):
        branch_dir = r.get("dir")
        if not branch_dir or not os.path.isdir(branch_dir):
            continue
        rows_in.append(r)
    total = len(rows_in)
    rows = []
    validated = []
    stopped_at = None
    stop_reason = None
    stop_cause = None

    if total == 0:
        return {
            "rows": rows,
            "validated": validated,
            "stopped_at": None,
            "stop_reason": "No generated branches to validate — run Generate first",
            "success": False,
            "total": 0,
            "completed": [],
            "remaining": [],
            "stop_cause": "done",
        }

    if auto_install and (language or "python").strip().lower() == "python":
        install_pkgs = []
        for gen in rows_in:
            info = metric_tool(gen["technique_code"], gen["metric_code"], language)
            pkgs = pip_packages_for_primary(
                info.get("primary", ""),
                info.get("family", ""),
                gen["technique_code"],
            )
            if not pkgs and (language or "python").strip().lower() != "python":
                pkgs = packages_for_language(info["family"], info.get("primary", ""), language)
            for pkg in pkgs:
                if pkg not in install_pkgs:
                    install_pkgs.append(pkg)
        if install_pkgs:
            if progress_callback:
                progress_callback(
                    "install",
                    0,
                    total,
                    "",
                    "installing tools: %s" % ",".join(install_pkgs),
                )
            ok, msg = _install_packages(install_pkgs)
            if progress_callback:
                progress_callback("install", 0, total, "", msg if ok else "install failed: %s" % msg)

    for idx, gen in enumerate(rows_in, start=1):
        if _deadline_passed(deadline):
            stop_cause = "time_budget"
            stop_reason = "Stage time budget reached before %s" % gen.get("branch_name")
            break

        tech = gen["technique_code"]
        metric = gen["metric_code"]
        bt = gen["branch_type"]
        bname = gen["branch_name"]
        branch_dir = gen["dir"]

        def _progress(step, msg):
            if progress_callback:
                progress_callback(step, idx - 1, total, bname, msg)

        attempts = 0
        try:
            base_strength = max(0, int(gen.get("strength") or 0))
        except (TypeError, ValueError):
            base_strength = 0
        if not branch_materialized(branch_dir, tech, language):
            _progress("fix", "repopulating incomplete branch directory")
            _fix_branch(tech, metric, bt, version, language, branch_dir, auto_install, strength=base_strength)

        assert_row = assert_branch_full(
            branch_dir, tech, metric, bt, version, language, require_real_tool=True,
        )
        _progress("assert", assert_row.get("overall", "?"))

        while assert_row.get("overall") == "FAIL" and attempts < max_fix_attempts:
            attempts += 1
            fix_strength = base_strength + attempts
            _progress("fix", "strength %d attempt %d/%d" % (fix_strength, attempts, max_fix_attempts))
            _fix_branch(tech, metric, bt, version, language, branch_dir, auto_install, strength=fix_strength)
            assert_row = assert_branch_full(
                branch_dir, tech, metric, bt, version, language, require_real_tool=True,
            )
            _progress("assert", assert_row.get("overall", "?"))

        overall = assert_row.get("overall")
        passed = overall == "PASS"
        if overall == "PASS" and assert_row.get("strength_pass") is False:
            passed = False
        if assert_row.get("metric_behavior") == "SKIPPED":
            passed = False
        if overall == "PARTIAL":
            passed = False

        row = _result_row(bname, tech, metric, bt, attempts + 1, assert_row, False, branch_dir=branch_dir)
        rows.append(row)

        if not passed:
            if stopped_at is None:
                stopped_at = bname
                stop_reason = _failure_detail(assert_row)
            _progress("validated", "needs fix: %s" % _failure_detail(assert_row))
            continue

        validated.append(bname)
        _progress("validated", "strength=%s" % assert_row.get("strength_score"))

    remaining = [g["branch_name"] for g in rows_in if g["branch_name"] not in validated]
    if stop_cause is None:
        stop_cause = "done" if len(validated) == total else "errors"
    return {
        "rows": rows,
        "validated": validated,
        "stopped_at": stopped_at,
        "stop_reason": stop_reason,
        "success": len(validated) == total,
        "total": total,
        "completed": list(validated),
        "remaining": remaining,
        "stop_cause": stop_cause,
    }


def _branch_strength_score(row):
    if not row:
        return 0.0
    try:
        return float(row.get("strength_score") or 0)
    except (TypeError, ValueError):
        return 0.0


def validate_with_regeneration(
    gen_rows,
    version,
    language,
    max_fix_attempts=2,
    auto_install=True,
    max_rounds=25,
    progress_callback=None,
    block_strict=True,
    deadline=None,
):
    """Validate branches; regenerate failed branches and re-validate until all pass or max_rounds."""
    result = validate_branches(
        gen_rows,
        version,
        language,
        max_fix_attempts=max_fix_attempts,
        auto_install=auto_install,
        progress_callback=progress_callback,
        block_strict=block_strict,
        deadline=deadline,
    )
    rows_by_branch = {r["branch_name"]: r for r in result.get("rows", [])}
    validated = set(result.get("validated") or [])
    total = result.get("total", 0)
    rounds_used = 0
    stop_cause = result.get("stop_cause")

    if total == 0:
        result["rounds_used"] = 0
        return result

    if result.get("stop_cause") == "time_budget":
        result["rounds_used"] = 0
        return result

    stalled = False
    stall_rounds = 0
    best_by_branch = {
        bname: _branch_strength_score(row)
        for bname, row in rows_by_branch.items()
        if bname not in validated
    }

    while len(validated) < total and rounds_used < max_rounds:
        if _deadline_passed(deadline):
            stop_cause = "time_budget"
            break
        rounds_used += 1
        failed_rows = [
            g for g in (gen_rows or [])
            if g.get("generated") and g.get("dir") and g["branch_name"] not in validated
        ]
        if not failed_rows:
            break
        n_failed = len(failed_rows)
        for idx, g in enumerate(failed_rows, start=1):
            if _deadline_passed(deadline):
                stop_cause = "time_budget"
                break
            bname = g["branch_name"]
            try:
                base_strength = max(0, int(g.get("strength") or 0))
            except (TypeError, ValueError):
                base_strength = 0
            new_strength = base_strength + 1
            if progress_callback:
                progress_callback(
                    "regenerate",
                    idx - 1,
                    n_failed,
                    bname,
                    "round %d strength=%d" % (rounds_used, new_strength),
                )
            write_branch(
                g["dir"],
                g["technique_code"],
                g["metric_code"],
                g["branch_type"],
                version,
                language,
                strength=new_strength,
                runtime=_branch_runtime(g["dir"], language),
            )
            meta = read_gen_meta(g["dir"])
            g["strength"] = meta.get("strength", new_strength)
            g["loc"] = meta.get("loc")

        if stop_cause == "time_budget":
            break

        sub = validate_branches(
            failed_rows,
            version,
            language,
            max_fix_attempts=max_fix_attempts,
            auto_install=auto_install,
            progress_callback=progress_callback,
            block_strict=block_strict,
            deadline=deadline,
        )
        if sub.get("stop_cause") == "time_budget":
            stop_cause = "time_budget"
        for r in sub.get("rows", []):
            rows_by_branch[r["branch_name"]] = r
        validated |= set(sub.get("validated") or [])

        still_failing = [b for b in best_by_branch if b not in validated]
        if not still_failing:
            break

        improved = False
        for bname in still_failing:
            score = _branch_strength_score(rows_by_branch.get(bname))
            prev = best_by_branch.get(bname, 0.0)
            if score > prev + 1e-6:
                improved = True
            best_by_branch[bname] = max(prev, score)

        if not improved:
            stall_rounds += 1
            if stall_rounds >= STALL_ROUNDS_LIMIT:
                stalled = True
                stop_cause = "stalled"
                break
        else:
            stall_rounds = 0

    if rounds_used >= max_rounds and len(validated) < total and stop_cause not in ("time_budget", "stalled"):
        stop_cause = "max_rounds"

    rows = list(rows_by_branch.values())
    stopped_at = next((r["branch_name"] for r in rows if r["branch_name"] not in validated), None)
    stop_reason = None
    if stopped_at:
        sr = rows_by_branch.get(stopped_at) or {}
        msgs = sr.get("messages") or ""
        if isinstance(msgs, str) and msgs:
            msg_list = [m.strip() for m in msgs.split(";") if m.strip()]
        else:
            msg_list = msgs if isinstance(msgs, list) else []
        stop_reason = _failure_detail({
            "structure": sr.get("structure"),
            "tool_support": sr.get("tool_support"),
            "metric_behavior": sr.get("metric_behavior"),
            "overall": sr.get("overall"),
            "strength_score": sr.get("strength_score"),
            "messages": msg_list,
        })
        if rounds_used:
            stop_reason = "%s (after %d regenerate round(s))" % (stop_reason, rounds_used)
        if stalled:
            stuck_score = _branch_strength_score(rows_by_branch.get(stopped_at))
            stop_reason = "%s; no improvement after %d round(s) - strength stuck at %.1f" % (
                stop_reason, rounds_used, stuck_score,
            )

    remaining = sorted(set(
        g["branch_name"] for g in (gen_rows or [])
        if g.get("generated") and g.get("dir")
    ) - validated)
    if stop_cause is None:
        stop_cause = "done" if len(validated) == total else "errors"

    return {
        "rows": rows,
        "validated": sorted(validated),
        "stopped_at": stopped_at,
        "stop_reason": stop_reason,
        "success": len(validated) == total and total > 0,
        "total": total,
        "rounds_used": rounds_used,
        "completed": sorted(validated),
        "remaining": remaining,
        "stop_cause": stop_cause,
    }


def push_branches(
    validated_rows,
    github_config,
    progress_callback=None,
    fallback_config=None,
    deadline=None,
):
    """Push validated branch directories to GitHub."""

    def _empty_result(reason, needs_install=False, total=0):
        return {
            "rows": [],
            "completed": [],
            "failed": [],
            "stopped_at": None,
            "stop_reason": reason,
            "success": False,
            "needs_install": needs_install,
            "total": total,
            "push_method": None,
            "used_fallback": False,
            "remaining": [],
            "stop_cause": "errors",
        }

    def _attempt(cfg, candidates=None):
        if not cfg or not cfg.get("token") or not cfg.get("repo_slug"):
            return _empty_result("GitHub not configured")

        token = cfg["token"]
        repo_slug = cfg["repo_slug"]
        base_branch = (cfg.get("default_branch") or "main").strip() or "main"
        push_login = cfg.get("login", "")
        push_method = cfg.get("push_method", "oauth")

        ok, needs_install, access_msg = check_app_repo_access(token, repo_slug)
        if not ok:
            return {
                "rows": [],
                "completed": [],
                "failed": [],
                "stopped_at": None,
                "stop_reason": access_msg,
                "success": False,
                "needs_install": needs_install,
                "total": 0,
                "push_method": push_method,
                "used_fallback": False,
                "remaining": [],
                "stop_cause": "errors",
            }

        default_candidates = [
            r for r in (validated_rows or [])
            if r.get("overall") in ("PASS", "PARTIAL") and r.get("dir") and os.path.isdir(r.get("dir"))
        ]
        cand = candidates if candidates is not None else default_candidates
        total = len(cand)
        rows = []
        completed = []
        failed = []
        stopped_at = None
        stop_reason = None
        stop_cause = None
        needs_install_flag = False

        for idx, row in enumerate(cand, start=1):
            if _deadline_passed(deadline):
                stop_cause = "time_budget"
                stop_reason = "Stage time budget reached before %s" % row.get("branch_name")
                break

            tech = row["technique_code"]
            metric = row["metric_code"]
            bt = row["branch_type"]
            bname = row["branch_name"]
            branch_dir = row["dir"]

            def _progress(step, msg):
                if progress_callback:
                    progress_callback(step, idx - 1, total, bname, msg)

            if not branch_materialized(branch_dir, tech):
                out = dict(row)
                out.update({
                    "pushed": False,
                    "failure_reason": "branch directory incomplete (missing source files); re-validate or regenerate",
                    "push_method": push_method,
                })
                rows.append(out)
                failed.append(bname)
                if stopped_at is None:
                    stopped_at = bname
                    stop_reason = out["failure_reason"]
                _progress("push", "skipped: incomplete branch dir")
                continue

            _progress("push", "pushing to GitHub")
            meta = read_gen_meta(branch_dir)
            gen_strength = int(meta.get("strength", 0) or 0)
            gen_version = (meta.get("version") or "2.6").strip() or "2.6"
            gen_language = normalize_language(meta.get("language") or "python")
            gen_runtime = _branch_runtime(branch_dir, gen_language, meta.get("runtime"))
            files = generate_branch_files(
                tech, metric, bt, gen_version, gen_language, strength=gen_strength, runtime=gen_runtime,
            )
            commit_sha, push_err, _method = push_branch_to_github(
                token,
                repo_slug,
                bname,
                files=files,
                source_dir=branch_dir,
                base=base_branch,
                message="Add %s codebase" % bname,
                login=push_login,
            )
            if push_err:
                out = dict(row)
                out.update({"pushed": False, "failure_reason": push_err, "push_method": push_method})
                rows.append(out)
                failed.append(bname)
                if stopped_at is None:
                    stopped_at = bname
                    stop_reason = push_err
                if (
                    _token_kind(token) == "github-app-user"
                    and "Contents: Read & write" in (push_err or "")
                ):
                    needs_install_flag = True
                _progress("push", "failed: %s" % push_err[:80])
                continue

            out = dict(row)
            out.update({"pushed": True, "failure_reason": "", "push_method": push_method})
            if commit_sha:
                out["commit_sha"] = commit_sha[:12]
            rows.append(out)
            completed.append(bname)
            _progress("done", "pushed")

        remaining = [r["branch_name"] for r in cand if r["branch_name"] not in completed]
        if stop_cause is None:
            if len(completed) == total and total > 0:
                stop_cause = "done"
            elif failed:
                stop_cause = "errors"
            else:
                stop_cause = "done"

        return {
            "rows": rows,
            "completed": completed,
            "failed": failed,
            "stopped_at": stopped_at,
            "stop_reason": stop_reason,
            "success": len(completed) == total and total > 0,
            "needs_install": needs_install_flag,
            "total": total,
            "push_method": push_method,
            "used_fallback": False,
            "remaining": remaining,
            "stop_cause": stop_cause,
        }

    primary = _attempt(github_config)
    if primary.get("success"):
        return primary

    fb = fallback_config
    primary_token = (github_config or {}).get("token", "")
    fb_token = (fb or {}).get("token", "")
    failed_names = primary.get("failed") or []
    can_fallback = (
        fb
        and fb_token
        and fb_token != primary_token
        and failed_names
    )
    if not can_fallback:
        return primary

    failed_rows = [
        r for r in (validated_rows or [])
        if r.get("branch_name") in failed_names
    ]
    fallback_result = _attempt(fb, candidates=failed_rows)
    merged_rows = {r["branch_name"]: r for r in primary.get("rows", [])}
    for r in fallback_result.get("rows", []):
        merged_rows[r["branch_name"]] = r
    completed = sorted(set(primary.get("completed", [])) | set(fallback_result.get("completed", [])))
    failed = fallback_result.get("failed") or []
    total = primary.get("total", 0)
    fallback_result["rows"] = list(merged_rows.values())
    fallback_result["completed"] = completed
    fallback_result["failed"] = failed
    fallback_result["remaining"] = [b for b in (primary.get("remaining") or []) if b not in completed]
    fallback_result["success"] = len(completed) == total and total > 0
    fallback_result["used_fallback"] = True
    if fallback_result.get("success"):
        login = fb.get("login") or "shared PAT"
        fallback_result["fallback_note"] = (
            "OAuth token could not write; pushed via shared PAT (@%s). "
            "Add **Contents: Read & write** to the GitHub App for per-user attribution."
            % login
        )
        fallback_result["stop_cause"] = "done"
    else:
        fallback_result["stop_reason"] = (
            "OAuth push failed for some branches; PAT fallback also failed: %s"
            % (fallback_result.get("stop_reason") or primary.get("stop_reason") or "unknown error")
        )
    return fallback_result


def process_branches_sequentially(
    techniques,
    metrics,
    types,
    version,
    language,
    repo_root,
    github_config=None,
    max_fix_attempts=2,
    auto_install=True,
    progress_callback=None,
    app_user=None,
):
    """Legacy all-in-one: generate, validate (fix-until-pass), push."""
    work_root = pipeline_work_dir(repo_root, app_user=app_user)
    gen = generate_branches(
        techniques, metrics, types, version, language, work_root,
        progress_callback=progress_callback,
    )
    if not gen.get("success"):
        return {
            "rows": [_result_row(
                r["branch_name"], r["technique_code"], r["metric_code"], r["branch_type"],
                0, None, False, r.get("error", "generate failed"), r.get("dir", ""),
            ) for r in gen.get("rows", []) if not r.get("generated")],
            "completed": [],
            "stopped_at": gen.get("stopped_at"),
            "stop_reason": gen.get("stop_reason"),
            "success": False,
            "needs_install": False,
            "total": gen.get("total", 0),
        }

    val = validate_branches(
        gen.get("rows", []), version, language,
        max_fix_attempts=max_fix_attempts,
        auto_install=auto_install,
        progress_callback=progress_callback,
        block_strict=True,
    )
    if not val.get("success"):
        return {
            "rows": val.get("rows", []),
            "completed": [],
            "stopped_at": val.get("stopped_at"),
            "stop_reason": val.get("stop_reason"),
            "success": False,
            "needs_install": False,
            "total": val.get("total", 0),
        }

    return push_branches(val.get("rows", []), github_config, progress_callback=progress_callback)
