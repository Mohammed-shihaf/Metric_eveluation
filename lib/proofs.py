"""Gather taxonomy, S3, and local proofs per branch."""

from __future__ import print_function

import contextlib
import os
import shutil
from pathlib import Path

from lib.compare import compare_report_files
from lib.github_api import materialize_branch
from lib.local_tool_runner import (
    run_local_tool_report,
    run_local_tool_batch_isolated,
    _resolve_branch_path,
)
from lib.metrics import classification_dir_for_branch
from lib.registry import iter_branches
from lib.report_schema import (
    find_s3_report_path,
    from_s3_tool_root,
    load_report,
    make_report,
    save_report,
)
from lib.sa_qa import format_task_failure_detail
from lib.s3_sync import sync_from_taxonomy_meta_with_retry
from lib.taxonomy_meta import (
    enrich_taxonomy_meta,
    failing_sections,
    failing_sections_for_branch,
    latest_taxonomy_by_branch,
    load_manifest_runs,
    load_run_summary_from_meta,
    load_taxonomy_gate_json,
    metric_expects_s3_artifacts,
    report_dir_from_meta,
    resolve_branch_taxonomy_meta,
)

ROOT = Path(__file__).resolve().parents[1]

REPORT_TAXONOMY = "taxonomy_report.json"
REPORT_S3 = "s3_report.json"
REPORT_LOCAL = "local_report.json"
REPORT_SONAR = "sonar_report.json"

USABLE_REPORT_STATUSES = frozenset(("PASS", "FAIL", "WARN"))


@contextlib.contextmanager
def branch_source(
    repo_root,
    build_dir,
    branch_name,
    github_config=None,
    ref=None,
    local_root=None,
):
    """Yield branch source path (local pipeline copy first, else GitHub or build/)."""
    with _resolve_branch_path(
        str(repo_root),
        build_dir,
        branch_name,
        github_config=github_config,
        ref=ref,
        local_root=local_root,
    ) as path:
        yield path



def _report_file_usable(path):
    """Return (present, usable) for a standard report JSON file."""
    path = Path(path)
    if not path.is_file():
        return False, False
    try:
        report = load_report(path)
    except Exception:
        return True, False
    status = (report.get("status") or "").upper()
    extra = report.get("extra") or {}
    skip_reason = str(extra.get("skip_reason", "")).lower()
    if status not in USABLE_REPORT_STATUSES:
        return True, False
    if "synthetic" in skip_reason:
        return True, False
    return True, True


def _classification_dir_for_branch(
    branch_name,
    taxonomy_root="taxonomy_reports",
    root=None,
    registry=None,
):
    return classification_dir_for_branch(
        branch_name, taxonomy_root, root=root, registry=registry,
    )


def format_branch_issues(info, s3_report=None):
    """Human-readable issue lines for Stage 2 run results."""
    issues = []
    status = info.get("status", "")
    if status == "ERROR":
        issues.append("Whitebox error: %s" % (info.get("detail") or "unknown"))
    elif status == "SKIPPED":
        issues.append("Skipped: %s" % (info.get("detail") or "not in catalog"))
    elif status == "NOT_COMPLETED":
        issues.append("Not completed: %s" % (info.get("detail") or "no taxonomy report"))

    run_health = info.get("run_health", "")
    if run_health == "DEGRADED":
        issues.append("Platform run degraded: %s" % (info.get("run_health_detail") or "task failures"))
    elif info.get("failed_tasks"):
        issues.append("Platform tasks: %s" % (info.get("run_health_detail") or "partial failures"))

    task_failures = info.get("task_failures") or []
    failure_detail = format_task_failure_detail(task_failures)
    if failure_detail:
        issues.append("Failed tasks: %s" % failure_detail)

    s3_sync = info.get("s3_sync") or {}
    sync_status = s3_sync.get("status")
    if sync_status == "AUTH":
        issues.append("S3 sync failed: AWS credentials rejected")
    elif sync_status and sync_status not in ("OK", "N/A"):
        reason = s3_sync.get("reason") or s3_sync.get("error") or ""
        issues.append("S3 sync during run: %s%s" % (
            sync_status,
            (" — %s" % reason) if reason else "",
        ))

    if s3_report:
        s3_status = s3_report.get("status", "")
        if s3_status == "AUTH":
            detail = (s3_report.get("extra") or {}).get("skip_reason") or s3_report.get("raw_summary") or ""
            issues.append(
                "S3 proof: credentials rejected by AWS%s"
                % ((" — %s" % detail) if detail else "")
            )
        elif s3_status in ("SKIPPED", "ERROR", "MISSING"):
            detail = (s3_report.get("extra") or {}).get("skip_reason") or s3_report.get("raw_summary") or ""
            issues.append("S3 proof: %s%s" % (s3_status, (" — %s" % detail) if detail else ""))

    return issues


def whitebox_completion(branches, taxonomy_root="taxonomy_reports", root=None, registry=None):
    """Per-branch whitebox status from taxonomy HTML + manifest."""
    from lib.registry import load_registry

    reg = registry or load_registry()
    if taxonomy_root == "taxonomy_reports":
        taxonomy_root = os.environ.get("OUTPUT_DIR", "").strip() or taxonomy_root
    repo_root = Path(root or ROOT)
    tax_root = repo_root / taxonomy_root
    out = {}

    # Index manifest runs by branch (latest batch per classification)
    manifest_by_branch = {}
    manifest_errors = {}
    catalog_skipped = set()
    if tax_root.is_dir():
        for class_dir in tax_root.iterdir():
            if not class_dir.is_dir():
                continue
            manifest_path = class_dir / "manifest.json"
            if manifest_path.is_file():
                import json

                manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
                for skipped in manifest_data.get("catalog_skipped", []):
                    catalog_skipped.add(skipped)
            for run in load_manifest_runs(class_dir):
                bname = run.get("branch")
                if not bname:
                    continue
                if run.get("error"):
                    manifest_errors[bname] = run.get("error")
                if run.get("run_id"):
                    manifest_by_branch[bname] = run

    for bname in branches:
        meta, source_dir = resolve_branch_taxonomy_meta(
            bname, taxonomy_root, str(repo_root), reg,
        )
        manifest_run = manifest_by_branch.get(bname) or {}
        meta = enrich_taxonomy_meta(
            meta,
            manifest_run=manifest_run,
            branch_name=bname,
            classification_dir=str(source_dir) if source_dir else None,
        )

        html_path = meta.get("html_path", "")
        has_html = bool(html_path and Path(html_path).is_file())
        gate_json = load_taxonomy_gate_json(meta, classification_dir=str(source_dir) if source_dir else None)
        gate_status = (gate_json.get("gate_status") or "").lower()
        has_taxonomy = has_html or gate_status == "completed"
        run_id = meta.get("run_id") or manifest_run.get("run_id", "")
        gate_score = manifest_run.get("gate_score")
        run_summary = load_run_summary_from_meta(
            meta, classification_dir=str(source_dir) if source_dir else None,
        )
        run_status = (
            run_summary.get("status")
            or manifest_run.get("status")
            or manifest_run.get("run_status")
            or ""
        ).lower()
        total_tasks = run_summary.get("total_tasks") or manifest_run.get("total_tasks") or 0
        completed_tasks = run_summary.get("completed_tasks") or manifest_run.get("completed_tasks") or 0
        failed_tasks = run_summary.get("failed_tasks") or manifest_run.get("failed_tasks") or 0
        task_failures = (
            manifest_run.get("task_failures")
            or run_summary.get("task_failures")
            or []
        )
        taxonomy_complete = has_taxonomy and (has_html or gate_status == "completed")
        fail_sections = (
            failing_sections_for_branch(gate_json, bname, reg)
            if gate_json else []
        )

        if taxonomy_complete:
            run_health = "OK"
            if failed_tasks:
                run_health_detail = (
                    "taxonomy complete; platform run %s with %d/%d tasks (%d failed)"
                    % (run_status or "finished", completed_tasks, total_tasks, failed_tasks)
                )
            else:
                run_health_detail = "taxonomy complete"
        elif run_status == "completed" and (not total_tasks or failed_tasks == 0):
            run_health = "OK"
            run_health_detail = "whitebox run completed"
        elif run_status in ("failed", "partial") or failed_tasks:
            run_health = "DEGRADED"
            run_health_detail = "%s: %d/%d tasks, %d failed" % (
                run_status or "unknown", completed_tasks, total_tasks, failed_tasks,
            )
            failure_detail = format_task_failure_detail(task_failures)
            if failure_detail:
                run_health_detail += " — failed: %s" % failure_detail
        elif has_taxonomy:
            run_health = "OK"
            run_health_detail = "taxonomy produced (run summary unavailable)"
        else:
            run_health = "UNKNOWN"
            run_health_detail = ""

        if bname in manifest_errors and not has_taxonomy:
            status = "ERROR"
            detail = manifest_errors[bname]
        elif has_taxonomy and run_id:
            status = "COMPLETED"
            detail = "taxonomy report produced"
        elif has_taxonomy:
            status = "COMPLETED"
            detail = "taxonomy HTML present"
        elif bname in manifest_errors:
            status = "ERROR"
            detail = manifest_errors[bname]
        elif bname in catalog_skipped:
            status = "SKIPPED"
            detail = (
                "not in Testable catalog — platform branch sync required "
                "(re-run whitebox after catalog updates)"
            )
        else:
            status = "NOT_COMPLETED"
            detail = "whitebox not run or no taxonomy report"

        out[bname] = {
            "status": status,
            "detail": detail,
            "run_id": run_id,
            "commit_sha": meta.get("commit_sha", "") or manifest_run.get("commit_sha", ""),
            "gate_score": gate_score,
            "html_path": html_path,
            "meta": meta,
            "manifest_run": manifest_run,
            "s3_sync": manifest_run.get("s3_sync") or {},
            "run_status": run_status,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "task_failures": task_failures,
            "run_health": run_health,
            "run_health_detail": run_health_detail,
            "failing_sections": fail_sections,
            "expects_s3": metric_expects_s3_artifacts(bname, reg),
        }
    return out


def _report_status_label(path, usable):
    """Human-readable report availability for compare readiness."""
    path = Path(path)
    if not path.is_file():
        return "missing"
    try:
        report = load_report(path)
    except Exception:
        return "invalid"
    status = (report.get("status") or "").upper()
    if usable:
        return status or "OK"
    if status == "N/A":
        return "N/A (expected)"
    if status == "AUTH":
        return "AUTH (refresh AWS creds)"
    if status == "SKIPPED":
        extra = report.get("extra") or {}
        reason = extra.get("skip_reason") or report.get("raw_summary") or ""
        if reason:
            return "SKIPPED (%s)" % reason[:60]
        return "SKIPPED"
    return status or "unusable"


def compare_readiness(branches, root=None):
    """Check which standard reports exist and are usable per branch under proofs/."""
    repo_root = Path(root or ROOT)
    rows = []
    for bname in branches:
        from lib.metrics import infer_from_branch_name

        tech, _, _, _ = infer_from_branch_name(bname)
        if not tech:
            rows.append({
                "branch_name": bname,
                "taxonomy": False,
                "s3": False,
                "local": False,
                "sonar": False,
                "ready": False,
                "can_compare": False,
                "missing": ["parse error"],
            })
            continue
        out_dir = proof_dir(repo_root, tech, bname)
        has_tax, tax_ok = _report_file_usable(out_dir / REPORT_TAXONOMY)
        has_s3, s3_ok = _report_file_usable(out_dir / REPORT_S3)
        has_local, local_ok = _report_file_usable(out_dir / REPORT_LOCAL)
        has_sonar, sonar_ok = _report_file_usable(out_dir / REPORT_SONAR)
        missing = []
        if not tax_ok:
            missing.append("taxonomy (Page 2)" + (" — file missing" if not has_tax else " — SKIPPED/ERROR"))
        if not s3_ok:
            missing.append("S3 (Compare)" + (" — file missing" if not has_s3 else " — SKIPPED/ERROR"))
        if not local_ok:
            missing.append("local (Page 3)" + (" — file missing" if not has_local else " — SKIPPED/ERROR"))
        if not sonar_ok:
            missing.append("sonar (Page 4)" + (" — file missing" if not has_sonar else " — SKIPPED/ERROR/stale"))
        rows.append({
            "branch_name": bname,
            "taxonomy": tax_ok,
            "s3": s3_ok,
            "local": local_ok,
            "sonar": sonar_ok,
            "taxonomy_label": _report_status_label(out_dir / REPORT_TAXONOMY, tax_ok),
            "s3_label": _report_status_label(out_dir / REPORT_S3, s3_ok),
            "local_label": _report_status_label(out_dir / REPORT_LOCAL, local_ok),
            "sonar_label": _report_status_label(out_dir / REPORT_SONAR, sonar_ok),
            "ready": tax_ok and s3_ok and local_ok and sonar_ok,
            "can_compare": s3_ok or local_ok,
            "missing": missing,
        })
    return rows


def completed_whitebox_branches(branches, taxonomy_root="taxonomy_reports", root=None, registry=None):
    """Return branch names with COMPLETED whitebox status."""
    status = whitebox_completion(branches, taxonomy_root, root, registry)
    return [b for b in branches if status.get(b, {}).get("status") == "COMPLETED"]


def proof_dir(root, technique_code, branch_name):
    return Path(root) / "proofs" / technique_code / branch_name


def _copy_taxonomy_proof(src_html, dest_dir):
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / "taxonomy.html"
    shutil.copy2(src_html, dest)
    return str(dest)


def _find_taxonomy_html(branch_name, taxonomy_root="taxonomy_reports", registry=None, root=None):
    repo_root = Path(root or ROOT)
    meta, _source_dir = resolve_branch_taxonomy_meta(
        branch_name, taxonomy_root, str(repo_root), registry,
    )
    html_path = meta.get("html_path")
    if html_path and Path(html_path).is_file():
        return html_path, meta
    return None, meta


def _save_taxonomy_proof(meta, out_dir, tech, metric, branch_name, branch_type, version):
    """Copy taxonomy HTML and write taxonomy_report.json when artifacts exist."""
    from lib.report_schema import from_taxonomy_html, make_report, save_report

    commit_sha = meta.get("commit_sha", "")
    run_id = meta.get("run_id", "")
    html_path = meta.get("html_path", "")

    if html_path and Path(html_path).is_file():
        _copy_taxonomy_proof(html_path, out_dir)
        tax_report = from_taxonomy_html(
            html_path, tech, metric, branch_name, branch_type, version,
            commit_sha=commit_sha, run_id=run_id,
        )
        save_report(tax_report, out_dir / "taxonomy_report.json")
        return tax_report

    gate_json = load_taxonomy_gate_json(meta)
    if not gate_json:
        return None

    gate_status = (gate_json.get("gate_status") or "").lower()
    if gate_status == "completed":
        status = "PASS"
    elif gate_status in ("failed", "error"):
        status = "FAIL"
    else:
        status = "SKIPPED"
    tax_report = make_report(
        technique_code=tech,
        metric_code=metric,
        branch_name=branch_name,
        branch_type=branch_type,
        version=version,
        tool_name="taxonomy-gate",
        source="taxonomy",
        status=status,
        metric_values={"gate_status": gate_status} if gate_status else {},
        raw_summary="taxonomy gate_status=%s" % (gate_status or "missing"),
        commit_sha=commit_sha,
        run_id=run_id,
        extra={"gate_json_only": True},
    )
    save_report(tax_report, out_dir / "taxonomy_report.json")
    return tax_report


def collect_taxonomy_proof(
    branch_name,
    meta=None,
    taxonomy_root="taxonomy_reports",
    root=None,
    manifest_run=None,
):
    """Write taxonomy_report.json (and HTML copy) without fetching S3."""
    if taxonomy_root == "taxonomy_reports":
        taxonomy_root = os.environ.get("OUTPUT_DIR", "").strip() or taxonomy_root
    repo_root = Path(root or ROOT)
    from lib.metrics import infer_from_branch_name

    tech, metric, branch_type, version = infer_from_branch_name(branch_name)
    if not tech:
        raise ValueError("cannot parse branch: %s" % branch_name)

    if meta is None:
        _, meta = _find_taxonomy_html(branch_name, taxonomy_root, root=str(repo_root))

    meta = enrich_taxonomy_meta(meta or {}, manifest_run=manifest_run, branch_name=branch_name)
    meta.setdefault("branch", branch_name)

    out_dir = proof_dir(repo_root, tech, branch_name)
    out_dir.mkdir(parents=True, exist_ok=True)

    tax_report = _save_taxonomy_proof(meta, out_dir, tech, metric, branch_name, branch_type, version)
    tax_json = out_dir / "taxonomy_report.json"
    tax_html = out_dir / "taxonomy.html"
    return {
        "report": tax_report,
        "taxonomy_json": str(tax_json) if tax_json.is_file() else "",
        "taxonomy_html": str(tax_html) if tax_html.is_file() else "",
        "proof_dir": str(out_dir),
    }


def collect_s3_proof(
    branch_name,
    meta=None,
    taxonomy_root="taxonomy_reports",
    download_root=None,
    dry_run=False,
    root=None,
    manifest_run=None,
    expects_s3=None,
    s3_wait_sec=None,
    s3_poll_sec=None,
    skip_taxonomy=False,
):
    """Sync S3 bundle (if needed) and write standard s3_report.json."""
    repo_root = Path(root or ROOT)
    from lib.metrics import infer_from_branch_name

    tech, metric, branch_type, version = infer_from_branch_name(branch_name)
    if not tech:
        raise ValueError("cannot parse branch: %s" % branch_name)

    if meta is None:
        _, meta = _find_taxonomy_html(branch_name, taxonomy_root, root=str(repo_root))

    meta = enrich_taxonomy_meta(meta or {}, manifest_run=manifest_run, branch_name=branch_name)
    meta.setdefault("branch", branch_name)
    commit_sha = meta.get("commit_sha", "")
    run_id = meta.get("run_id", "")

    out_dir = proof_dir(repo_root, tech, branch_name)
    out_dir.mkdir(parents=True, exist_ok=True)

    if not skip_taxonomy:
        _save_taxonomy_proof(meta, out_dir, tech, metric, branch_name, branch_type, version)

    if expects_s3 is None:
        expects_s3 = metric_expects_s3_artifacts(branch_name)

    if not expects_s3:
        report = make_report(
            technique_code=tech,
            metric_code=metric,
            branch_name=branch_name,
            branch_type=branch_type,
            version=version,
            tool_name="platform-s3",
            source="s3",
            status="N/A",
            raw_summary="No platform S3 tool bundle expected for this metric (taxonomy-derived)",
            commit_sha=commit_sha,
            run_id=run_id,
            extra={"skip_reason": "Metric does not publish platform S3 artifacts (emitted_directly=false)"},
        )
        out_path = out_dir / "s3_report.json"
        save_report(report, out_path)
        report["_path"] = str(out_path)
        return report

    dl_root = download_root or os.environ.get("S3_DOWNLOAD_ROOT", str(repo_root / "s3_downloads"))
    sync_summary = (manifest_run or {}).get("s3_sync") or {}
    tool_root = None

    existing_path = sync_summary.get("local_path", "")
    if existing_path and Path(existing_path).is_dir() and any(Path(existing_path).iterdir()):
        tool_root = existing_path
    else:
        tool_root = find_s3_report_path(dl_root, branch_name, commit_sha, run_id)

    if not dry_run and not tool_root and commit_sha and run_id:
        from lib.sa_qa import reload_s3_credentials

        env_file = repo_root / ".env.local"
        if env_file.is_file():
            reload_s3_credentials(str(env_file), root=str(repo_root))
        prev_active = os.environ.get("S3_SYNC_ACTIVE_BRANCHES")
        os.environ["S3_SYNC_ACTIVE_BRANCHES"] = branch_name
        try:
            wait_sec = s3_wait_sec if s3_wait_sec is not None else int(os.environ.get("S3_SYNC_WAIT_SEC", "90"))
            poll_sec = s3_poll_sec if s3_poll_sec is not None else int(os.environ.get("S3_SYNC_POLL_SEC", "10"))
            sync_summary = sync_from_taxonomy_meta_with_retry(
                meta, wait_sec=wait_sec, poll_sec=poll_sec, dry_run=False,
            )
        finally:
            if prev_active is not None:
                os.environ["S3_SYNC_ACTIVE_BRANCHES"] = prev_active
            else:
                os.environ.pop("S3_SYNC_ACTIVE_BRANCHES", None)
        if sync_summary.get("local_path") and Path(sync_summary["local_path"]).is_dir():
            tool_root = sync_summary["local_path"]
        if not tool_root:
            tool_root = find_s3_report_path(dl_root, branch_name, commit_sha, run_id)

    if not tool_root:
        report = from_s3_tool_root(
            str(out_dir),
            tech,
            metric,
            branch_name,
            branch_type,
            version,
            commit_sha=commit_sha,
            run_id=run_id,
        )
        sync_status = (sync_summary or {}).get("status", "")
        sync_reason = (sync_summary or {}).get("reason") or (sync_summary or {}).get("error", "")
        skip_parts = []
        if sync_status == "AUTH":
            report["status"] = "AUTH"
            report["raw_summary"] = sync_reason or "AWS S3 credentials expired or invalid"
            skip_parts.append(report["raw_summary"])
        elif sync_status == "SKIPPED" and sync_reason:
            report["status"] = "SKIPPED"
            report["raw_summary"] = sync_reason
            skip_parts.append(sync_reason)
        else:
            report["status"] = "SKIPPED"
            report["raw_summary"] = "S3 bundle not found after sync"
            skip_parts.append(
                "S3 bundle not found for commit=%s run=%s under %s"
                % (commit_sha or "?", run_id or "?", dl_root)
            )
            if sync_status and sync_status not in ("OK",):
                skip_parts.append("sync %s: %s" % (sync_status, sync_reason or "no details"))
        if not commit_sha or not run_id:
            skip_parts.append("missing commit_sha or run_id in taxonomy metadata")
        report.setdefault("extra", {})["skip_reason"] = "; ".join(skip_parts)
        if sync_summary:
            report["extra"]["sync_summary"] = sync_summary
    else:
        report = from_s3_tool_root(
            tool_root,
            tech,
            metric,
            branch_name,
            branch_type,
            version,
            commit_sha=commit_sha,
            run_id=run_id,
        )
        if sync_summary:
            report.setdefault("extra", {})["sync_summary"] = sync_summary

    out_path = out_dir / "s3_report.json"
    save_report(report, out_path)
    report["_path"] = str(out_path)
    return report


def collect_local_proof(
    branch_name,
    build_dir="build",
    install=True,
    root=None,
    meta=None,
    github_config=None,
    local_root=None,
    language=None,
):
    """Run local tool and write standard local_report.json."""
    repo_root = Path(root or ROOT)
    from lib.metrics import infer_from_branch_name

    tech, metric, branch_type, version = infer_from_branch_name(branch_name)
    if not tech:
        raise ValueError("cannot parse branch: %s" % branch_name)

    out_dir = proof_dir(repo_root, tech, branch_name)
    out_dir.mkdir(parents=True, exist_ok=True)

    commit_sha = (meta or {}).get("commit_sha", "")
    run_id = (meta or {}).get("run_id", "")

    with branch_source(
        repo_root,
        build_dir,
        branch_name,
        github_config=github_config,
        ref=commit_sha or branch_name,
        local_root=local_root,
    ) as branch_path:
        from lib.lang_support import branch_language, normalize_language

        lang = normalize_language(language or branch_language(branch_path))
        report = run_local_tool_report(
            branch_path,
            tech,
            metric,
            branch_type,
            version,
            language=lang,
            commit_sha=commit_sha,
            run_id=run_id,
            install=install,
            require_real_tool=True,
        )
    out_path = out_dir / "local_report.json"
    save_report(report, out_path)
    report["_path"] = str(out_path)
    return report


def collect_sonar_proof(
    branch_name,
    build_dir="build",
    root=None,
    meta=None,
    host_url=None,
    token=None,
    github_config=None,
):
    """Run SonarQube scan and write standard sonar_report.json."""
    from lib.sonar_runner import run_sonar_for_branch

    repo_root = Path(root or ROOT)
    from lib.metrics import infer_from_branch_name

    tech, metric, branch_type, version = infer_from_branch_name(branch_name)
    if not tech:
        raise ValueError("cannot parse branch: %s" % branch_name)

    out_dir = proof_dir(repo_root, tech, branch_name)
    out_dir.mkdir(parents=True, exist_ok=True)

    commit_sha = (meta or {}).get("commit_sha", "")
    run_id = (meta or {}).get("run_id", "")

    with branch_source(
        repo_root, build_dir, branch_name, github_config=github_config, ref=commit_sha or branch_name,
    ) as branch_path:
        report, _log = run_sonar_for_branch(
            branch_path,
            host_url=host_url,
            token=token,
            root=repo_root,
        )
    if commit_sha and not report.get("commit_sha"):
        report["commit_sha"] = commit_sha
    if run_id and not report.get("run_id"):
        report["run_id"] = run_id

    out_path = out_dir / REPORT_SONAR
    save_report(report, out_path)
    report["_path"] = str(out_path)
    return report


def _skipped_report(branch_name, reason):
    return {
        "branch_name": branch_name,
        "status": "SKIPPED",
        "extra": {"skip_reason": reason},
    }


def _load_or_skip_report(path, branch_name, label):
    if path.is_file():
        return load_report(path)
    return _skipped_report(branch_name, "%s report not produced" % label)


def collect_comparison_proof(branch_name, root=None):
    """Compare S3, local, and SonarQube reports; taxonomy is reference-only."""
    repo_root = Path(root or ROOT)
    from lib.metrics import infer_from_branch_name

    tech, _, _, _ = infer_from_branch_name(branch_name)
    if not tech:
        raise ValueError("cannot parse branch: %s" % branch_name)

    out_dir = proof_dir(repo_root, tech, branch_name)
    tax_path = out_dir / REPORT_TAXONOMY
    s3_path = out_dir / REPORT_S3
    local_path = out_dir / REPORT_LOCAL
    sonar_path = out_dir / REPORT_SONAR

    has_s3 = s3_path.is_file()
    has_local = local_path.is_file()
    has_tax = tax_path.is_file()
    has_sonar = sonar_path.is_file()

    missing = []
    if not has_tax:
        missing.append("taxonomy_report.json")
    if not has_s3:
        missing.append("s3_report.json")
    if not has_local:
        missing.append("local_report.json")
    if not has_sonar:
        missing.append("sonar_report.json")

    if not has_s3 and not has_local:
        return {
            "branch_name": branch_name,
            "verdict": "INCOMPLETE",
            "summary": "need at least S3 or local report in %s" % out_dir,
            "proof_dir": str(out_dir),
            "missing_reports": missing,
        }

    from lib.compare import compare_four_reports

    tax_report = (
        load_report(tax_path)
        if has_tax
        else _skipped_report(branch_name, "taxonomy report not produced")
    )
    s3_report = (
        load_report(s3_path)
        if has_s3
        else _skipped_report(branch_name, "S3 report not produced")
    )
    local_report = (
        load_report(local_path)
        if has_local
        else _skipped_report(branch_name, "local report not produced")
    )
    sonar_report = (
        load_report(sonar_path)
        if has_sonar
        else _skipped_report(branch_name, "SonarQube report not produced (Docker required)")
    )
    comparison = compare_four_reports(tax_report, s3_report, local_report, sonar_report)
    comparison["proof_dir"] = str(out_dir)
    comparison["missing_reports"] = missing
    if has_local:
        extra_local = local_report.get("extra") or {}
        comparison["local_tool_name"] = local_report.get("tool_name", "")
        comparison["local_executed_tool"] = extra_local.get("executed_tool", "")
        comparison["local_real_tool"] = extra_local.get("real_tool")
        comparison["local_raw_summary"] = local_report.get("raw_summary", "")
        comparison["local_metric_values"] = local_report.get("metric_values") or {}
    if has_s3:
        extra_s3 = s3_report.get("extra") or {}
        comparison["s3_tool_name"] = s3_report.get("tool_name", "")
        comparison["s3_executed_tool"] = extra_s3.get("executed_tool", "")
        comparison["s3_metric_values"] = s3_report.get("metric_values") or {}
        comparison["s3_raw_summary"] = s3_report.get("raw_summary", "")
        comparison["s3_executed"] = s3_report.get("status") in ("PASS", "FAIL", "WARN")
        comparison["s3_real_tool"] = extra_s3.get("real_tool")
    if has_sonar:
        extra_sonar = sonar_report.get("extra") or {}
        comparison["sonar_tool_name"] = sonar_report.get("tool_name", "")
        comparison["sonar_metric_values"] = sonar_report.get("metric_values") or {}
        comparison["sonar_raw_summary"] = sonar_report.get("raw_summary", "")
        comparison["sonar_real_tool"] = extra_sonar.get("real_tool")
    out_path = out_dir / "comparison.json"
    import json

    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(comparison, fh, indent=2)
    comparison["comparison_path"] = str(out_path)
    return comparison


def collect_local_batch(
    branches,
    build_dir="build",
    install=True,
    taxonomy_root="taxonomy_reports",
    root=None,
    progress_callback=None,
    require_whitebox=True,
    isolated=None,
    github_config=None,
    local_root=None,
    language=None,
):
    """Run local tools for an explicit branch list."""
    repo_root = Path(root or ROOT)
    if isolated is None:
        isolated = os.environ.get("LOCAL_TOOL_ISOLATED", "true").lower() in ("1", "true", "yes")
    results = []
    total = len(branches)
    wb = whitebox_completion(branches, taxonomy_root, repo_root)

    runnable = []
    for bname in branches:
        wb_info = wb.get(bname, {})
        if require_whitebox and wb_info.get("status") != "COMPLETED":
            row = {
                "branch_name": bname,
                "status": "SKIPPED",
                "error": "whitebox not completed",
            }
            results.append(row)
            if progress_callback:
                progress_callback("local", len(results), total, bname, "skipped")
            continue
        runnable.append((bname, wb_info.get("meta") or {}))

    if not runnable:
        return results

    if isolated:
        commit_sha_by_branch = {b: m.get("commit_sha", "") for b, m in runnable}
        run_id_by_branch = {b: m.get("run_id", "") for b, m in runnable}
        branch_names = [b for b, _ in runnable]
        reports = run_local_tool_batch_isolated(
            branch_names,
            build_dir=build_dir,
            output_dir="proofs",
            root=str(repo_root),
            commit_sha_by_branch=commit_sha_by_branch,
            run_id_by_branch=run_id_by_branch,
            progress_callback=progress_callback,
            github_config=github_config,
            local_root=local_root,
            language=language,
        )
        report_by_branch = {r.get("branch_name"): r for r in reports}
        for idx, (bname, _) in enumerate(runnable, start=1):
            report = report_by_branch.get(bname, {})
            extra = report.get("extra") or {}
            row = {
                "branch_name": bname,
                "local_report": report,
                "status": report.get("status", "OK"),
                "tool": report.get("tool_name", ""),
                "executed_tool": extra.get("executed_tool", ""),
                "real_tool": extra.get("real_tool"),
                "skip_reason": extra.get("skip_reason", ""),
                "tool_log": extra.get("tool_log", ""),
                "tool_stderr": extra.get("tool_stderr", ""),
                "install_msg": extra.get("install_msg", ""),
                "install_failed": extra.get("install_failed", []),
                "report_path": report.get("_path") or extra.get("report_path", ""),
            }
            results.append(row)
        return results

    for idx, (bname, meta) in enumerate(runnable, start=1):
        if progress_callback:
            progress_callback("local", idx - 1, total, bname, "starting")
        row = {"branch_name": bname}
        try:
            report = collect_local_proof(
                bname,
                build_dir=build_dir,
                install=install,
                root=repo_root,
                meta=meta,
                github_config=github_config,
                local_root=local_root,
                language=language,
            )
            row["local_report"] = report
            row["status"] = report.get("status", "OK")
            row["tool"] = report.get("tool_name", "")
            extra = report.get("extra") or {}
            row["executed_tool"] = extra.get("executed_tool", "")
            row["real_tool"] = extra.get("real_tool")
            row["skip_reason"] = extra.get("skip_reason", "")
            row["tool_log"] = extra.get("tool_log", "")
            row["install_msg"] = extra.get("install_msg", "")
            if progress_callback:
                progress_callback("local", idx, total, bname, row["status"])
        except Exception as exc:
            row["status"] = "ERROR"
            row["error"] = str(exc)
            if progress_callback:
                progress_callback("local", idx, total, bname, "error: %s" % exc)
        results.append(row)
    return results


def collect_sonar_batch(
    branches,
    build_dir="build",
    taxonomy_root="taxonomy_reports",
    root=None,
    progress_callback=None,
    require_whitebox=False,
    github_config=None,
):
    """Run SonarQube for an explicit branch list (server started once)."""
    from lib.sonar_runner import ensure_sonar_server, ensure_sonar_token, run_sonar_for_branch

    repo_root = Path(root or ROOT)
    results = []
    total = len(branches)
    wb = whitebox_completion(branches, taxonomy_root, repo_root)

    ok, host_url, server_msg = ensure_sonar_server(root=repo_root)
    if not ok:
        for bname in branches:
            from lib.metrics import infer_from_branch_name

            tech, metric, branch_type, version = infer_from_branch_name(bname)
            if not tech:
                results.append({
                    "branch_name": bname,
                    "status": "ERROR",
                    "error": server_msg,
                })
                continue
            report = make_report(
                technique_code=tech,
                metric_code=metric,
                branch_name=bname,
                branch_type=branch_type,
                version=version,
                tool_name="SonarQube Community",
                source="sonar",
                status="ERROR",
                raw_summary=server_msg,
                extra={"skip_reason": server_msg},
            )
            out_dir = proof_dir(repo_root, tech, bname)
            out_dir.mkdir(parents=True, exist_ok=True)
            save_report(report, out_dir / REPORT_SONAR)
            results.append({
                "branch_name": bname,
                "status": "ERROR",
                "error": server_msg,
                "sonar_report": report,
            })
        return results

    try:
        token = ensure_sonar_token(host_url, root=repo_root)
    except Exception as exc:
        for bname in branches:
            from lib.metrics import infer_from_branch_name

            tech, metric, branch_type, version = infer_from_branch_name(bname)
            if not tech:
                results.append({
                    "branch_name": bname,
                    "status": "ERROR",
                    "error": str(exc),
                })
                continue
            report = make_report(
                technique_code=tech,
                metric_code=metric,
                branch_name=bname,
                branch_type=branch_type,
                version=version,
                tool_name="SonarQube Community",
                source="sonar",
                status="ERROR",
                raw_summary=str(exc),
                extra={"skip_reason": str(exc)},
            )
            out_dir = proof_dir(repo_root, tech, bname)
            out_dir.mkdir(parents=True, exist_ok=True)
            save_report(report, out_dir / REPORT_SONAR)
            results.append({
                "branch_name": bname,
                "status": "ERROR",
                "error": str(exc),
                "sonar_report": report,
            })
        return results

    for idx, bname in enumerate(branches, start=1):
        if progress_callback:
            progress_callback("sonar", idx - 1, total, bname, "starting")
        row = {"branch_name": bname, "server_msg": server_msg}
        wb_info = wb.get(bname, {})
        if require_whitebox and wb_info.get("status") != "COMPLETED":
            row["status"] = "SKIPPED"
            row["error"] = "whitebox not completed"
            results.append(row)
            if progress_callback:
                progress_callback("sonar", idx, total, bname, "skipped")
            continue
        try:
            from lib.metrics import infer_from_branch_name

            meta = wb_info.get("meta") or {}
            with branch_source(
                repo_root,
                build_dir,
                bname,
                github_config=github_config,
                ref=meta.get("commit_sha") or bname,
            ) as branch_path:
                report, log = run_sonar_for_branch(
                    branch_path,
                    host_url=host_url,
                    token=token,
                    root=repo_root,
                )
            if meta.get("commit_sha") and not report.get("commit_sha"):
                report["commit_sha"] = meta["commit_sha"]
            if meta.get("run_id") and not report.get("run_id"):
                report["run_id"] = meta["run_id"]
            out_dir = proof_dir(repo_root, infer_from_branch_name(bname)[0], bname)
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / REPORT_SONAR
            save_report(report, out_path)
            report["_path"] = str(out_path)
            row["sonar_report"] = report
            row["status"] = report.get("status", "OK")
            row["tool_log"] = log
            row["coverage_pct"] = (report.get("metric_values") or {}).get("coverage_pct")
            row["skip_reason"] = (report.get("extra") or {}).get("skip_reason", "")
            if progress_callback:
                progress_callback("sonar", idx, total, bname, row["status"])
        except Exception as exc:
            row["status"] = "ERROR"
            row["error"] = str(exc)
            if progress_callback:
                progress_callback("sonar", idx, total, bname, "error: %s" % exc)
        results.append(row)
    return results


def collect_proofs_batch(
    techniques="all",
    metrics="all",
    types=None,
    version="2.6",
    build_dir="build",
    taxonomy_root="taxonomy_reports",
    root=None,
    install_local=True,
    sync_s3=True,
    run_local=True,
    compare=True,
    progress_callback=None,
):
    """Full proof pipeline for selected branches."""
    repo_root = Path(root or ROOT)
    results = []
    planned = list(iter_branches(techniques, metrics, types, version))
    total = len(planned)

    for idx, (tech, metric, bt, bname) in enumerate(planned, start=1):
        if progress_callback:
            progress_callback("proofs", idx - 1, total, bname, "starting")
        row = {"branch_name": bname, "technique": tech, "metric": metric, "type": bt}
        _, meta = _find_taxonomy_html(bname, taxonomy_root, root=str(repo_root))

        try:
            if sync_s3:
                row["s3_report"] = collect_s3_proof(
                    bname, meta=meta, taxonomy_root=taxonomy_root, root=repo_root
                )
                if progress_callback:
                    progress_callback(
                        "proofs", idx - 1, total, bname,
                        "s3 %s" % (row["s3_report"].get("status", "?")),
                    )
            if run_local:
                row["local_report"] = collect_local_proof(
                    bname, build_dir=build_dir, install=install_local, root=repo_root, meta=meta
                )
                if progress_callback:
                    progress_callback(
                        "proofs", idx - 1, total, bname,
                        "local %s" % (row["local_report"].get("status", "?")),
                    )
            if compare and row.get("s3_report") and row.get("local_report"):
                row["comparison"] = collect_comparison_proof(bname, root=repo_root)
            row["proof_dir"] = str(proof_dir(repo_root, tech, bname))
            row["status"] = "OK"
            if progress_callback:
                progress_callback("proofs", idx, total, bname, "done")
        except Exception as exc:
            row["status"] = "ERROR"
            row["error"] = str(exc)
            if progress_callback:
                progress_callback("proofs", idx, total, bname, "error: %s" % exc)
        results.append(row)

    return results


def list_proof_branches(root=None, techniques=None):
    """List branches that have any proof artifacts."""
    repo_root = Path(root or ROOT)
    proofs_root = repo_root / "proofs"
    if not proofs_root.is_dir():
        return []
    branches = []
    for tech_dir in sorted(proofs_root.iterdir()):
        if not tech_dir.is_dir():
            continue
        if techniques and tech_dir.name not in techniques:
            continue
        for branch_dir in sorted(tech_dir.iterdir()):
            if branch_dir.is_dir():
                branches.append({
                    "technique": tech_dir.name,
                    "branch_name": branch_dir.name,
                    "proof_dir": str(branch_dir),
                    "has_taxonomy": (branch_dir / REPORT_TAXONOMY).is_file()
                    or (branch_dir / "taxonomy.html").is_file(),
                    "has_s3": (branch_dir / REPORT_S3).is_file(),
                    "has_local": (branch_dir / REPORT_LOCAL).is_file(),
                    "has_sonar": (branch_dir / REPORT_SONAR).is_file(),
                    "has_comparison": (branch_dir / "comparison.json").is_file(),
                })
    return branches


def load_proof_bundle(branch_name, root=None):
    """Load all proof artifacts for a branch."""
    repo_root = Path(root or ROOT)
    from lib.metrics import infer_from_branch_name

    tech, _, _, _ = infer_from_branch_name(branch_name)
    if not tech:
        return None
    out_dir = proof_dir(repo_root, tech, branch_name)
    bundle = {"branch_name": branch_name, "proof_dir": str(out_dir)}
    for key, filename in (
        ("taxonomy_html", "taxonomy.html"),
        ("taxonomy_report", "taxonomy_report.json"),
        ("s3_report", "s3_report.json"),
        ("local_report", "local_report.json"),
        ("sonar_report", "sonar_report.json"),
        ("comparison", "comparison.json"),
    ):
        path = out_dir / filename
        if path.is_file():
            if filename.endswith(".json"):
                bundle[key] = load_report(path)
                bundle[key]["_path"] = str(path)
            else:
                bundle[key] = str(path)
    return bundle
