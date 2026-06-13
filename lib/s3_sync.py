"""Download platform tool reports from S3 aligned with taxonomy runs."""

from __future__ import print_function

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

COVERAGE_REL = "coverage-py/0/coverage.json"


def _s3_config():
    return {
        "bucket": os.environ.get("S3_BUCKET", "us2-qa-testable").strip(),
        "search_prefix": os.environ.get("S3_SEARCH_PREFIX", "qa-op/cell-001/").strip().rstrip("/") + "/",
        "cell_batch_id": os.environ.get("S3_CELL_BATCH_ID", "").strip(),
        "download_root": Path(os.environ.get("S3_DOWNLOAD_ROOT", str(ROOT / "s3_downloads"))),
    }


def _branch_allowed(branch):
    prefix = os.environ.get("S3_SYNC_BRANCH_PREFIX", "").strip()
    if prefix and not branch.startswith(prefix):
        return False
    allowlist = os.environ.get("S3_SYNC_BRANCHES", "").strip()
    if allowlist:
        allowed = frozenset(b.strip() for b in allowlist.split(",") if b.strip())
        return branch in allowed
    return True


def _s3_client():
    import boto3

    key = os.environ.get("AWS_ACCESS_KEY_ID", "").strip()
    secret = os.environ.get("AWS_SECRET_ACCESS_KEY", "").strip()
    token = os.environ.get("AWS_SESSION_TOKEN", "").strip()
    region = os.environ.get("AWS_DEFAULT_REGION", "us-east-2").strip()
    if key and secret:
        kwargs = {
            "aws_access_key_id": key,
            "aws_secret_access_key": secret,
            "region_name": region,
        }
        if token:
            kwargs["aws_session_token"] = token
        return boto3.client("s3", **kwargs)
    return boto3.client("s3")


def _normalize_prefix(prefix):
    return prefix if prefix.endswith("/") else prefix + "/"


def find_s3_run_prefix(bucket, search_prefix, branch, commit_sha, run_id, cell_batch_id=None):
    """Locate S3 key prefix ending at .../<branch>/<commit>/<run_id>/."""
    s3 = _s3_client()
    search_prefix = _normalize_prefix(search_prefix)
    needles = [
        "%s/%s/%s/" % (branch, commit_sha, run_id),
        "%s/%s/" % (branch, commit_sha),
    ]
    best = None
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=search_prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if branch not in key or commit_sha not in key:
                continue
            if cell_batch_id and cell_batch_id not in key:
                continue
            for needle in needles:
                if needle not in key:
                    continue
                idx = key.index(needle) + len(needle)
                prefix = key[:idx]
                parts = prefix.rstrip("/").split("/")
                if len(parts) < 5:
                    continue
                run_uuid = parts[-1]
                commit = parts[-2]
                br = parts[-3]
                platform_run_uuid = parts[-4]
                cell_id = parts[-5]
                if br != branch or commit != commit_sha:
                    continue
                if run_id and run_uuid != run_id and needle.endswith("%s/" % run_id):
                    continue
                candidate = (prefix, [cell_id, platform_run_uuid, br, commit, run_uuid])
                if best is None or len(prefix) > len(best[0]):
                    best = candidate
    return best


def download_s3_prefix(bucket, s3_prefix, local_dir):
    s3 = _s3_client()
    local_dir = Path(local_dir)
    local_dir.mkdir(parents=True, exist_ok=True)
    paginator = s3.get_paginator("list_objects_v2")
    count = 0
    for page in paginator.paginate(Bucket=bucket, Prefix=s3_prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key.endswith("/"):
                continue
            rel = key[len(s3_prefix):].lstrip("/")
            dest = local_dir / rel.replace("/", os.sep)
            dest.parent.mkdir(parents=True, exist_ok=True)
            s3.download_file(bucket, key, str(dest))
            count += 1
    return count


def validate_coverage_json(tool_root):
    path = Path(tool_root) / COVERAGE_REL.replace("/", os.sep)
    if not path.is_file():
        return "MISSING", {"path": str(path), "num_statements": 0}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        return "EMPTY", {"path": str(path), "error": str(exc), "num_statements": 0}
    totals = data.get("totals") or {}
    statements = int(totals.get("num_statements") or 0)
    covered = int(totals.get("covered_lines") or 0)
    detail = {
        "path": str(path),
        "num_statements": statements,
        "covered_lines": covered,
        "coverage_pct": round(100.0 * covered / statements, 1) if statements else 0.0,
    }
    if statements <= 0:
        return "EMPTY", detail
    return "OK", detail


def local_tool_root(download_root, parts):
    return Path(download_root).joinpath(*parts)


def sync_run(branch, commit_sha, run_id, taxonomy_html_path="", cell_batch_id=None, dry_run=False):
    cfg = _s3_config()
    bucket = cfg["bucket"]
    search_prefix = cfg["search_prefix"]
    cell_batch_id = cell_batch_id or cfg["cell_batch_id"]
    download_root = cfg["download_root"]

    if not _branch_allowed(branch):
        return {
            "branch": branch,
            "status": "SKIPPED",
            "reason": "branch not in S3 sync filter",
        }

    if not commit_sha or not run_id:
        return {
            "branch": branch,
            "status": "MISSING",
            "reason": "commit_sha and run_id required",
            "taxonomy_html_path": taxonomy_html_path,
        }

    found = find_s3_run_prefix(
        bucket, search_prefix, branch, commit_sha, run_id, cell_batch_id or None)
    if not found:
        return {
            "branch": branch,
            "commit_sha": commit_sha,
            "run_id": run_id,
            "status": "MISSING",
            "reason": "no S3 prefix matched",
            "taxonomy_html_path": taxonomy_html_path,
            "s3_bucket": bucket,
            "s3_search_prefix": search_prefix,
        }

    s3_prefix, parts = found
    local_root = local_tool_root(download_root, parts)
    summary = {
        "branch": branch,
        "commit_sha": commit_sha,
        "run_id": run_id,
        "taxonomy_html_path": taxonomy_html_path,
        "s3_bucket": bucket,
        "s3_prefix": s3_prefix,
        "local_path": str(local_root),
        "cell_batch_id": parts[0],
        "platform_run_uuid": parts[1],
    }

    if dry_run:
        summary["status"] = "DRY_RUN"
        return summary

    try:
        n_files = download_s3_prefix(bucket, s3_prefix, local_root)
        cov_status, cov_detail = validate_coverage_json(local_root)
        summary["files_downloaded"] = n_files
        summary["coverage"] = cov_detail
        summary["coverage_status"] = cov_status
        if n_files <= 0:
            summary["status"] = "ERROR"
        else:
            summary["status"] = "OK"
            if cov_status != "OK":
                summary["coverage_note"] = "bundle downloaded; coverage-py optional or empty"
    except Exception as exc:
        summary["status"] = "ERROR"
        summary["error"] = str(exc)

    return summary


def sync_from_taxonomy_meta(meta, dry_run=False):
    return sync_run(
        branch=meta.get("branch", ""),
        commit_sha=meta.get("commit_sha", ""),
        run_id=meta.get("run_id", ""),
        taxonomy_html_path=meta.get("html_path", ""),
        dry_run=dry_run,
    )


def update_manifest(manifest_path, sync_summaries):
    manifest_path = Path(manifest_path)
    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    else:
        manifest = {"runs": []}

    by_branch = {r.get("branch"): r for r in manifest.get("runs", []) if r.get("branch")}
    for sync in sync_summaries:
        branch = sync.get("branch")
        if not branch:
            continue
        row = by_branch.get(branch, {"branch": branch})
        for key in ("report_folder", "status", "gate_score", "taxonomy_html_path"):
            if key in sync and sync.get(key):
                row[key] = sync[key]
        row["commit_sha"] = sync.get("commit_sha") or row.get("commit_sha")
        row["run_id"] = sync.get("run_id") or row.get("run_id")
        row["s3_sync"] = {
            "status": sync.get("status"),
            "local_path": sync.get("local_path"),
            "s3_prefix": sync.get("s3_prefix"),
            "coverage_status": sync.get("coverage_status"),
            "coverage": sync.get("coverage"),
            "files_downloaded": sync.get("files_downloaded"),
        }
        if sync.get("taxonomy_html_path"):
            row["taxonomy_html_path"] = sync["taxonomy_html_path"]
        by_branch[branch] = row

    manifest["runs"] = [by_branch[b] for b in sorted(by_branch)]
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
    return manifest


def backfill_missing(classification_dir, dry_run=False):
    from lib.taxonomy_meta import latest_taxonomy_by_branch

    classification_dir = Path(classification_dir)
    download_root = _s3_config()["download_root"]
    summaries = []

    for branch, meta in latest_taxonomy_by_branch(classification_dir).items():
        commit = meta.get("commit_sha", "")
        run_id = meta.get("run_id", "")
        existing = None
        if commit and run_id:
            for cell_dir in download_root.glob("*"):
                if not cell_dir.is_dir():
                    continue
                for plat_dir in cell_dir.glob("*"):
                    candidate = plat_dir / branch / commit / run_id
                    if candidate.is_dir() and any(candidate.iterdir()):
                        existing = candidate
                        break
        if existing:
            cov_status, cov_detail = validate_coverage_json(existing)
            summaries.append({
                "branch": branch,
                "commit_sha": commit,
                "run_id": run_id,
                "status": "OK",
                "local_path": str(existing),
                "coverage_status": cov_status,
                "coverage": cov_detail,
                "taxonomy_html_path": meta.get("html_path", ""),
                "skipped": "already present",
            })
            continue
        summaries.append(sync_from_taxonomy_meta(meta, dry_run=dry_run))

    manifest_path = classification_dir / "manifest.json"
    if not dry_run:
        update_manifest(manifest_path, summaries)
    return summaries
