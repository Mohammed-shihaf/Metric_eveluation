"""Load and query config/metrics_registry.yaml."""

from __future__ import print_function

import os

try:
    import yaml
except ImportError:
    yaml = None

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REGISTRY_PATH = os.path.join(ROOT, "config", "metrics_registry.yaml")

_CACHE = None


def load_registry(path=None):
    global _CACHE
    path = path or REGISTRY_PATH
    if _CACHE is not None and path == REGISTRY_PATH:
        return _CACHE
    if yaml is None:
        raise RuntimeError("PyYAML required: pip install pyyaml")
    with open(path, encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if path == REGISTRY_PATH:
        _CACHE = data
    return data


def all_techniques(registry=None):
    reg = registry or load_registry()
    return reg["techniques"]


def technique_by_code(code, registry=None):
    code = code.upper()
    for tech in all_techniques(registry):
        if tech["technique_code"] == code:
            return tech
    raise KeyError("Unknown technique_code: %s" % code)


def metric_entry(technique_code, metric_code, registry=None):
    tech = technique_by_code(technique_code, registry)
    metric_code = metric_code.upper()
    for m in tech["metrics"]:
        if m["metric_code"] == metric_code:
            return tech, m
    raise KeyError("Unknown metric %s in technique %s" % (metric_code, technique_code))


def all_metric_entries(registry=None):
    reg = registry or load_registry()
    out = []
    for tech in reg["techniques"]:
        for m in tech["metrics"]:
            out.append((tech, m))
    return out


def parse_techniques_arg(value, registry=None):
    if not value or str(value).strip().lower() == "all":
        return [t["technique_code"] for t in all_techniques(registry)]
    codes = [c.strip().upper() for c in str(value).split(",") if c.strip()]
    known = {t["technique_code"] for t in all_techniques(registry)}
    bad = [c for c in codes if c not in known]
    if bad:
        raise ValueError("Unknown technique(s): %s" % bad)
    return codes


def parse_metrics_filter(value, technique_code, registry=None):
    tech = technique_by_code(technique_code, registry)
    known = [m["metric_code"] for m in tech["metrics"]]
    if not value or str(value).strip().lower() == "all":
        return list(known)
    codes = [c.strip().upper() for c in str(value).split(",") if c.strip()]
    bad = [c for c in codes if c not in known]
    if bad:
        raise ValueError("Unknown metric(s) for %s: %s" % (technique_code, bad))
    return codes


def parse_types_arg(value, registry=None):
    reg = registry or load_registry()
    allowed = reg.get("branch_types", ["Bug", "BugFX", "TCC", "CC"])
    if not value:
        return list(allowed)
    if isinstance(value, (list, tuple)):
        types = list(value)
    else:
        types = [t.strip() for t in str(value).split(",") if t.strip()]
    bad = [t for t in types if t not in allowed]
    if bad:
        raise ValueError("Unknown branch type(s): %s" % bad)
    return types


def iter_branches(techniques="all", metrics="all", types=None, version="2.6", registry=None):
    """Yield (technique_code, metric_code, branch_type, branch_name) tuples."""
    from lib.metrics import branch_name

    reg = registry or load_registry()
    types = parse_types_arg(types, reg)
    for tech_code in parse_techniques_arg(techniques, reg):
        for metric_code in parse_metrics_filter(metrics, tech_code, reg):
            for bt in types:
                yield tech_code, metric_code, bt, branch_name(tech_code, metric_code, bt, version)


def package_name(technique_code):
    return technique_code.lower()
