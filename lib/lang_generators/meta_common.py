"""Shared metadata and config helpers for multi-language generators."""

from __future__ import print_function

import json

from lib.metrics import branch_name as metrics_branch_name


def gen_meta(strength, technique_code, metric_code, branch_type, version, language, runtime, n_fn, loc, bname):
    return json.dumps(
        {
            "strength": strength,
            "technique": technique_code,
            "metric": metric_code,
            "branch_type": branch_type,
            "version": version,
            "language": language,
            "runtime": runtime,
            "n_functions": n_fn,
            "loc": loc,
            "branch_name": bname,
        },
        indent=2,
    ) + "\n"


def config_fields(tech, metric, branch_type, version, language, runtime, lang_tools=None):
    """Common config key/value pairs for all languages."""
    lang_tools = lang_tools or {}
    return {
        "language": language,
        "runtime": runtime,
        "version": version,
        "branch_type": branch_type,
        "tech": tech["technique_code"],
        "metric": metric["metric_code"],
        "metric_name": metric["l5_metric"],
        "l2": tech["l2"],
        "l3": tech["l3"],
        "primary_tool": lang_tools.get("primary") or "",
    }


def branch_label(technique_code, metric_code, branch_type, version):
    return metrics_branch_name(technique_code, metric_code, branch_type, version)


def count_loc_files(files, extensions, prefixes):
    total = 0
    for path, content in files.items():
        if path == ".gen_meta.json":
            continue
        if extensions and not any(path.endswith(ext) for ext in extensions):
            continue
        if prefixes and not any(
            path.startswith(p) or ("/%s/" % p) in path.replace("\\", "/") or path == p
            for p in prefixes
        ):
            continue
        total += content.count("\n") + (0 if content.endswith("\n") else 1)
    return total
