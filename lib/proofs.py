"""Gather taxonomy, S3, and local proofs per branch."""

from __future__ import print_function

import contextlib
import os
import shutil
from pathlib import Path

from lib.compare import compare_report_files
from lib.github_api import materialize_branch
from lib.local_tool_runner import run_local_tool_report, run_local_tool_batch_isolated
from lib.metrics import report_group_label
from lib.registry import iter_branches
from lib.report_schema import (
    find_s3_report_path,
    from_s3_tool_root,
    load_report,
    make_report,
    save_report,
)
from lib.s3_sync import sync_from_taxonomy_meta
from lib.taxonomy_meta import latest_taxonomy_by_branch, load_manifest_runs

ROOT = Path(__file__).resolve().parents[1]

REPORT_TAXONOMY = "taxonomy_report.json"
REPORT_S3 = "s3_report.json"
REPORT_LOCAL = "local_report.json"
REPORT_SONAR = "sonar_report.json"

USABLE_REPORT_STATUSES = frozenset(("PASS", "FAIL", "WARN"))


@contextlib.contextmanager
def branch_source(repo_root, build_dir, branch_name, github_config=None, ref=None):
    """Yield a filesystem path to branch source (GitHub zipball or local build/)."""
    if github_config and github_config.get("token") and github_config.get("repo_slug"):
        with materialize_branch(
            github_config["token"],
            github_config["repo_slug"],
            branch_name,
            ref=ref or branch_name,
        ) as path:
            yield path
    else:
        yield str(Path(repo_root) / build_dir / branch_name)



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


def _classification_dir_for_branch(branch_name, taxonomy_root="taxonomy_reports", registry=None):
    from lib.metrics import infer_from_branch_name

    tech, _, _, _ = infer_from_branch_name(branch_name, registry)
    if not tech:
        return None
    group = report_group_label(tech, registry)
    return Path(taxonomy_root) / group


def whitebox_completion(branches, taxonomy_root="taxonomy_reports", root=None, registry=None):
    """Per-branch whitebox status from taxonomy HTML + manifest."""
    from lib.registry import load_registry

    reg = registry or load_registry()
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
        class_dir = _classification_dir_for_branch(bname, taxonomy_root, reg)
        meta = {}
        if class_dir and class_dir.is_dir():
            meta = latest_taxonomy_by_branch(class_dir).get(bname, {})

        html_path = meta.get("html_path", "")
        has_taxonomy = bool(html_path and Path(html_path).is_file())
        run_id = meta.get("run_id") or (manifest_by_branch.get(bname) or {}).get("run_id", "")
        gate_score = (manifest_by_branch.get(bname) or {}).get("gate_score")

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
            detail = "not in Testable catalog yet — re-run whitebox after catalog sync"
        else:
            status = "NOT_COMPLETED"
            detail = "whitebox not run or no taxonomy report"

        out[bname] = {
            "status": status,
            "detail": detail,
            "run_id": run_id,
            "commit_sha": meta.get("commit_sha", ""),
            "gate_score": gate_score,
            "html_path": html_path,
            "meta": meta,
        }
    return out


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
            missing.append("S3 (Page 2)" + (" — file missing" if not has_s3 else " — SKIPPED/ERROR"))
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
            "ready": tax_ok and s3_ok and local_ok and sonar_ok,
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


def _find_taxonomy_html(branch_name, taxonomy_root="taxonomy_reports", registry=None):
    from lib.metrics import infer_from_branch_name

    tech, metric, _, _ = infer_from_branch_name(branch_name)
    if not tech:
        return None, {}
    group = report_group_label(tech, registry)
    class_dir = Path(taxonomy_root) / group
    by_branch = latest_taxonomy_by_branch(class_dir)
    meta = by_branch.get(branch_name)
    if not meta:
        return None, {}
    html_path = meta.get("html_path")
    if html_path and Path(html_path).is_file():
        return html_path, meta
    return None, meta


def collect_s3_proof(
    branch_name,
    meta=None,
    taxonomy_root="taxonomy_reports",
    download_root=None,
    dry_run=False,
    root=None,
):
    """Sync S3 bundle (if needed) and write standard s3_report.json."""
    repo_root = Path(root or ROOT)
    from lib.metrics import infer_from_branch_name

    tech, metric, branch_type, version = infer_from_branch_name(branch_name)
    if not tech:
        raise ValueError("cannot parse branch: %s" % branch_name)

    if meta is None:
        _, meta = _find_taxonomy_html(branch_name, taxonomy_root)

    meta = meta or {}
    commit_sha = meta.get("commit_sha", "")
    run_id = meta.get("run_id", "")
    html_path = meta.get("html_path", "")

    out_dir = proof_dir(repo_root, tech, branch_name)
    out_dir.mkdir(parents=True, exist_ok=True)

    if html_path and Path(html_path).is_file():
        _copy_taxonomy_proof(html_path, out_dir)
        from lib.report_schema import from_taxonomy_html, save_report

        tax_report = from_taxonomy_html(
            html_path, tech, metric, branch_name, branch_type, version,
            commit_sha=commit_sha, run_id=run_id,
        )
        save_report(tax_report, out_dir / "taxonomy_report.json")

    if not dry_run and commit_sha and run_id:
        from lib.sa_qa import load_env

        env_file = repo_root / ".env.local"
        if env_file.is_file():
            load_env(str(env_file))
        sync_summary = sync_from_taxonomy_meta(meta, dry_run=False)
    else:
        sync_summary = None

    dl_root = download_root or os.environ.get("S3_DOWNLOAD_ROOT", str(repo_root / "s3_downloads"))
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
        report["status"] = "SKIPPED"
        report["raw_summary"] = "S3 bundle not found"
        skip_parts = [
            "S3 bundle not found for commit=%s run=%s under %s"
            % (commit_sha or "?", run_id or "?", dl_root)
        ]
        if sync_summary:
            sync_status = sync_summary.get("status", "")
            sync_reason = sync_summary.get("reason") or sync_summary.get("error", "")
            if sync_status and sync_status != "OK":
                skip_parts.append("sync %s: %s" % (sync_status, sync_reason or "no details"))
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
        repo_root, build_dir, branch_name, github_config=github_config, ref=commit_sha or branch_name,
    ) as branch_path:
        report = run_local_tool_report(
            branch_path,
            tech,
            metric,
            branch_type,
            version,
            commit_sha=commit_sha,
            run_id=run_id,
            install=install,
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


def collect_comparison_proof(branch_name, root=None):
    """Compare taxonomy, S3, and local standard reports for one branch."""
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
    missing = []
    if not tax_path.is_file():
        missing.append("taxonomy_report.json")
    if not s3_path.is_file():
        missing.append("s3_report.json")
    if not local_path.is_file():
        missing.append("local_report.json")
    if not sonar_path.is_file():
        missing.append("sonar_report.json")
    if missing:
        comparison = {
            "branch_name": branch_name,
            "verdict": "INCOMPLETE",
            "summary": "missing report(s): %s in %s" % (", ".join(missing), out_dir),
            "proof_dir": str(out_dir),
            "missing_reports": missing,
        }
        return comparison

    from lib.compare import compare_four_reports

    tax_report = load_report(tax_path)
    s3_report = load_report(s3_path)
    local_report = load_report(local_path)
    sonar_report = load_report(sonar_path)
    comparison = compare_four_reports(tax_report, s3_report, local_report, sonar_report)
    comparison["proof_dir"] = str(out_dir)
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
        )
        report_by_branch = {r.get("branch_name"): r for r in reports}
        for idx, (bname, _) in enumerate(runnable, start=1):
            report = report_by_branch.get(bname, {})
            row = {
                "branch_name": bname,
                "local_report": report,
                "status": report.get("status", "OK"),
                "tool": report.get("tool_name", ""),
                "skip_reason": (report.get("extra") or {}).get("skip_reason", ""),
                "tool_log": (report.get("extra") or {}).get("tool_log", ""),
                "install_msg": (report.get("extra") or {}).get("install_msg", ""),
            }
            results.append(row)
        return results

    for idx, (bname, meta) in enumerate(runnable, start=1):
        if progress_callback:
            progress_callback("local", idx - 1, total, bname, "starting")
        row = {"branch_name": bname}
        try:
            report = collect_local_proof(
                bname, build_dir=build_dir, install=install, root=repo_root, meta=meta,
                github_config=github_config,
            )
            row["local_report"] = report
            row["status"] = report.get("status", "OK")
            row["tool"] = report.get("tool_name", "")
            row["skip_reason"] = (report.get("extra") or {}).get("skip_reason", "")
            row["tool_log"] = (report.get("extra") or {}).get("tool_log", "")
            row["install_msg"] = (report.get("extra") or {}).get("install_msg", "")
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
        _, meta = _find_taxonomy_html(bname, taxonomy_root)

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
