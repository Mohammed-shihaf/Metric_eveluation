"""Registry-driven branch validation."""

from __future__ import print_function

import os
import re

from lib.metrics import BRANCH_NAME_RE, branch_name, parse_branch_name, sanitize_version
from lib.registry import iter_branches, metric_entry, package_name, technique_by_code

try:
    from lib.sa_validate import (
        TYPE_ASSERTERS as SA_TYPE_ASSERTERS,
        BranchValidationError,
        assert_bug_branch as sa_assert_bug,
        assert_bugfx_branch as sa_assert_bugfx,
        assert_cc_branch as sa_assert_cc,
        assert_tcc_branch as sa_assert_tcc,
    )
except ImportError:
    BranchValidationError = AssertionError
    SA_TYPE_ASSERTERS = {}

TCC_CONFIG_FILES = (".coveragerc", "setup.cfg", "pytest.ini", ".testmondata.ini", ".eslintrc.json", "jscpd.json")
STUB_MIN_LINES = 25
STUB_MAX_LINES = 70
FORBIDDEN_MARKERS = ("TOOL_MODE", "-tcc-", "fallback-cc-", "if False:", "phantom")
FULL_TEST_MIN = {"DOV": 12, "TDI": 1, "QRA": 1}


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _line_count(path):
    return len(_read(path).splitlines())


def _count_loc(root, pkg):
    total = 0
    for dirpath, _, files in os.walk(root):
        for fn in files:
            if not fn.endswith(".py"):
                continue
            rel = os.path.relpath(os.path.join(dirpath, fn), root).replace("\\", "/")
            if rel == "main.py" or rel.startswith("%s/" % pkg) or rel.startswith("tests/"):
                total += _line_count(os.path.join(dirpath, fn))
    return total


def _count_tests(root):
    tests = os.path.join(root, "tests")
    if not os.path.isdir(tests):
        return 0, []
    total, files = 0, []
    for fn in os.listdir(tests):
        if not fn.endswith(".py") or fn == "__init__.py":
            continue
        n = len(re.findall(r"^\s+def test_", _read(os.path.join(tests, fn)), re.M))
        total += n
        files.append((fn, n))
    return total, files


def _assert_no_forbidden(root):
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            if not fn.endswith(".py"):
                continue
            text = _read(os.path.join(dirpath, fn))
            for marker in FORBIDDEN_MARKERS:
                assert marker not in text, "forbidden %r in %s" % (
                    marker, os.path.relpath(os.path.join(dirpath, fn), root))


def _parse_config(root, pkg):
    path = os.path.join(root, pkg, "config.py")
    assert os.path.isfile(path), "missing %s/config.py" % pkg
    text = _read(path)
    out = {}
    for key in ("BRANCH_TYPE", "TARGET_METRIC_ABBREV", "TARGET_TECHNIQUE", "PYTHON_VERSION", "LANGUAGE"):
        m = re.search(r"^%s\s*=\s*'([^']+)'" % key, text, re.M)
        if m:
            out[key] = m.group(1)
    return out


def _assert_generic(root, technique_code, metric_code, branch_type, version, language):
    parsed = parse_branch_name(os.path.basename(root))
    assert parsed, "cannot parse folder name: %s" % root
    assert parsed["tech"] == technique_code.upper()
    assert parsed["metric"] == metric_code.upper()
    assert parsed["type"] == branch_type
    assert parsed["version"] == sanitize_version(version)

    tech, metric = metric_entry(technique_code, metric_code)
    pkg = package_name(technique_code)
    cfg = _parse_config(root, pkg)
    assert cfg.get("BRANCH_TYPE") == branch_type
    assert cfg.get("TARGET_METRIC_ABBREV") == metric_code.upper()
    assert cfg.get("TARGET_TECHNIQUE") == technique_code.upper()
    if language:
        assert cfg.get("LANGUAGE") == language

    target_path = os.path.join(root, pkg, "%s.py" % metric["module_key"])
    assert os.path.isfile(target_path)
    target_src = _read(target_path)

    for m in tech["metrics"]:
        path = os.path.join(root, pkg, "%s.py" % m["module_key"])
        assert os.path.isfile(path)
        if m["metric_code"] != metric_code.upper():
            lines = _line_count(path)
            assert STUB_MIN_LINES <= lines <= STUB_MAX_LINES, "stub %s lines=%d" % (m["module_key"], lines)

    _assert_no_forbidden(root)
    test_count, test_files = _count_tests(root)

    if branch_type == "Bug":
        assert "escalated-" in target_src
        for name in TCC_CONFIG_FILES:
            assert not os.path.isfile(os.path.join(root, name))
        assert test_count <= 2, "Bug expects partial tests, got %d %s" % (test_count, test_files)
    elif branch_type == "BugFX":
        assert "escalated-" not in target_src
        for name in TCC_CONFIG_FILES:
            assert not os.path.isfile(os.path.join(root, name))
        assert test_count >= FULL_TEST_MIN.get(metric_code.upper(), 2)
    elif branch_type == "TCC":
        assert "disabled-" in target_src or "audit-strict-" in target_src
        assert any(os.path.isfile(os.path.join(root, n)) for n in TCC_CONFIG_FILES)
        assert test_count >= FULL_TEST_MIN.get(metric_code.upper(), 2)
    else:
        assert "neutral-" in target_src or "OUTCOME_LOOKUP" in target_src
        assert "escalated-" not in target_src
        for name in TCC_CONFIG_FILES:
            assert not os.path.isfile(os.path.join(root, name))
        assert test_count >= FULL_TEST_MIN.get(metric_code.upper(), 12)

    loc = _count_loc(root, pkg)
    assert loc >= 1000, "LOC %d < 1000" % loc
    return loc


def validate_branch(root, technique_code=None, metric_code=None, branch_type=None,
                    version="2.6", language="python"):
    folder = os.path.basename(os.path.normpath(root))
    parsed = parse_branch_name(folder)
    if not parsed:
        raise BranchValidationError("cannot parse branch folder: %s" % folder)
    technique_code = (technique_code or parsed["tech"]).upper()
    metric_code = (metric_code or parsed["metric"]).upper()
    branch_type = branch_type or parsed["type"]
    version = parsed["version"] if version == "2.6" else sanitize_version(version)

    if technique_code == "SA" and language == "python":
        fn = SA_TYPE_ASSERTERS.get(branch_type)
        if fn:
            try:
                fn(root, metric_code, version, language)
            except AssertionError as exc:
                raise BranchValidationError("%s: %s" % (folder, exc)) from exc
            return folder, branch_type, _count_loc(root, "sa")

    try:
        loc = _assert_generic(root, technique_code, metric_code, branch_type, version, language)
    except AssertionError as exc:
        raise BranchValidationError("%s: %s" % (folder, exc)) from exc
    return folder, branch_type, loc


def validate_build_report(techniques="all", metrics="all", types=None, version="2.6",
                          language="python", build_dir="build", root=None):
    """Validate all matching branches; return rows with PASS/FAIL/MISSING (no raise)."""
    repo_root = root or os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    rows = []
    for tech, metric, bt, bname in iter_branches(techniques, metrics, types, version):
        path = os.path.join(repo_root, build_dir, bname)
        rel_path = os.path.join(build_dir, bname)
        if not os.path.isdir(path):
            rows.append((bname, tech, metric, bt, 0, "MISSING", rel_path, "missing: %s" % path))
            continue
        try:
            name, branch_type, loc = validate_branch(path, tech, metric, bt, version, language)
            rows.append((name, tech, metric, branch_type, loc, "PASS", rel_path, ""))
        except BranchValidationError as exc:
            rows.append((bname, tech, metric, bt, 0, "FAIL", rel_path, str(exc)))
    return rows


def validate_build(techniques="all", metrics="all", types=None, version="2.6",
                   language="python", build_dir="build", root=None):
    rows = validate_build_report(
        techniques, metrics, types, version, language, build_dir, root)
    failures = [r for r in rows if r[5] != "PASS"]
    if failures:
        lines = ["Validation failed (%d):" % len(failures)]
        for name, _, _, _, _, status, _, msg in failures:
            lines.append("  %s [%s]: %s" % (name, status, msg))
        raise BranchValidationError("\n".join(lines))
    return [(r[0], r[1], r[2], r[3], r[4], r[5]) for r in rows]


def validate_build_full_report(
    techniques="all",
    metrics="all",
    types=None,
    version="2.6",
    language="python",
    build_dir="build",
    root=None,
    tool_assert=False,
    parallel=1,
):
    """Structural validation plus optional tool_assert rows."""
    structural = validate_build_report(
        techniques, metrics, types, version, language, build_dir, root)
    struct_by_name = {r[0]: r for r in structural}

    tool_rows = []
    if tool_assert:
        from lib.tool_assert import tool_assert_build_report

        tool_rows = tool_assert_build_report(
            techniques, metrics, types, version, language, build_dir, root, parallel=parallel
        )
    tool_by_name = {r["branch_name"]: r for r in tool_rows}

    combined = []
    for name, tech, metric, bt, loc, struct_status, path, msg in structural:
        tr = tool_by_name.get(name, {})
        combined.append({
            "branch_name": name,
            "technique_code": tech,
            "metric_code": metric,
            "branch_type": bt,
            "loc": loc,
            "structural": struct_status,
            "structural_msg": msg,
            "path": path,
            "tool_assert": tr.get("status", "N/A") if tool_assert else "N/A",
            "tool_used": tr.get("tool_used", ""),
            "raw_metric_value": tr.get("raw_metric_value", ""),
            "expected_outcome": tr.get("expected_outcome", ""),
            "actual_outcome": tr.get("actual_outcome", ""),
            "tool_assert_msg": tr.get("message", ""),
        })
    return combined
