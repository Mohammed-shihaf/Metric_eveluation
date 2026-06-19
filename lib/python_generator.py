"""Generic Python branch generator for any technique/metric in the registry."""

from __future__ import print_function

import json
import os
import textwrap

from lib.registry import metric_entry, package_name, technique_by_code
from lib.sa_generator import (
    FUTURE,
    FORBIDDEN_MARKERS,
    MIN_LOC,
    SUPPORT_GENERATORS,
    _assert_no_forbidden,
    _gen_tests_generic,
    _stub_metric_module,
    gen_models_py,
    n_functions as sa_n_functions,
)

DEFAULT_N_FUNCTIONS = 72
N_FUNCTIONS_OVERRIDES = {
    ("SA", "EPI"): 26,
    ("SA", "DOV"): 20,
    ("SA", "LSV"): 32,
    ("SA", "TLCC"): 34,
    ("SA", "TDI"): 36,
    ("SA", "QRA"): 40,
}

VARIANT_MAP = {"Bug": "bug", "BugFX": "bugfx", "TCC": "tcc", "CC": "cc"}

# Tool-detectable defect snippets (Bug branches only) — see docs/TOOL_ASSERTS.md
_TOOL_DEFECT_SNIPPETS = {
    "SX": (
        "\n    # intentional-sast-vuln for tool-assert\n"
        "    hardcoded_password = 'secret-token-12345'\n"
        "    if retry_count > 99:\n"
        "        eval('1+1')  # noqa: S307\n"
    ),
    "DR": (
        "\n    # defect: dependency risk marker for pip-audit branch\n"
        "    _risk_marker = 'cve-seed'\n"
    ),
}


def _compact_case_body(prefix, idx, metric_name):
    """Flake8-clean function body that preserves realistic LOC."""
    return (
        "def %s_case_%d(state, enabled, retry_count, priority):\n"
        '    """Evaluate %s case %d."""\n'
        "    if state is None:\n"
        "        raise ValueError('state required')\n"
        "    if retry_count < 0:\n"
        "        retry_count = 0\n"
        "    idx = %d\n"
        "    severity = priority %% 5\n"
        "    active = bool(enabled)\n"
        "    score = (severity + idx) %% 7\n"
        "    if not active and score < 2:\n"
        "        return 'idle-%s-%%s-%%d' %% (state, idx)\n"
        "    if active and score >= 5:\n"
        "        return 'active-%s-%%s-%%d' %% (state, idx)\n"
        "    return 'default-%s-%%s-%%d' %% (state, idx)\n\n"
    ) % (prefix, idx, metric_name, idx, idx, prefix, prefix, prefix)


def _family_bug_extra(prefix, idx, family, strength):
    """Tool-detectable defect snippets keyed by runner family."""
    if family == "crosshair" and idx == 1:
        return (
            "    if retry_count > 5:\n"
            "        score = score - 100\n"
            "    assert score >= 0, 'crosshair invariant'\n"
        )
    if family == "pymcdc" and idx == 1:
        return (
            "    gate_a = retry_count > 2\n"
            "    gate_b = priority < 3\n"
            "    gate_c = enabled\n"
            "    if (gate_a and gate_b) or (gate_b and gate_c) or (gate_a and gate_c):\n"
            "        return 'mcdc-%s-%%d' %% idx\n" % prefix
        )
    if family == "complexity" and strength > 0 and idx <= 2 + strength:
        return (
            "    for outer in range(%d):\n"
            "        for inner in range(%d):\n"
            "            for mid in range(2):\n"
            "                if outer %% 2 == 0 and inner %% 3 == 0 and mid %% 2 == 0:\n"
            "                    if retry_count > outer:\n"
            "                        if priority < inner:\n"
            "                            return 'complex-%s-%%d' %% idx\n"
        ) % (3 + strength, 4 + strength, prefix)
    if family == "coverage" and idx == 1:
        return "    # defect: partial coverage path\n    if retry_count > 99:\n        return None\n"
    if family == "lint" and idx <= 3:
        return (
            "    x=retry_count+priority  # noqa: E225 intentional lint defect\n"
            "    unused = x * 2\n"
        )
    if family == "beniget" and idx == 1:
        return "    _dead_local = score * 99\n    # defect: unused assignment\n"
    if family == "duplication" and idx <= 4:
        return (
            "    chunk = []\n"
            "    for token in (state, str(priority), str(retry_count)):\n"
            "        chunk.append('dup-%s-%%d-' %% idx + token)\n"
            "        chunk.append(token[::-1])\n"
            "        chunk.append(str(len(token)))\n"
            "    payload = '-'.join(chunk)\n"
            "    if len(payload) > 12:\n"
            "        return payload\n"
        ) % prefix
    return ""


def _expected_case_value(prefix, idx, state, enabled, retry_count, priority, variant):
    """Deterministic expected return for mutation oracle tests."""
    if state is None:
        raise ValueError("state required")
    if retry_count < 0:
        retry_count = 0
    severity = priority % 5
    active = bool(enabled)
    score = (severity + idx) % 7
    if variant == "bug":
        if not active and score < 2:
            return "idle-%s-%s-%d" % (prefix, state, idx)
        if active and score >= 5:
            return "active-%s-%s-%d" % (prefix, state, idx)
        if retry_count > 3 and not enabled:
            return "escalated-%s-%s-%d" % (prefix, state, idx)
        return "default-%s-%s-%d" % (prefix, state, idx)
    if variant == "bugfx":
        if not active and score < 2:
            return "idle-%s-%s-%d" % (prefix, state, idx)
        if active and score >= 5:
            return "active-%s-%s-%d" % (prefix, state, idx)
        if retry_count > 3 and not enabled:
            return "stable-%s-%s-%d" % (prefix, state, idx)
        return "default-%s-%s-%d" % (prefix, state, idx)
    if variant == "tcc":
        if not active and score < 2:
            return "idle-%s-%s-%d" % (prefix, state, idx)
        if active and score >= 5:
            return "active-%s-%s-%d" % (prefix, state, idx)
        if not enabled:
            return "disabled-%s-%s-%d" % (prefix, state, idx)
        return "default-%s-%s-%d" % (prefix, state, idx)
    if not active and score < 2:
        return "idle-%s-%s-%d" % (prefix, state, idx)
    if active and score >= 5:
        return "active-%s-%s-%d" % (prefix, state, idx)
    lookup = {"%s" % prefix: "neutral-%s-%d" % (prefix, idx)}
    if state in lookup:
        return lookup[state]
    return "default-%s-%s-%d" % (prefix, state, idx)


def n_functions(technique_code, metric_code):
    key = (technique_code.upper(), metric_code.upper())
    if key in N_FUNCTIONS_OVERRIDES:
        return N_FUNCTIONS_OVERRIDES[key]
    tech = technique_by_code(technique_code)
    # smaller technique groups need more functions per target to reach MIN_LOC
    return max(DEFAULT_N_FUNCTIONS, 44 - len(tech["metrics"]))


def _count_loc(files, pkg):
    total = 0
    for path, content in files.items():
        if path == "main.py" or path.startswith("%s/" % pkg) or path.startswith("tests/"):
            total += content.count("\n") + (0 if content.endswith("\n") else 1)
    return total


def _gen_config(tech, metric, branch_type, version, language, pkg, runtime=None):
    from lib.lang_support import default_runtime, normalize_runtime

    rt = normalize_runtime(language, runtime or default_runtime(language))
    tools = "\n".join(
        "    '%s': {'classification': '%s', 'metric': '%s', 'tool': '%s'}," % (
            m["module_key"],
            m["taxonomy_classification"],
            m["l5_metric"],
            (m.get("tools") or {}).get(language, {}).get("primary") or "",
        )
        for m in tech["metrics"]
    )
    return FUTURE + (
        '"""Runtime configuration for %(l2)s / %(l3)s."""\n'
        "LANGUAGE = '%(language)s'\n"
        "RUNTIME_VERSION = '%(runtime)s'\n"
        "PYTHON_VERSION = '%(runtime)s'\n"
        "BRANCH_TYPE = '%(branch_type)s'\n"
        "BRANCH_VARIANT = '%(branch_type)s'\n"
        "TARGET_TECHNIQUE = '%(tech)s'\n"
        "TARGET_METRIC_ABBREV = '%(metric)s'\n"
        "TARGET_METRIC_NAME = '%(metric_name)s'\n"
        "TESTING_TYPE = '%(l2)s'\n"
        "TECHNIQUE = '%(l3)s'\n"
        "METRIC_TOOL_MAP = {\n%(tools)s\n}\n"
    ) % {
        "language": language,
        "runtime": rt,
        "version": version,
        "branch_type": branch_type,
        "tech": tech["technique_code"],
        "metric": metric["metric_code"],
        "metric_name": metric["l5_metric"],
        "l2": tech["l2"],
        "l3": tech["l3"],
        "tools": tools,
    }


def _gen_init(pkg, l2, version):
    return FUTURE + textwrap.dedent(
        '''
        """%(l2)s package (Python %(version)s)."""
        __version__ = '1.0.0'
        __testing_type__ = '%(l2)s'
        def package_info():
            return {'version': __version__, 'testing_type': __testing_type__}
        '''
    ) % {"l2": l2, "version": version}


def _case_body(prefix, idx, variant, metric_name, tool, technique_code=None, family=None, strength=0):
    """One realistic ~18-line decision function."""
    if family == "lint" and variant != "bug":
        return _compact_case_body(prefix, idx, metric_name)
    if variant == "bug":
        extra = (
            "    if retry_count > 3 and not enabled:\n"
            "        return 'escalated-%s-%%s-%%d' %% (state, idx)\n" % prefix
        )
        if idx == 1 and technique_code and technique_code.upper() in _TOOL_DEFECT_SNIPPETS:
            extra += _TOOL_DEFECT_SNIPPETS[technique_code.upper()]
        extra += _family_bug_extra(prefix, idx, family, strength)
    elif variant == "bugfx":
        extra = (
            "    if retry_count > 3 and not enabled:\n"
            "        return 'stable-%s-%%s-%%d' %% (state, idx)\n" % prefix
        )
        if family == "complexity" and strength > 0:
            extra = "    return 'resolved-%s-%%s-%%d' %% (state, idx)\n" % prefix
    elif variant == "tcc":
        extra = (
            "    if not enabled:\n"
            "        return 'disabled-%s-%%s-%%d' %% (state, idx)\n" % prefix
        )
    else:
        extra = (
            "    lookup = {'%s': 'neutral-%s-' + str(idx)}\n"
            "    if state in lookup:\n"
            "        return lookup[state]\n" % (prefix, prefix)
        )
        if family == "complexity" and strength > 0:
            extra = "    return 'neutral-%s-%%s-%%d' %% (state, idx)\n" % prefix
    return (
        "def %s_case_%d(state, enabled, retry_count, priority):\n"
        '    """Evaluate %s case %d (%s-oriented)."""\n'
        "    if state is None:\n"
        "        raise ValueError('state required')\n"
        "    if retry_count < 0:\n"
        "        retry_count = 0\n"
        "    idx = %d\n"
        "    severity = priority %% 5\n"
        "    active = bool(enabled)\n"
        "    score = (severity + idx) %% 7\n"
        "    if not active and score < 2:\n"
        "        return 'idle-%s-%%s-%%d' %% (state, idx)\n"
        "    if active and score >= 5:\n"
        "        return 'active-%s-%%s-%%d' %% (state, idx)\n"
        "%s"
        "    return 'default-%s-%%s-%%d' %% (state, idx)\n\n"
    ) % (prefix, idx, metric_name, idx, tool or "tool", idx, prefix, prefix, extra, prefix)


def _gen_target_module(metric, variant, n_fn, tool, technique_code=None, strength=0):
    from lib.tool_assert import tool_family

    prefix = metric["metric_code"].lower()
    family = tool_family(tool or "", technique_code or "")
    parts = [
        FUTURE,
        "METRIC_NAME = '%s'\nTOOL_PRIMARY = '%s'\n\n" % (metric["l5_metric"], tool or ""),
    ]
    if family == "lint" and variant != "bug":
        parts[1] = (
            "# flake8: noqa\n"
            "METRIC_NAME = '%s'\nTOOL_PRIMARY = '%s'\n\n" % (metric["l5_metric"], tool or "")
        )
    if family == "duplication" and variant == "bug":
        base = _case_body(
            prefix, 1, variant, metric["l5_metric"], tool or "tool",
            technique_code, family, strength,
        )
        parts.append(base)
        for i in range(2, min(6, n_fn + 1)):
            parts.append(
                base.replace("%s_case_1" % prefix, "%s_case_%d" % (prefix, i))
                .replace("case 1", "case %d" % i)
            )
        for i in range(6, n_fn + 1):
            parts.append(
                _case_body(
                    prefix, i, variant, metric["l5_metric"], tool or "tool",
                    technique_code, family, strength,
                )
            )
        return "".join(parts)
    for i in range(1, n_fn + 1):
        parts.append(
            _case_body(prefix, i, variant, metric["l5_metric"], tool or "tool", technique_code, family, strength)
        )
    return "".join(parts)


def _churn_meta(metric, variant, technique_code=None, strength=0):
    """Emit churn metadata when the metric primary maps to churn family."""
    from lib.tool_assert import CHURN_FAIL_THRESHOLD, tool_family

    primary = (metric.get("tools") or {}).get("python", {}).get("primary", "")
    tc = (technique_code or "").upper()
    if tool_family(primary, tc) != "churn":
        if tc == "DP" and variant == "bug":
            score = CHURN_FAIL_THRESHOLD + 15.0 + strength * 5.0
        else:
            return {}
    else:
        if variant == "bug":
            score = CHURN_FAIL_THRESHOLD + 15.0 + strength * 8.0
        else:
            score = max(5.0, CHURN_FAIL_THRESHOLD - 25.0 - strength * 5.0)
    return {
        ".churn_meta.json": json.dumps(
            {
                "churn_score": score,
                metric["module_key"]: {"churn_score": score, "commits": 42},
            },
            indent=2,
        )
        + "\n",
    }


def _requirements_extra(technique_code, variant):
    tc = technique_code.upper()
    if tc == "DR":
        if variant == "bug":
            return "urllib3==1.24.1\nrequests==2.20.0\ncryptography==2.3\n"
        return "# no vulnerable dependencies\n"
    if tc == "TCC" and variant == "tcc":
        return "coverage==7.0.0\npytest>=8.0.0\n"
    return "pytest>=8.0.0\n"


def _gen_stub(module_key, l5, l3, tool):
    return FUTURE + textwrap.dedent(
        '''
        """Stub: %(l5)s — %(l3)s (not the target metric for this branch)."""
        TOOL_HINT = '%(tool)s'
        DOMAIN = '%(l3)s'

        class %(cls)sAnalyzer(object):
            def __init__(self, name):
                self.name = name
                self.readings = []

            def record(self, value, label):
                if value is None:
                    return False
                self.readings.append((label, float(value)))
                return True

            def average(self):
                if not self.readings:
                    return 0.0
                total = sum(v for _, v in self.readings)
                return total / len(self.readings)

            def summarize(self):
                return {'name': self.name, 'count': len(self.readings), 'avg': self.average()}


        def evaluate_%(key)s_sample(inputs):
            """Lightweight domain helper for %(l5)s."""
            analyzer = %(cls)sAnalyzer('%(key)s')
            for label, value in inputs.items():
                analyzer.record(value, label)
            avg = analyzer.average()
            if avg > 10:
                return 'elevated'
            if avg > 5:
                return 'moderate'
            return 'low'
        '''
    ) % {
        "l5": l5,
        "l3": l3,
        "tool": tool or "n/a",
        "key": module_key,
        "cls": "".join(w.capitalize() for w in module_key.split("_")[:3]) or "Metric",
    }


def _gen_main(pkg, metric_code, module_key, n_fn):
    return FUTURE + textwrap.dedent(
        '''
        import sys
        from %(pkg)s.config import TARGET_METRIC_ABBREV, BRANCH_TYPE
        from %(pkg)s import %(module)s as target

        def run_demo():
            print('Branch type:', BRANCH_TYPE)
            print('Target metric:', TARGET_METRIC_ABBREV)
            samples = [
                ('alpha', True, 1, 3),
                ('beta', False, 2, 5),
                ('gamma', True, 0, 7),
            ]
            for state, enabled, retry, priority in samples:
                fn = getattr(target, '%(prefix)s_case_1')
                result = fn(state, enabled, retry, priority)
                print('  %%s -> %%s' %% (state, result))

        if __name__ == '__main__':
            run_demo()
        '''
    ) % {
        "pkg": pkg,
        "module": module_key,
        "prefix": metric_code.lower(),
    }


def _gen_tests(pkg, metric, branch_type, n_fn, strength=0, technique_code=None, tool=""):
    from lib.lang_generators.base import scaled_test_count
    from lib.tool_assert import tool_family

    files = {"tests/__init__.py": FUTURE}
    prefix = metric["metric_code"].lower()
    mod = metric["module_key"]
    fn = "%s_case_1" % prefix
    variant = VARIANT_MAP[branch_type]
    family = tool_family(tool or "", technique_code or "")
    if branch_type == "Bug":
        files["tests/test_%s.py" % mod] = (
            FUTURE + "import unittest\nfrom %s.%s import %s\n\n"
            "class TestBugPartial(unittest.TestCase):\n"
            "    def test_one_case(self):\n"
            "        self.assertTrue(%s('x', True, 1, 3))\n" % (pkg, mod, fn, fn))
        return files
    test_count = scaled_test_count(n_fn, branch_type, strength)
    use_exact = family == "mutation"
    lines = [
        FUTURE,
        "import unittest\nfrom %s import %s as target\n\n" % (pkg, mod),
        "class Test%sFull(unittest.TestCase):\n" % metric["metric_code"],
    ]
    for i in range(1, test_count + 1):
        fn_i = "%s_case_%d" % (prefix, min(i, n_fn))
        case_idx = min(i, n_fn)
        retry = i % 3
        pri = i % 5
        state = "s%d" % i
        if use_exact:
            expected = _expected_case_value(prefix, case_idx, state, True, retry, pri, variant)
            lines.append(
                "    def test_%s(self):\n"
                "        got = target.%s('%s', True, %d, %d)\n"
                "        self.assertEqual(got, '%s')\n"
                % (fn_i, fn_i, state, retry, pri, expected)
            )
        else:
            lines.append(
                "    def test_%s(self):\n        self.assertIsNotNone(target.%s('s%%d' %% %d, True, %d, %d))\n"
                % (fn_i, fn_i, i, retry, pri)
            )
    lines.append("\n")
    files["tests/test_%s.py" % mod] = "".join(lines)
    if branch_type != "Bug":
        files["tests/test_stub_sanity.py"] = (
            FUTURE + "import unittest\nimport os\n\nclass TestStubs(unittest.TestCase):\n"
            "    def test_pkg_exists(self):\n        self.assertTrue(os.path.isdir('%s'))\n" % pkg)
    return files


def _tool_configs(branch_type, pkg, primary_tool, family=None):
    if branch_type != "TCC":
        return {}
    configs = {}
    if family == "testmon" or (primary_tool and "testmon" in primary_tool.lower()):
        configs[".testmondata.ini"] = "[testmon]\nversion = 1\n"
    if primary_tool and "eslint" in primary_tool.lower():
        configs[".eslintrc.json"] = '{"env":{"node":true},"rules":{"complexity":["error",10]}}\n'
        return configs
    if primary_tool and "jscpd" in primary_tool.lower():
        configs["jscpd.json"] = '{"threshold":5,"minLines":10}\n'
        return configs
    configs.update({
        ".coveragerc": "[run]\nbranch = True\nsource = %s\nomit = tests/*\n" % pkg,
        "setup.cfg": "[tool:pytest]\ntestpaths = tests\n",
        "pytest.ini": "[pytest]\ntestpaths = tests\n",
    })
    return configs


def generate_branch_files(technique_code, metric_code, branch_type, version="2.6", language="python", strength=0, runtime=None):
    from lib.lang_generators.base import effective_strength, scaled_n_functions
    from lib.lang_support import normalize_language

    strength = effective_strength(strength)
    if normalize_language(language) != "python":
        from lib.lang_generators.template_core import generate_branch_files as dispatch_gen
        return dispatch_gen(technique_code, metric_code, branch_type, version, language, strength=strength, runtime=runtime)
    from lib.lang_support import default_runtime, normalize_runtime

    rt = normalize_runtime(language, runtime or default_runtime(language))
    tech = technique_by_code(technique_code)
    _, metric = metric_entry(technique_code, metric_code)
    from lib.metrics import branch_name as metrics_branch_name
    pkg = package_name(technique_code)
    variant = VARIANT_MAP[branch_type]
    tool = (metric.get("tools") or {}).get("python", {}).get("primary", "")
    bname = metrics_branch_name(technique_code, metric_code, branch_type, version)

    n_fn = scaled_n_functions(n_functions(technique_code, metric_code), strength)
    files = None
    loc = 0
    while n_fn <= 180:
        files = _assemble_files(
            tech, metric, technique_code, metric_code, pkg, variant, n_fn, tool,
            branch_type, version, language, strength=strength, runtime=rt,
        )
        loc = _count_loc(files, pkg)
        if loc >= MIN_LOC:
            break
        n_fn += 4
    if loc < MIN_LOC:
        raise ValueError("Generated %s has only %d LOC (need >= %d)" % (bname, loc, MIN_LOC))
    files[".gen_meta.json"] = json.dumps(
        {
            "strength": strength,
            "technique": technique_code,
            "metric": metric_code,
            "branch_type": branch_type,
            "version": version,
            "language": language,
            "runtime": rt,
            "n_functions": n_fn,
            "loc": loc,
            "branch_name": bname,
        },
        indent=2,
    ) + "\n"
    return files


def _assemble_files(tech, metric, technique_code, metric_code, pkg, variant, n_fn, tool, branch_type, version, language, strength=0, runtime=None):
    from lib.tool_assert import tool_family

    files = {}
    files["%s/__init__.py" % pkg] = _gen_init(pkg, tech["l2"], version)
    files["%s/config.py" % pkg] = _gen_config(tech, metric, branch_type, version, language, pkg, runtime=runtime)
    files["%s/models.py" % pkg] = gen_models_py().replace("sa/", "%s/" % pkg)
    for rel, gen_fn in SUPPORT_GENERATORS.items():
        if rel == "sa/models.py":
            continue
        out_rel = rel.replace("sa/", "%s/" % pkg)
        files[out_rel] = gen_fn().replace("sa/", "%s/" % pkg)

    target_rel = "%s/%s.py" % (pkg, metric["module_key"])
    for m in tech["metrics"]:
        rel = "%s/%s.py" % (pkg, m["module_key"])
        mtool = (m.get("tools") or {}).get("python", {}).get("primary", "")
        if m["metric_code"] == metric["metric_code"]:
            files[rel] = _gen_target_module(metric, variant, n_fn, mtool, technique_code, strength=strength)
        elif rel == target_rel:
            # Duplicate module_key shared with the target metric: keep the rich
            # target module, do not overwrite it with a stub.
            continue
        else:
            files[rel] = _gen_stub(m["module_key"], m["l5_metric"], tech["l3"], mtool)

    files["main.py"] = _gen_main(pkg, metric["metric_code"], metric["module_key"], n_fn)
    from lib.metrics import branch_name as metrics_branch_name
    bname = metrics_branch_name(technique_code, metric_code, branch_type, version)
    files["README.md"] = "# %s\n\n%s / %s\n" % (bname, tech["l2"], metric["l5_metric"])
    files["requirements.txt"] = _requirements_extra(technique_code, variant)
    files.update(_tool_configs(branch_type, pkg, tool, family=tool_family(tool or "", technique_code)))
    files.update(_churn_meta(metric, variant, technique_code, strength=strength))
    files.update(_gen_tests(pkg, metric, branch_type, n_fn, strength=strength,
                             technique_code=technique_code, tool=tool))
    for path, content in files.items():
        if path.endswith(".py"):
            _assert_no_forbidden(content, path)
    return files


def read_gen_meta(branch_dir):
    """Read per-branch generation metadata written alongside the codebase."""
    path = os.path.join(branch_dir, ".gen_meta.json")
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError, TypeError):
        return {}


def _safe_rmtree(path):
    import shutil
    import stat
    import time

    def _on_rm_error(func, p, exc_info):
        try:
            os.chmod(p, stat.S_IWRITE)
            func(p)
        except OSError:
            pass

    if not os.path.isdir(path):
        return
    for attempt in range(3):
        try:
            shutil.rmtree(path, onerror=_on_rm_error)
            return
        except OSError:
            for root, _, files in os.walk(path):
                for fn in files:
                    if fn.endswith(".sqlite") or fn.endswith(".sqlite-journal"):
                        try:
                            os.chmod(os.path.join(root, fn), stat.S_IWRITE)
                            os.remove(os.path.join(root, fn))
                        except OSError:
                            pass
            time.sleep(0.2 * (attempt + 1))
    shutil.rmtree(path, ignore_errors=True)


def write_branch(root, technique_code, metric_code, branch_type, version="2.6", language="python", strength=0, runtime=None):
    import os
    from lib.lang_generators.base import effective_strength
    from lib.lang_support import normalize_language
    from lib.metrics import branch_name as metrics_branch_name

    strength = effective_strength(strength)
    if normalize_language(language) != "python":
        from lib.lang_generators.template_core import write_branch as dispatch_write
        return dispatch_write(root, technique_code, metric_code, branch_type, version, language, strength=strength, runtime=runtime)

    files = generate_branch_files(technique_code, metric_code, branch_type, version, language, strength=strength, runtime=runtime)
    if os.path.isdir(root):
        _safe_rmtree(root)
    os.makedirs(root)
    for rel, content in files.items():
        path = os.path.join(root, rel)
        parent = os.path.dirname(path)
        if parent and not os.path.isdir(parent):
            os.makedirs(parent)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(content)
    pkg = package_name(technique_code)
    loc = _count_loc(files, pkg)
    bname = metrics_branch_name(technique_code, metric_code, branch_type, version)
    return bname, loc
