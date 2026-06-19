"""Multi-language structural validation helpers."""

from __future__ import print_function

import os
import re

from lib.lang_generators.base import MIN_LOC
from lib.metrics import parse_branch_name, sanitize_version
from lib.registry import metric_entry, package_name

TCC_CONFIG_FILES = (
    ".coveragerc", "setup.cfg", "pytest.ini", ".testmondata.ini",
    ".eslintrc.json", "jscpd.json", "checkstyle.xml", "coverlet.runsettings",
)
FORBIDDEN_MARKERS = ("TOOL_MODE", "-tcc-", "fallback-cc-", "if False:", "phantom")
FULL_TEST_MIN = {"DOV": 12, "TDI": 1, "QRA": 1}


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _line_count(path):
    return len(_read(path).splitlines())


def _target_path(root, technique_code, metric_code, language):
    lang = (language or "python").lower()
    _, metric = metric_entry(technique_code, metric_code)
    pkg = package_name(technique_code)
    module = metric["module_key"]
    if lang == "python":
        return os.path.join(root, pkg, "%s.py" % module)
    if lang == "java":
        cls = module.title().replace("_", "")
        pkg_dir = "com/testable/%s" % pkg.lower()
        return os.path.join(root, "src/main/java", pkg_dir, "%s.java" % cls)
    if lang == "javascript":
        return os.path.join(root, pkg.lower(), "%s.js" % module)
    if lang == "typescript":
        return os.path.join(root, pkg.lower(), "%s.ts" % module)
    if lang in ("csharp", "c#"):
        cls = module.title().replace("_", "")
        return os.path.join(root, "src", pkg, "%s.cs" % cls)
    raise ValueError("unsupported language %r" % language)


def _config_values(root, technique_code, language):
    lang = (language or "python").lower()
    pkg = package_name(technique_code)
    if lang == "python":
        path = os.path.join(root, pkg, "config.py")
        text = _read(path)
        out = {}
        for key in ("BRANCH_TYPE", "TARGET_METRIC_ABBREV", "TARGET_TECHNIQUE", "PYTHON_VERSION", "RUNTIME_VERSION", "LANGUAGE"):
            m = re.search(r"^%s\s*=\s*'([^']+)'" % key, text, re.M)
            if m:
                out[key] = m.group(1)
        return out
    if lang == "java":
        path = os.path.join(root, "src/main/java/com/testable/%s/Config.java" % pkg.lower())
        text = _read(path)
        out = {}
        for key in ("BRANCH_TYPE", "TARGET_METRIC_ABBREV", "TARGET_TECHNIQUE", "PYTHON_VERSION", "RUNTIME_VERSION", "LANGUAGE"):
            m = re.search(r'%s = "([^"]+)"' % key, text)
            if m:
                out[key] = m.group(1)
        return out
    if lang in ("javascript", "typescript"):
        ext = "js" if lang == "javascript" else "ts"
        path = os.path.join(root, pkg.lower(), "config.%s" % ext)
        text = _read(path)
        out = {}
        for key in ("BRANCH_TYPE", "TARGET_METRIC_ABBREV", "TARGET_TECHNIQUE", "PYTHON_VERSION", "RUNTIME_VERSION", "LANGUAGE"):
            m = re.search(r"%s:\s*'([^']+)'" % key, text)
            if m:
                out[key] = m.group(1)
        return out
    path = os.path.join(root, "src", pkg, "Config.cs")
    text = _read(path)
    out = {}
    for key in ("BRANCH_TYPE", "TARGET_METRIC_ABBREV", "TARGET_TECHNIQUE", "PYTHON_VERSION", "LANGUAGE"):
        m = re.search(r'const string %s = "([^"]+)"' % key, text)
        if m:
            out[key] = m.group(1)
    return out


def _count_loc(root, language):
    meta_path = os.path.join(root, ".gen_meta.json")
    if os.path.isfile(meta_path):
        import json
        try:
            with open(meta_path, encoding="utf-8") as fh:
                data = json.load(fh)
            if data.get("loc"):
                return int(data["loc"])
        except (ValueError, TypeError, OSError):
            pass
    total = 0
    exts = {
        "python": (".py",),
        "java": (".java",),
        "javascript": (".js",),
        "typescript": (".ts",),
        "csharp": (".cs",),
    }.get((language or "python").lower(), (".py",))
    for dirpath, _, files in os.walk(root):
        for fn in files:
            if fn.endswith(exts):
                total += _line_count(os.path.join(dirpath, fn))
    return total


def _count_tests(root, language):
    lang = (language or "python").lower()
    if lang == "python":
        tests = os.path.join(root, "tests")
        if not os.path.isdir(tests):
            return 0
        total = 0
        for fn in os.listdir(tests):
            if fn.endswith(".py") and fn != "__init__.py":
                total += len(re.findall(r"^\s+def test_", _read(os.path.join(tests, fn)), re.M))
        return total
    if lang == "java":
        total = 0
        for dirpath, _, files in os.walk(root):
            for fn in files:
                if fn.endswith("Test.java"):
                    total += len(re.findall(r"@Test", _read(os.path.join(dirpath, fn))))
        return total
    if lang == "csharp":
        total = 0
        tests = os.path.join(root, "tests")
        if os.path.isdir(tests):
            for fn in os.listdir(tests):
                if fn.endswith(".cs"):
                    total += len(re.findall(r"\[Fact\]", _read(os.path.join(tests, fn))))
        return total
    run_js = os.path.join(root, "tests", "run.js")
    if os.path.isfile(run_js):
        return len(re.findall(r"console\.assert", _read(run_js)))
    return 0


def assert_branch_structure(root, technique_code, metric_code, branch_type, version, language):
    parsed = parse_branch_name(os.path.basename(root))
    assert parsed, "cannot parse folder name"
    assert parsed["tech"] == technique_code.upper()
    assert parsed["metric"] == metric_code.upper()
    assert parsed["type"] == branch_type
    assert parsed["version"] == sanitize_version(version)

    cfg = _config_values(root, technique_code, language)
    assert cfg.get("BRANCH_TYPE") == branch_type
    assert cfg.get("TARGET_METRIC_ABBREV") == metric_code.upper()
    assert cfg.get("TARGET_TECHNIQUE") == technique_code.upper()
    if language:
        assert cfg.get("LANGUAGE") == language

    target_path = _target_path(root, technique_code, metric_code, language)
    assert os.path.isfile(target_path), "missing target %s" % target_path
    target_src = _read(target_path)
    test_count = _count_tests(root, language)

    if branch_type == "Bug":
        assert "escalated-" in target_src
        for name in TCC_CONFIG_FILES:
            assert not os.path.isfile(os.path.join(root, name))
        assert test_count <= 2, "Bug expects partial tests, got %d" % test_count
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
        assert "neutral-" in target_src or "OUTCOME_LOOKUP" in target_src, (
            "CC missing neutral-/OUTCOME_LOOKUP marker"
        )
        assert "escalated-" not in target_src
        for name in TCC_CONFIG_FILES:
            assert not os.path.isfile(os.path.join(root, name))
        assert test_count >= FULL_TEST_MIN.get(metric_code.upper(), 12)

    loc = _count_loc(root, language)
    assert loc >= MIN_LOC, "LOC %d < %d" % (loc, MIN_LOC)
    return loc
