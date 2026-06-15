"""Registry-driven branch naming and report paths (v2: full L5 slug names)."""

from __future__ import print_function

import os
import re
from datetime import datetime, timezone

from lib.registry import (
    load_registry,
    metric_by_slug,
    metric_entry,
    parse_metrics_filter,
    parse_techniques_arg,
    parse_types_arg,
    technique_by_code,
)

BRANCH_TYPES = ("Bug", "BugFX", "TCC", "CC")
FIXED_BRANCH_TYPES = BRANCH_TYPES
SUPPORTED_LANGUAGES = ("python", "java", "csharp", "javascript", "typescript", "c", "cpp")
ALL_METRICS = "all"
ALL_TECHNIQUES = "all"

# Legacy v1: SA_DOV_Bug_2.6
BRANCH_NAME_RE_V1 = re.compile(
    r"^(?P<tech>[A-Z][A-Z0-9]{1,5})_(?P<metric>[A-Z][A-Z0-9]{1,5})_"
    r"(?P<type>Bug|BugFX|TCC|CC)_(?P<version>[^_/\\]+)$"
)
BRANCH_NAME_RE = BRANCH_NAME_RE_V1  # backward compat

REPORT_TS_SUFFIX_RE = re.compile(r"_(\d{8}T\d{6}Z|\d{8}_\d{6})$")


def sanitize_version(version):
    return re.sub(r"[^A-Za-z0-9._-]", "_", str(version).strip())


def branch_name(technique_code, metric_code, branch_type="Bug", version="2.6", registry=None):
    """v2: SA_Decision-Outcome-Verification_Bug_2.6"""
    _, metric = metric_entry(technique_code, metric_code, registry)
    slug = metric.get("branch_slug") or metric_code
    return "%s_%s_%s_%s" % (
        technique_code.upper(),
        slug,
        branch_type,
        sanitize_version(version),
    )


def parse_branch_name(name, registry=None):
    """Parse v2 or legacy v1 branch folder names."""
    reg = registry or load_registry()
    m = BRANCH_NAME_RE_V1.match(name)
    if m:
        return m.groupdict()

    parts = name.split("_")
    if len(parts) < 4:
        return None
    tech = parts[0]
    version = parts[-1]
    branch_type = parts[-2]
    if branch_type not in BRANCH_TYPES:
        return None
    slug = parts[1] if len(parts) == 4 else "_".join(parts[1:-2])
    try:
        metric = metric_by_slug(tech, slug, reg)
    except KeyError:
        return None
    return {
        "tech": tech.upper(),
        "metric": metric["metric_code"],
        "type": branch_type,
        "version": version,
        "branch_slug": slug,
    }


def infer_from_branch_name(name, registry=None):
    parsed = parse_branch_name(name, registry)
    if not parsed:
        return None, None, None, None
    return parsed["tech"], parsed["metric"], parsed["type"], parsed["version"]


def branch_name_aliases(name, registry=None):
    """Return candidate branch folder names for S3/Git lookups (v2 first, then legacy v1)."""
    parsed = parse_branch_name(name, registry)
    if not parsed:
        return [name]
    tech = parsed["tech"]
    metric_code = parsed["metric"]
    branch_type = parsed["type"]
    version = parsed["version"]
    aliases = [name]
    v1 = "%s_%s_%s_%s" % (tech, metric_code, branch_type, version)
    if v1 not in aliases:
        aliases.append(v1)
    return aliases


def github_branch_url(branch_name, repository_match=None):
    repo = (repository_match or os.environ.get("REPOSITORY_MATCH", "")).strip()
    if not repo:
        return ""
    return "https://github.com/%s/tree/%s" % (repo, branch_name)


def report_output_dir(output_root=None, group_label=None):
    root = output_root or "taxonomy_reports"
    label = group_label or os.environ.get("REPORT_CLASSIFICATION", "Structural Analysis")
    return os.path.join(root, label)


def report_timestamp():
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def report_timestamp_notebook():
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def report_folder_name(branch_name, collected_at=None):
    ts = collected_at or report_timestamp()
    return "%s_%s" % (branch_name, ts)


def report_file_path(group_label, branch_name, collected_at=None):
    ts = collected_at or report_timestamp_notebook()
    folder = os.path.join(report_output_dir(group_label=group_label), branch_name)
    return os.path.join(folder, "%s_%s.html" % (branch_name, ts))


def branch_name_from_report_folder(folder_name):
    m = REPORT_TS_SUFFIX_RE.search(folder_name)
    return folder_name[:m.start()] if m else folder_name


def infer_metric_from_report_folder(folder_name, registry=None):
    base = branch_name_from_report_folder(folder_name)
    tech, metric, branch_type, _ = infer_from_branch_name(base, registry)
    if not tech:
        return None, None
    return metric, branch_type


def branches_for_selection(techniques="all", metrics="all", version="2.6", branch_types=None, registry=None):
    from lib.registry import iter_branches

    types = branch_types or FIXED_BRANCH_TYPES
    return [name for _, _, _, name in iter_branches(techniques, metrics, types, version, registry)]


def taxonomy_classification(technique_code, metric_code, registry=None):
    _, m = metric_entry(technique_code, metric_code, registry)
    return m["taxonomy_classification"]


def report_group_label(technique_code, registry=None):
    from lib.registry import technique_by_code
    return technique_by_code(technique_code, registry)["report_group_label"]


def _branch_display_fields(parsed, folder_name, path, registry=None):
    """Resolve human-readable technique/metric labels and v2 branch name."""
    reg = registry or load_registry()
    tech_code = parsed["tech"]
    metric_code = parsed["metric"]
    branch_type = parsed["type"]
    version = parsed["version"]
    try:
        tech = technique_by_code(tech_code, reg)
        _, metric = metric_entry(tech_code, metric_code, reg)
        technique = tech.get("l2") or tech.get("report_group_label") or tech_code
        metric_name = metric.get("l5_metric") or metric.get("branch_slug") or metric_code
        canonical_name = branch_name(tech_code, metric_code, branch_type, version, reg)
    except KeyError:
        technique = tech_code
        metric_name = parsed.get("branch_slug") or metric_code
        canonical_name = folder_name
    return {
        "branch_name": canonical_name,
        "folder_name": folder_name,
        "technique": technique,
        "metric": metric_name,
        "branch_type": branch_type,
        "version": version,
        "path": path,
    }


def scan_build_dir(build_dir="build", root=None, registry=None):
    """List branches present on disk under build/ with full technique/metric names."""
    repo = root or os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    build_path = os.path.join(repo, build_dir)
    rows = []
    if not os.path.isdir(build_path):
        return rows
    reg = registry or load_registry()
    for name in sorted(os.listdir(build_path)):
        path = os.path.join(build_path, name)
        if not os.path.isdir(path):
            continue
        parsed = parse_branch_name(name, reg)
        if parsed:
            rows.append(_branch_display_fields(parsed, name, path, reg))
        else:
            rows.append({
                "branch_name": name,
                "folder_name": name,
                "path": path,
                "technique": "?",
                "metric": "?",
                "branch_type": "?",
                "version": "?",
            })
    return rows


# --- backward-compatible SA aliases ---
def _sa_registry_rows(registry=None):
    reg = registry or load_registry()
    tech = next(t for t in reg["techniques"] if t["technique_code"] == "SA")
    rows = []
    for m in tech["metrics"]:
        rows.append((
            m["module_key"],
            m["metric_code"],
            m["taxonomy_classification"],
            m["l5_metric"],
            (m.get("tools") or {}).get("python", {}).get("primary", ""),
        ))
    return rows


def get_sa_metrics(registry=None):
    return _sa_registry_rows(registry)


def parse_metrics_arg(metrics_csv, technique_code="SA", registry=None):
    return parse_metrics_filter(metrics_csv, technique_code, registry)


def module_variant(module_key, target_module_key, branch_type):
    if module_key != target_module_key:
        return "stub"
    return {"Bug": "bug", "BugFX": "bugfx", "TCC": "tcc", "CC": "cc"}[branch_type]
