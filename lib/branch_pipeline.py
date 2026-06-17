"""Per-branch generate -> validate (fix-until-pass) -> push pipeline."""

from __future__ import print_function

import hashlib
import json
import os
import shutil
import subprocess
import sys

from lib.branch_asserts import assert_branch_full
from lib.branch_post_verify import verify_generated_branch
from lib.github_api import push_branch_to_github, read_remote_text
from lib.github_auth import check_app_repo_access
from lib.lang_generators.base import effective_strength
from lib.lang_generators import write_branch
from lib.python_generator import generate_branch_files, read_gen_meta
from lib.registry import iter_branches
from lib.tool_map import metric_tool, pip_packages_for_family, pip_packages_for_primary
from lib.lang_tool_runners import packages_for_language


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
        if os.path.isdir(branch_dir):
            meta = read_gen_meta(branch_dir)
            rows.append({
                "branch_name": bname,
                "technique_code": tech,
                "metric_code": metric,
                "branch_type": bt,
                "dir": branch_dir,
                "generated": True,
                "error": "",
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


def _fix_branch(tech, metric, bt, version, language, branch_path, auto_install, strength=0):
    """Regenerate one branch with escalating strength and optionally install tools."""
    write_branch(branch_path, tech, metric, bt, version, language, strength=strength)
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
):
    """Write in-scope branches to work_root/<branch_name>."""
    work_root = os.path.abspath(work_root)
    if clear_existing and os.path.isdir(work_root):
        shutil.rmtree(work_root, ignore_errors=True)
    os.makedirs(work_root, exist_ok=True)

    planned = list(iter_branches(techniques, metrics, types, version))
    total = len(planned)
    rows = []
    stopped_at = None
    stop_reason = None

    for idx, (tech, metric, bt, bname) in enumerate(planned, start=1):
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
                branch_dir, tech, metric, bt, version, language, strength=strength,
            )
            meta = read_gen_meta(branch_dir)
            _progress("verify", "structure, import, pytest")

            def _verify_cb(step, msg):
                _progress(step, msg)

            vr = verify_generated_branch(
                branch_dir, tech, metric, bt, version, language,
                progress_callback=_verify_cb,
            )
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
    if total == 0:
        return {
            "rows": rows,
            "generated": generated,
            "stopped_at": None,
            "stop_reason": "No branches in scope",
            "success": False,
            "total": 0,
        }
    return {
        "rows": rows,
        "generated": generated,
        "stopped_at": stopped_at,
        "stop_reason": stop_reason,
        "success": len(generated) == total,
        "total": total,
    }


def validate_branches(
    gen_rows,
    version,
    language,
    max_fix_attempts=2,
    auto_install=True,
    progress_callback=None,
    block_strict=True,
):
    """Run assert validation with fix-until-pass loop per branch."""
    rows_in = [r for r in (gen_rows or []) if r.get("generated") and r.get("dir")]
    total = len(rows_in)
    rows = []
    validated = []
    stopped_at = None
    stop_reason = None

    if total == 0:
        return {
            "rows": rows,
            "validated": validated,
            "stopped_at": None,
            "stop_reason": "No generated branches to validate — run Generate first",
            "success": False,
            "total": 0,
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

    return {
        "rows": rows,
        "validated": validated,
        "stopped_at": stopped_at,
        "stop_reason": stop_reason,
        "success": len(validated) == total,
        "total": total,
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
    )
    rows_by_branch = {r["branch_name"]: r for r in result.get("rows", [])}
    validated = set(result.get("validated") or [])
    total = result.get("total", 0)
    rounds_used = 0

    if total == 0:
        result["rounds_used"] = 0
        return result

    stalled = False
    best_by_branch = {
        bname: _branch_strength_score(row)
        for bname, row in rows_by_branch.items()
        if bname not in validated
    }

    while len(validated) < total and rounds_used < max_rounds:
        rounds_used += 1
        failed_rows = [
            g for g in (gen_rows or [])
            if g.get("generated") and g.get("dir") and g["branch_name"] not in validated
        ]
        if not failed_rows:
            break
        n_failed = len(failed_rows)
        for idx, g in enumerate(failed_rows, start=1):
            bname = g["branch_name"]
            try:
                base_strength = max(0, int(g.get("strength") or 0))
            except (TypeError, ValueError):
                base_strength = 0
            new_strength = base_strength + rounds_used
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
            )
            meta = read_gen_meta(g["dir"])
            g["strength"] = meta.get("strength", new_strength)
            g["loc"] = meta.get("loc")

        sub = validate_branches(
            failed_rows,
            version,
            language,
            max_fix_attempts=max_fix_attempts,
            auto_install=auto_install,
            progress_callback=progress_callback,
            block_strict=block_strict,
        )
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
            stalled = True
            break

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

    return {
        "rows": rows,
        "validated": sorted(validated),
        "stopped_at": stopped_at,
        "stop_reason": stop_reason,
        "success": len(validated) == total and total > 0,
        "total": total,
        "rounds_used": rounds_used,
    }


def push_branches(
    validated_rows,
    github_config,
    progress_callback=None,
    fallback_config=None,
):
    """Push validated branch directories to GitHub."""

    def _empty_result(reason, needs_install=False, total=0):
        return {
            "rows": [],
            "completed": [],
            "stopped_at": None,
            "stop_reason": reason,
            "success": False,
            "needs_install": needs_install,
            "total": total,
            "push_method": None,
            "used_fallback": False,
        }

    def _attempt(cfg):
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
                "stopped_at": None,
                "stop_reason": access_msg,
                "success": False,
                "needs_install": needs_install,
                "total": 0,
                "push_method": push_method,
                "used_fallback": False,
            }

        candidates = [
            r for r in (validated_rows or [])
            if r.get("overall") in ("PASS", "PARTIAL") and r.get("dir") and os.path.isdir(r.get("dir"))
        ]
        total = len(candidates)
        rows = []
        completed = []
        stopped_at = None
        stop_reason = None

        for idx, row in enumerate(candidates, start=1):
            tech = row["technique_code"]
            metric = row["metric_code"]
            bt = row["branch_type"]
            bname = row["branch_name"]
            branch_dir = row["dir"]

            def _progress(step, msg):
                if progress_callback:
                    progress_callback(step, idx - 1, total, bname, msg)

            _progress("push", "pushing to GitHub")
            meta = read_gen_meta(branch_dir)
            gen_strength = int(meta.get("strength", 0) or 0)
            gen_version = (meta.get("version") or "2.6").strip() or "2.6"
            gen_language = (meta.get("language") or "python").strip() or "python"
            files = generate_branch_files(
                tech, metric, bt, gen_version, gen_language, strength=gen_strength,
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
                stopped_at = bname
                stop_reason = push_err
                break

            out = dict(row)
            out.update({"pushed": True, "failure_reason": "", "push_method": push_method})
            if commit_sha:
                out["commit_sha"] = commit_sha[:12]
            rows.append(out)
            completed.append(bname)
            _progress("done", "pushed")

        return {
            "rows": rows,
            "completed": completed,
            "stopped_at": stopped_at,
            "stop_reason": stop_reason,
            "success": stopped_at is None and len(completed) == total and total > 0,
            "needs_install": False,
            "total": total,
            "push_method": push_method,
            "used_fallback": False,
        }

    primary = _attempt(github_config)
    if primary.get("success"):
        return primary

    fb = fallback_config
    primary_token = (github_config or {}).get("token", "")
    fb_token = (fb or {}).get("token", "")
    can_fallback = (
        fb
        and fb_token
        and fb_token != primary_token
        and not primary.get("success")
    )
    if not can_fallback:
        return primary

    fallback_result = _attempt(fb)
    if fallback_result.get("success"):
        login = fb.get("login") or "shared PAT"
        fallback_result["used_fallback"] = True
        fallback_result["fallback_note"] = (
            "OAuth token could not write; pushed via shared PAT (@%s). "
            "Add **Contents: Read & write** to the GitHub App for per-user attribution."
            % login
        )
        return fallback_result

    fallback_result["used_fallback"] = True
    fallback_result["stop_reason"] = (
        "OAuth push failed; PAT fallback also failed: %s"
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
