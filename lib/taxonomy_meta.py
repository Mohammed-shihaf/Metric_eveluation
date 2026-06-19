"""Extract run metadata from taxonomy reports and manifest."""

from __future__ import print_function

import json
import re
from pathlib import Path

from lib.metrics import branch_name_from_report_folder, classification_dir_for_branch

_HTML_FIELDS = (
    ("branch", r"Branch name</th><td>([^<]+)"),
    ("commit_sha", r"Commit ID</th><td>([^<]+)"),
    ("run_id", r"Run ID</th><td>([^<]+)"),
    ("repo", r"Repo name</th><td>([^<]+)"),
)


def parse_taxonomy_html(html_path):
    """Return dict with branch, commit_sha, run_id, repo, html_path."""
    path = Path(html_path)
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8", errors="replace")
    meta = {"html_path": str(path)}
    for key, pattern in _HTML_FIELDS:
        m = re.search(pattern, text)
        if m:
            meta[key] = m.group(1).strip()
    folder = path.parent.name
    if "branch" not in meta:
        meta["branch"] = branch_name_from_report_folder(folder)
    if "run_id" not in meta:
        m = re.search(r"taxonomy-gate-([0-9a-f-]+)\.html", path.name, re.I)
        if m:
            meta["run_id"] = m.group(1)
    return meta


def _report_folders(classification_dir):
    """Saved run folders under a classification dir (HTML and/or JSON artifacts)."""
    root = Path(classification_dir)
    if not root.is_dir():
        return []
    folders = []
    for folder in sorted(root.iterdir()):
        if not folder.is_dir():
            continue
        if (folder / "taxonomy-gate.json").is_file() or any(folder.glob("taxonomy-gate*.html")):
            folders.append(folder)
    return folders


def report_dir_from_meta(meta, classification_dir=None):
    """Resolve on-disk report folder from a meta dict."""
    for key in ("report_dir",):
        path = meta.get(key, "")
        if path and Path(path).is_dir():
            return Path(path)
    html_path = meta.get("html_path", "")
    if html_path:
        path = Path(html_path)
        if path.is_dir():
            return path
        if path.is_file():
            return path.parent
    report_folder = meta.get("report_folder", "")
    if report_folder and classification_dir:
        candidate = Path(classification_dir) / report_folder
        if candidate.is_dir():
            return candidate
    return None


def meta_from_report_folder(folder_path):
    """Build metadata from a saved taxonomy report folder."""
    folder = Path(folder_path)
    if not folder.is_dir():
        return {}
    meta = {
        "report_dir": str(folder),
        "report_folder": folder.name,
        "branch": branch_name_from_report_folder(folder.name),
    }
    run_id_file = folder / "run_id.txt"
    if run_id_file.is_file():
        meta["run_id"] = run_id_file.read_text(encoding="utf-8").strip()
    summary_path = folder / "run_summary.json"
    if summary_path.is_file():
        try:
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            if summary.get("commit_sha"):
                meta["commit_sha"] = summary["commit_sha"]
            if summary.get("run_id") and not meta.get("run_id"):
                meta["run_id"] = summary["run_id"]
            if summary.get("branch_name"):
                meta["branch"] = summary["branch_name"]
        except Exception:
            pass
    for html in sorted(folder.glob("taxonomy-gate*.html")):
        meta["html_path"] = str(html)
        parsed = parse_taxonomy_html(html)
        for key, value in parsed.items():
            if value and not meta.get(key):
                meta[key] = value
        break
    ts = folder.name.rsplit("_", 1)[-1] if "_" in folder.name else ""
    meta["_folder_ts"] = ts
    return meta


def latest_taxonomy_by_branch(classification_dir):
    """Map branch -> latest metadata dict from saved taxonomy report folders."""
    by_branch = {}
    for folder in _report_folders(classification_dir):
        meta = meta_from_report_folder(folder)
        branch = meta.get("branch")
        if not branch:
            continue
        prev = by_branch.get(branch)
        if prev is None or meta.get("_folder_ts", "") >= prev.get("_folder_ts", ""):
            by_branch[branch] = meta
    return by_branch


def enrich_taxonomy_meta(meta, manifest_run=None, branch_name=None, classification_dir=None):
    """Fill branch/commit/run_id from manifest and on-disk report folder."""
    enriched = dict(meta or {})
    if branch_name and not enriched.get("branch"):
        enriched["branch"] = branch_name
    if manifest_run:
        for key in ("commit_sha", "run_id", "report_folder"):
            if manifest_run.get(key) and not enriched.get(key):
                enriched[key] = manifest_run[key]
        html_hint = manifest_run.get("taxonomy_html_path") or manifest_run.get("html_path")
        if html_hint and not enriched.get("html_path"):
            enriched["html_path"] = html_hint
    report_dir = report_dir_from_meta(enriched, classification_dir=classification_dir)
    if report_dir:
        folder_meta = meta_from_report_folder(report_dir)
        for key in ("commit_sha", "run_id", "branch", "html_path", "report_folder", "report_dir"):
            if folder_meta.get(key) and not enriched.get(key):
                enriched[key] = folder_meta[key]
        if not enriched.get("_folder_ts"):
            enriched["_folder_ts"] = folder_meta.get("_folder_ts", "")
    return enriched


def load_manifest_runs(classification_dir):
    manifest_path = Path(classification_dir) / "manifest.json"
    if not manifest_path.is_file():
        return []
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    return data.get("runs", [])


def _meta_with_usable_report(meta, classification_dir=None):
    """True when meta points at taxonomy HTML or taxonomy-gate.json."""
    html_path = meta.get("html_path", "")
    if html_path and Path(html_path).is_file():
        return True
    report_dir = report_dir_from_meta(meta, classification_dir=classification_dir)
    return bool(report_dir and (report_dir / "taxonomy-gate.json").is_file())


def resolve_branch_taxonomy_meta(
    branch_name,
    taxonomy_root="taxonomy_reports",
    root=None,
    registry=None,
):
    """Return (meta, source_class_dir) for a branch, with cross-folder fallback.

    Looks in the canonical technique classification dir first, then scans every
    subdir under taxonomy_root for legacy misfiled reports.
    """
    from lib.registry import load_registry

    reg = registry or load_registry()
    repo_root = Path(root) if root else Path(__file__).resolve().parents[1]
    tax_root = repo_root / taxonomy_root
    canonical_dir = classification_dir_for_branch(
        branch_name, taxonomy_root, root=str(repo_root), registry=reg,
    )

    def _meta_from_dir(class_dir):
        if not class_dir or not class_dir.is_dir():
            return {}
        return latest_taxonomy_by_branch(class_dir).get(branch_name, {})

    best_meta = _meta_from_dir(canonical_dir)
    best_dir = canonical_dir

    if tax_root.is_dir():
        for alt_dir in sorted(tax_root.iterdir()):
            if not alt_dir.is_dir():
                continue
            if alt_dir == canonical_dir:
                continue
            alt_meta = _meta_from_dir(alt_dir)
            if not _meta_with_usable_report(alt_meta, classification_dir=alt_dir):
                continue
            if not _meta_with_usable_report(best_meta, classification_dir=best_dir):
                best_meta, best_dir = alt_meta, alt_dir
            elif alt_meta.get("_folder_ts", "") >= best_meta.get("_folder_ts", ""):
                best_meta, best_dir = alt_meta, alt_dir

    return best_meta, best_dir


def load_run_summary_from_meta(meta, classification_dir=None):
    """Load run_summary.json from the report folder when present."""
    report_dir = report_dir_from_meta(meta, classification_dir=classification_dir)
    if not report_dir:
        return {}
    summary_path = report_dir / "run_summary.json"
    if not summary_path.is_file():
        return {}
    try:
        return json.loads(summary_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def load_taxonomy_gate_json(meta, classification_dir=None):
    """Load taxonomy-gate.json from the report folder when available."""
    report_dir = report_dir_from_meta(meta, classification_dir=classification_dir)
    if not report_dir:
        return {}
    gate_path = report_dir / "taxonomy-gate.json"
    if not gate_path.is_file():
        return {}
    try:
        return json.loads(gate_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def metric_expects_s3_artifacts(branch_name, registry=None):
    """False when the metric is taxonomy-derived and does not publish platform S3 bundles."""
    from lib.metrics import infer_from_branch_name
    from lib.registry import load_registry, metric_entry

    reg = registry or load_registry()
    tech, metric, _, _ = infer_from_branch_name(branch_name, reg)
    if not tech or not metric:
        return True
    try:
        _, entry = metric_entry(tech, metric, reg)
    except KeyError:
        return True
    return bool(entry.get("emitted_directly", True))


def failing_sections(taxonomy_json, score_threshold=0.0):
    """Return classifications/techniques with zero or missing normalized scores."""
    rows = []
    if not taxonomy_json:
        return rows
    for tt in taxonomy_json.get("weighted_breakdown") or []:
        testing_type = tt.get("testing_type", "")
        for technique in tt.get("techniques") or []:
            tech_name = technique.get("technique", "")
            for cls in technique.get("classifications") or []:
                score = cls.get("normalized_score")
                if score is None or float(score) <= score_threshold:
                    rows.append({
                        "testing_type": testing_type,
                        "technique": tech_name,
                        "classification": cls.get("classification", ""),
                        "normalized_score": score,
                    })
    return rows


def branch_taxonomy_scope(branch_name, registry=None):
    """Registry taxonomy labels that apply to one generated branch."""
    from lib.metrics import infer_from_branch_name
    from lib.registry import metric_entry

    tech, metric, _, _ = infer_from_branch_name(branch_name, registry)
    if not tech or not metric:
        return set()
    try:
        _, entry = metric_entry(tech, metric, registry)
    except KeyError:
        return set()
    labels = {
        entry.get("taxonomy_classification"),
        entry.get("l4_classification"),
        entry.get("l5_metric"),
    }
    return {label.strip() for label in labels if label and str(label).strip()}


def failing_sections_for_branch(
    taxonomy_json,
    branch_name,
    registry=None,
    score_threshold=0.0,
):
    """Like failing_sections, but only for classifications in this branch's metric scope."""
    scope = branch_taxonomy_scope(branch_name, registry)
    if not scope:
        return failing_sections(taxonomy_json, score_threshold=score_threshold)
    rows = []
    if not taxonomy_json:
        return rows
    for tt in taxonomy_json.get("weighted_breakdown") or []:
        testing_type = tt.get("testing_type", "")
        for technique in tt.get("techniques") or []:
            tech_name = technique.get("technique", "")
            for cls in technique.get("classifications") or []:
                name = cls.get("classification", "")
                if name not in scope:
                    continue
                score = cls.get("normalized_score")
                if score is None or float(score) <= score_threshold:
                    rows.append({
                        "testing_type": testing_type,
                        "technique": tech_name,
                        "classification": name,
                        "normalized_score": score,
                    })
    return rows
