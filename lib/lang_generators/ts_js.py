"""Full TypeScript/JavaScript branch generator with per-technique/family parity."""

from __future__ import print_function

import json
import textwrap

from lib.lang_generators.base import MIN_LOC, VARIANT_MAP, effective_strength, scaled_n_functions, scaled_test_count
from lib.lang_generators.case_emit import n_functions, variant_extra_js
from lib.lang_generators.meta_common import branch_label, config_fields, count_loc_files, gen_meta
from lib.registry import metric_entry, package_name, technique_by_code
from lib.registry_tools import get_metric_tools
from lib.tool_assert import tool_family


def _node_major(runtime):
    rt = (runtime or "Node 20").strip()
    if rt.lower().startswith("node"):
        return rt.split()[-1]
    return "20"


def _ts_target(runtime):
    major = _node_major(runtime)
    if int(major) >= 20:
        return "ES2022"
    return "ES2020"


def _case_method(prefix, idx, variant, family, technique_code, strength, ext):
    extra = variant_extra_js(prefix, idx, variant, family, technique_code, strength, ext)
    sig = (
        "export function %(prefix)sCase%(idx)d(state: string, enabled: boolean, retry: number, priority: number): string {"
        if ext == "ts"
        else "function %(prefix)sCase%(idx)d(state, enabled, retry, priority) {"
    ) % {"prefix": prefix, "idx": idx}
    body = textwrap.dedent(
        '''
        %(sig)s
          if (state == null) throw new Error('state required');
          if (retry < 0) retry = 0;
          const idx = %(idx)d;
          const severity = priority %% 5;
          const active = !!enabled;
          let score = (severity + idx) %% 7;
          if (!active && score < 2) return `idle-%(prefix)s-${state}-${idx}`;
          if (active && score >= 5) return `active-%(prefix)s-${state}-${idx}`;
        %(extra)s
          return `default-%(prefix)s-${state}-${idx}`;
        }
        '''
    ) % {"sig": sig, "prefix": prefix, "idx": idx, "extra": extra}
    return body


def _config_body(fields):
    return textwrap.dedent(
        '''
        {
          LANGUAGE: '%(language)s',
          RUNTIME_VERSION: '%(runtime)s',
          PYTHON_VERSION: '%(runtime)s',
          BRANCH_TYPE: '%(branch_type)s',
          TARGET_TECHNIQUE: '%(tech)s',
          TARGET_METRIC_ABBREV: '%(metric)s',
          TARGET_METRIC_NAME: '%(metric_name)s',
          TESTING_TYPE: '%(l2)s',
          TECHNIQUE: '%(l3)s',
        }
        '''
    ).strip() % fields


def _assemble_js_like_files(tech, metric, technique_code, metric_code, branch_type, version, language, runtime, strength, ext, n_fn):
    pkg = package_name(technique_code).lower()
    variant = VARIANT_MAP[branch_type]
    prefix = metric_code.lower()
    module = metric["module_key"]
    lang_tools = get_metric_tools(technique_code, metric_code, language)
    family = tool_family(lang_tools.get("primary") or "", technique_code)
    node_major = _node_major(runtime)
    files = {}
    pkg_json = {
        "name": pkg,
        "version": "1.0.0",
        "type": "commonjs" if ext == "ts" else "module",
        "scripts": {"test": "node tests/run.js"},
        "engines": {"node": ">=%s.0.0" % node_major},
    }
    if ext == "ts":
        pkg_json["devDependencies"] = {
            "typescript": (runtime or "5.4").strip(),
            "@types/node": "^20.0.0",
        }
    files["package.json"] = json.dumps(pkg_json, indent=2) + "\n"
    if ext == "ts":
        files["tsconfig.json"] = json.dumps(
            {"compilerOptions": {"target": _ts_target(runtime), "module": "commonjs", "strict": True}},
            indent=2,
        ) + "\n"

    cfg = config_fields(tech, metric, branch_type, version, language, runtime, lang_tools)
    cfg_body = _config_body(cfg)
    if ext == "ts":
        files["%s/config.ts" % pkg] = "const Config = %s;\nexport default Config;\n" % cfg_body
    else:
        files["%s/config.js" % pkg] = "module.exports = %s;\n" % cfg_body

    body = []
    for i in range(1, n_fn + 1):
        body.append(_case_method(prefix, i, variant, family, technique_code, strength, ext))
    exports = ", ".join("%sCase%d" % (prefix, i) for i in range(1, min(n_fn, 12) + 1))
    if ext == "ts":
        body.append("export { %s };\n" % exports)
    else:
        body.append("export { %s };\n" % exports)
    files["%s/%s.%s" % (pkg, module, ext)] = "\n".join(body)

    for m in tech["metrics"]:
        if m["metric_code"] == metric_code.upper():
            continue
        stub = "module.exports = { stub: () => 'stub-%s' };\n" % m["module_key"]
        files["%s/%s.js" % (pkg, m["module_key"])] = stub

    test_count = scaled_test_count(n_fn, branch_type, strength)
    if ext == "ts":
        tests = ["const target = require('../%s/%s');\n" % (pkg, module)]
    else:
        tests = ["import * as target from '../%s/%s.js';\n" % (pkg, module)]
    for i in range(1, test_count + 1):
        fn = "%sCase%d" % (prefix, min(i, n_fn))
        tests.append("console.assert(target.%s('s%d', true, %d, %d) != null);\n" % (fn, i, i % 3, i % 5))
    files["tests/run.js"] = "".join(tests)
    files["main.js"] = "console.log('metric %s');\n" % metric_code
    if branch_type == "TCC":
        files[".eslintrc.json"] = '{"rules":{"complexity":["error",10]}}\n'
    return files


def generate_branch_files(technique_code, metric_code, branch_type, version="2.6", language="javascript", strength=0, runtime="Node 20"):
    strength = effective_strength(strength)
    lang = (language or "javascript").strip().lower()
    ext = "ts" if lang == "typescript" else "js"
    tech = technique_by_code(technique_code)
    _, metric = metric_entry(technique_code, metric_code)
    bname = branch_label(technique_code, metric_code, branch_type, version)
    n_fn = scaled_n_functions(n_functions(technique_code, metric_code), strength)
    files = None
    loc = 0
    prefixes = (package_name(technique_code).lower(), "tests", "main.js")
    exts = (".ts", ".js", ".json") if ext == "ts" else (".js", ".json")
    while n_fn <= 200:
        files = _assemble_js_like_files(
            tech, metric, technique_code, metric_code, branch_type, version, lang, runtime, strength, ext, n_fn,
        )
        loc = count_loc_files(files, exts, prefixes)
        if loc >= MIN_LOC:
            break
        n_fn += 8
    if loc < MIN_LOC:
        raise ValueError("Generated %s has only %d LOC (need >= %d)" % (bname, loc, MIN_LOC))
    files[".gen_meta.json"] = gen_meta(
        strength, technique_code, metric_code, branch_type, version, lang, runtime, n_fn, loc, bname,
    )
    return files
