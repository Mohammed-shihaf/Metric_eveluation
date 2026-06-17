"""Shared generation constants and helpers for all languages."""

from __future__ import print_function

MIN_LOC = 2500
BASE_STRENGTH_FLOOR = 4
DEFAULT_N_FUNCTIONS = 72
VARIANT_MAP = {"Bug": "bug", "BugFX": "bugfx", "TCC": "tcc", "CC": "cc"}


def effective_strength(strength):
    try:
        s = int(strength or 0)
    except (TypeError, ValueError):
        s = 0
    return max(s, BASE_STRENGTH_FLOOR)


def scaled_n_functions(base_n, strength):
    return min(180, base_n + effective_strength(strength) * 4)


def scaled_test_count(n_fn, branch_type, strength):
    if branch_type == "Bug":
        return 1
    base = n_fn if branch_type != "Bug" else 1
    if strength > 0:
        return min(n_fn, 18 + effective_strength(strength) * 8)
    return max(base, 16)


def variant_marker(variant, idx, strength):
    if variant == "bug":
        return "escalated-%d" % idx
    if variant == "bugfx":
        return "resolved-%d" % idx
    if variant == "tcc":
        return ("disabled-%d" % idx) if idx % 2 else ("audit-strict-%d" % idx)
    return "neutral-%d" % idx
