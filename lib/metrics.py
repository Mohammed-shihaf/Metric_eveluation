"""Registry-driven branch naming and report paths."""

from __future__ import print_function

import os
import re
from datetime import datetime, timezone

from lib.registry import (
    all_metric_entries,
    load_registry,
    metric_entry,
    parse_metrics_filter,
    parse_techniques_arg,
    parse_types_arg,
)

BRANCH_TYPES = ("Bug", "BugFX", "TCC", "CC")
FIXED_BRANCH_TYPES = BRANCH_TYPES
SUPPORTED_LANGUAGES = ("python", "java", "csharp", "javascript", "typescript", "c", "cpp")
ALL_METRICS = "all"
ALL_TECHNIQUES = "all"

BRANCH_NAME_RE = re.compile(
    r"^(?P<tech>[A-Z][A-Z0-9]{1,5})_(?P<metric>[A-Z][A-Z0-9]{1,5})_"
    r"(?P<type>Bug|BugFX|TCC|CC)_(?P<version>[^_/\\]+)$"
)

REPORT_TS_SUFFIX_RE = re.compile(r"_(\d{8}T\d{6}Z|\d{8}_\d{6})$")


def sanitize_version(version):
    return re.sub(r"[^A-Za-z0-9._-]", "_", str(version).strip())


def branch_name(technique_code, metric_code, branch_type="Bug", version="2.6"):
    return "%s_%s_%s_%s" % (
        technique_code.upper(),
        metric_code.upper(),
        branch_type,
        sanitize_version(version),
    )


def parse_branch_name(name):
    m = BRANCH_NAME_RE.match(name)
    if not m:
        return None
    return m.groupdict()


def infer_from_branch_name(name):
    parsed = parse_branch_name(name)
    if not parsed:
        return None, None, None, None
    return parsed["tech"], parsed["metric"], parsed["type"], parsed["version"]


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
    """taxonomy_reports/<L2>/<BRANCH>/<BRANCH>_<YYYYMMDD_HHMMSS>.html"""
    ts = collected_at or report_timestamp_notebook()
    folder = os.path.join(report_output_dir(group_label=group_label), branch_name)
    return os.path.join(folder, "%s_%s.html" % (branch_name, ts))


def branch_name_from_report_folder(folder_name):
    m = REPORT_TS_SUFFIX_RE.search(folder_name)
    return folder_name[:m.start()] if m else folder_name


def infer_metric_from_report_folder(folder_name):
    """Return (metric_code, branch_type) from a report folder name."""
    base = branch_name_from_report_folder(folder_name)
    tech, metric, branch_type, _ = infer_from_branch_name(base)
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


SA_METRICS = property(lambda self: None)  # placeholder; use get_sa_metrics() below


def get_sa_metrics(registry=None):
    return _sa_registry_rows(registry)


METRIC_ABBREVS = None  # set on first access


def _sa_abbrevs(registry=None):
    return [r[1] for r in _sa_registry_rows(registry)]


def parse_metrics_arg(metrics_csv, technique_code="SA", registry=None):
    return parse_metrics_filter(metrics_csv, technique_code, registry)


def module_variant(module_key, target_module_key, branch_type):
    if module_key != target_module_key:
        return "stub"
    return {"Bug": "bug", "BugFX": "bugfx", "TCC": "tcc", "CC": "cc"}[branch_type]
