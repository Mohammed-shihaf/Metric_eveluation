"""Shared filter helpers for CLI and Streamlit UI."""

from __future__ import print_function

from lib.registry import all_techniques, iter_branches, load_registry, parse_metrics_filter, parse_techniques_arg, parse_types_arg


def selection_summary(techniques="all", metrics="all", types=None, version="2.6", registry=None):
    branches = list(iter_branches(techniques, metrics, types, version, registry))
    return {
        "techniques": parse_techniques_arg(techniques, registry),
        "metrics_filter": metrics,
        "types": parse_types_arg(types, registry),
        "version": version,
        "branch_count": len(branches),
        "branches": [b[3] for b in branches],
    }


def technique_label(tech):
    """Unique sidebar label: technique_code + L3 name (per Excel mapping)."""
    code = tech.get("technique_code", "")
    l3 = (tech.get("l3") or "").strip()
    l2 = (tech.get("l2") or "").strip()
    name = l3 or l2 or code
    return "%s — %s" % (code, name)


def technique_options(registry=None):
    reg = registry or load_registry()
    return [(t["technique_code"], technique_label(t)) for t in all_techniques(reg)]


def metric_options(technique_code, registry=None):
    reg = registry or load_registry()
    return parse_metrics_filter("all", technique_code, reg)


def qualified_metric_choices(technique_codes, registry=None):
    """TECH:METRIC tokens for sidebar multiselect."""
    reg = registry or load_registry()
    choices = []
    for tc in technique_codes or []:
        for m in metric_options(tc, reg):
            choices.append("%s:%s" % (tc, m))
    return sorted(set(choices))


def full_scope_branch_count(registry=None, version="2.6"):
    reg = registry or load_registry()
    types = branch_type_options(reg)
    return len(list(iter_branches("all", "all", types, version, reg)))


def branch_type_options(registry=None):
    reg = registry or load_registry()
    return parse_types_arg(None, reg)


def csv_from_list(items):
    if not items:
        return "all"
    if isinstance(items, str):
        return items
    return ",".join(items)
