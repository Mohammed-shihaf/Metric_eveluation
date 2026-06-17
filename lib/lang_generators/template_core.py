"""Template-based multi-language branch file generation."""

from __future__ import print_function

import json
import textwrap

from lib.lang_generators.base import (
    DEFAULT_N_FUNCTIONS,
    MIN_LOC,
    VARIANT_MAP,
    effective_strength,
    scaled_n_functions,
    scaled_test_count,
    variant_marker,
)
from lib.metrics import branch_name as metrics_branch_name
from lib.registry import metric_entry, package_name, technique_by_code
from lib.sa_generator import MIN_LOC as SA_MIN_LOC

MIN_LOC = max(MIN_LOC, SA_MIN_LOC)


def _count_loc(files, extensions, prefixes):
    total = 0
    for path, content in files.items():
        if path == ".gen_meta.json":
            continue
        if not any(path.endswith(ext) for ext in extensions):
            continue
        if prefixes and not any(path.startswith(p) or ("/%s/" % p) in path or path == p for p in prefixes):
            continue
        total += content.count("\n") + (0 if content.endswith("\n") else 1)
    return total


def _gen_meta(strength, technique_code, metric_code, branch_type, version, language, n_fn, loc, bname):
    return json.dumps(
        {
            "strength": strength,
            "technique": technique_code,
            "metric": metric_code,
            "branch_type": branch_type,
            "version": version,
            "language": language,
            "n_functions": n_fn,
            "loc": loc,
            "branch_name": bname,
        },
        indent=2,
    ) + "\n"


def _java_case_method(prefix, idx, variant, strength):
    mark = variant_marker(variant, idx, strength)
    depth = 2 + effective_strength(strength)
    lines = [
        "    public static String %sCase%d(String state, boolean enabled, int retry, int priority) {" % (prefix, idx),
        "        // %s" % mark,
        "        int score = priority + retry;",
        "        if (enabled && retry > %d) {" % depth,
        "            score += 3;",
        "        }",
        "        if (state != null && state.length() > 2) {",
        "            score += state.charAt(0);",
        "        }",
        "        for (int i = 0; i < retry; i++) {",
        "            score += i % 3;",
        "        }",
        "        if (priority > 5 && enabled) {",
        "            score -= 1;",
        "        }",
        "        return state + \"-\" + mark + \"-\" + score;",
        "    }",
        "",
    ]
    return "\n".join(lines)


def _java_files(tech, metric, technique_code, metric_code, branch_type, version, language, strength, n_fn=None):
    pkg = package_name(technique_code).lower()
    pkg_path = "com.testable.%s" % pkg
    pkg_dir = pkg_path.replace(".", "/")
    variant = VARIANT_MAP[branch_type]
    prefix = metric_code.lower()
    module = metric["module_key"]
    if n_fn is None:
        n_fn = scaled_n_functions(DEFAULT_N_FUNCTIONS, strength)
    primary = "tool"

    files = {}
    files["pom.xml"] = textwrap.dedent(
        '''
        <project xmlns="http://maven.apache.org/POM/4.0.0">
          <modelVersion>4.0.0</modelVersion>
          <groupId>com.testable</groupId>
          <artifactId>%s</artifactId>
          <version>1.0.0</version>
          <properties><maven.compiler.source>17</maven.compiler.source></properties>
        </project>
        '''
    ).strip() % pkg

    cfg = textwrap.dedent(
        '''
        package %s;
        public final class Config {
            public static final String LANGUAGE = "%s";
            public static final String PYTHON_VERSION = "%s";
            public static final String BRANCH_TYPE = "%s";
            public static final String TARGET_TECHNIQUE = "%s";
            public static final String TARGET_METRIC_ABBREV = "%s";
        }
        '''
    ) % (pkg_path, language, version, branch_type, technique_code.upper(), metric_code.upper())
    files["src/main/java/%s/Config.java" % pkg_dir] = cfg

    target_lines = [
        "package %s;" % pkg_path,
        "public final class %s {" % module.title().replace("_", ""),
        "    private %s() {}" % module.title().replace("_", ""),
    ]
    if branch_type == "Bug" and technique_code.upper() == "SX":
        target_lines.append("    private static final String hardcodedPassword = \"secret-token-12345\";")
    for i in range(1, n_fn + 1):
        target_lines.append(_java_case_method(prefix, i, variant, strength))
    target_lines.append("}")
    files["src/main/java/%s/%s.java" % (pkg_dir, module.title().replace("_", ""))] = "\n".join(target_lines)

    for m in tech["metrics"]:
        if m["metric_code"] == metric_code.upper() or m["module_key"] == metric["module_key"]:
            continue
        stub = textwrap.dedent(
            '''
            package %s;
            public final class %s {
                public static String stub() { return "stub-%s"; }
            }
            '''
        ) % (pkg_path, m["module_key"].title().replace("_", ""), m["module_key"])
        files["src/main/java/%s/%s.java" % (pkg_dir, m["module_key"].title().replace("_", ""))] = stub

    test_count = scaled_test_count(n_fn, branch_type, strength)
    tests = [
        "package %s;" % pkg_path,
        "import org.junit.Test;",
        "import static org.junit.Assert.*;",
        "public class %sTest {" % module.title().replace("_", ""),
    ]
    for i in range(1, test_count + 1):
        fn = "%sCase%d" % (prefix, min(i, n_fn))
        tests.append(
            "    @Test public void test%s() { assertNotNull(%s.%s(\"s%d\", true, %d, %d)); }"
            % (i, module.title().replace("_", ""), fn, i, i % 3, i % 5)
        )
    tests.append("}")
    files["src/test/java/%s/%sTest.java" % (pkg_dir, module.title().replace("_", ""))] = "\n".join(tests)

    if branch_type == "TCC":
        files["checkstyle.xml"] = "<module name=\"Checker\"/>\n"
    files["main.java"] = textwrap.dedent(
        '''
        public class Main {
            public static void main(String[] args) {
                System.out.println("Target metric: %s");
            }
        }
        '''
    ).strip() % metric_code
    return files, n_fn, pkg


def _js_like_files(tech, metric, technique_code, metric_code, branch_type, version, language, strength, ext, n_fn=None):
    pkg = package_name(technique_code).lower()
    variant = VARIANT_MAP[branch_type]
    prefix = metric_code.lower()
    module = metric["module_key"]
    if n_fn is None:
        n_fn = scaled_n_functions(DEFAULT_N_FUNCTIONS, strength)
    files = {}
    files["package.json"] = json.dumps(
        {"name": pkg, "version": "1.0.0", "type": "module", "scripts": {"test": "node tests/run.js"}},
        indent=2,
    ) + "\n"
    if ext == "ts":
        files["tsconfig.json"] = json.dumps({"compilerOptions": {"target": "ES2020", "module": "commonjs"}}, indent=2) + "\n"

    cfg_body = textwrap.dedent(
        '''
        {
          LANGUAGE: '%s',
          PYTHON_VERSION: '%s',
          BRANCH_TYPE: '%s',
          TARGET_TECHNIQUE: '%s',
          TARGET_METRIC_ABBREV: '%s',
        }
        '''
    ).strip() % (language, version, branch_type, technique_code.upper(), metric_code.upper())
    if ext == "ts":
        files["%s/config.ts" % pkg] = "const Config = %s;\nexport default Config;\n" % cfg_body
    else:
        files["%s/config.js" % pkg] = "module.exports = %s;\n" % cfg_body

    body = []
    if branch_type == "Bug" and technique_code.upper() == "SX":
        body.append("const hardcodedPassword = 'secret-token-12345';")
    if ext == "ts":
        body.append("export function %sCase1(state: string, enabled: boolean, retry: number, priority: number): string {" % prefix)
    else:
        body.append("function %sCase1(state, enabled, retry, priority) {" % prefix)
    mark = variant_marker(variant, 1, strength)
    body.append("  // %s" % mark)
    body.append("  let score = priority + retry;")
    body.append("  if (enabled && retry > %d) score += 3;" % (2 + effective_strength(strength)))
    body.append("  return state + '-' + '%s' + '-' + score;" % mark)
    body.append("}")
    for i in range(2, n_fn + 1):
        mark = variant_marker(variant, i, strength)
        body.append("function %sCase%d(state, enabled, retry, priority) {" % (prefix, i))
        body.append("  // %s" % mark)
        body.append("  let score = priority + retry + %d;" % i)
        body.append("  for (let j = 0; j < retry; j++) score += j % 3;")
        body.append("  return state + '-' + '%s' + '-' + score;" % mark)
        body.append("}")
    if ext == "ts":
        body.append("export { %sCase1 };" % prefix)
    else:
        body.append("module.exports = { %sCase1 };" % prefix)
    target_path = "%s/%s.%s" % (pkg, module, ext)
    files[target_path] = "\n".join(body) + "\n"

    for m in tech["metrics"]:
        if m["metric_code"] == metric_code.upper() or m["module_key"] == metric["module_key"]:
            continue
        stub = "module.exports = { stub: () => 'stub-%s' };\n" % m["module_key"]
        files["%s/%s.js" % (pkg, m["module_key"])] = stub

    test_count = scaled_test_count(n_fn, branch_type, strength)
    tests = ["const target = require('../%s/%s');\n" % (pkg, module)]
    for i in range(1, test_count + 1):
        fn = "%sCase%d" % (prefix, min(i, n_fn))
        tests.append("console.assert(target.%s('s%d', true, %d, %d) != null);\n" % (fn, i, i % 3, i % 5))
    files["tests/run.js"] = "".join(tests)
    files["main.js"] = "console.log('metric %s');\n" % metric_code
    if branch_type == "TCC":
        files[".eslintrc.json"] = '{"rules":{"complexity":["error",10]}}\n'
    return files, n_fn, pkg


def _csharp_files(tech, metric, technique_code, metric_code, branch_type, version, language, strength, n_fn=None):
    pkg = package_name(technique_code)
    variant = VARIANT_MAP[branch_type]
    prefix = metric_code.lower()
    module = metric["module_key"].title().replace("_", "")
    if n_fn is None:
        n_fn = scaled_n_functions(DEFAULT_N_FUNCTIONS, strength)
    ns = "Testable.%s" % pkg
    files = {}
    files["%s.csproj" % pkg] = textwrap.dedent(
        '''
        <Project Sdk="Microsoft.NET.Sdk">
          <PropertyGroup><TargetFramework>net8.0</TargetFramework></PropertyGroup>
        </Project>
        '''
    ).strip()

    cfg = textwrap.dedent(
        '''
        namespace %s {
          public static class Config {
            public const string LANGUAGE = "%s";
            public const string PYTHON_VERSION = "%s";
            public const string BRANCH_TYPE = "%s";
            public const string TARGET_TECHNIQUE = "%s";
            public const string TARGET_METRIC_ABBREV = "%s";
          }
        }
        '''
    ) % (ns, language, version, branch_type, technique_code.upper(), metric_code.upper())
    files["src/%s/Config.cs" % pkg] = cfg

    lines = ["namespace %s {" % ns, "public static class %s {" % module]
    if branch_type == "Bug" and technique_code.upper() == "SX":
        lines.append("  private const string hardcodedPassword = \"secret-token-12345\";")
    for i in range(1, n_fn + 1):
        mark = variant_marker(variant, i, strength)
        lines.append(
            "  public static string %sCase%d(string state, bool enabled, int retry, int priority) {" % (prefix, i)
        )
        lines.append("    // %s" % mark)
        lines.append("    int score = priority + retry + %d;" % i)
        lines.append("    for (int j = 0; j < retry; j++) score += j %% 3;")
        lines.append("    return state + \"-\" + \"%s\" + \"-\" + score;" % mark)
        lines.append("  }")
    lines.append("}")
    lines.append("}")
    files["src/%s/%s.cs" % (pkg, module)] = "\n".join(lines)

    for m in tech["metrics"]:
        if m["metric_code"] == metric_code.upper() or m["module_key"] == metric["module_key"]:
            continue
        stub = "namespace %s { public static class %s { public static string Stub() => \"stub\"; } }" % (
            ns, m["module_key"].title().replace("_", ""))
        files["src/%s/%s.cs" % (pkg, m["module_key"].title().replace("_", ""))] = stub + "\n"

    test_count = scaled_test_count(n_fn, branch_type, strength)
    tests = ["using Xunit;", "namespace %s {" % ns, "public class %sTests {" % module]
    for i in range(1, test_count + 1):
        fn = "%sCase%d" % (prefix, min(i, n_fn))
        tests.append("  [Fact] public void Test%d() { Assert.NotNull(%s.%s(\"s%d\", true, %d, %d)); }" % (
            i, module, fn, i, i % 3, i % 5))
    tests.append("}}")
    files["tests/%sTests.cs" % module] = "\n".join(tests)
    files["Program.cs"] = 'Console.WriteLine("metric %s");\n' % metric_code
    if branch_type == "TCC":
        files["coverlet.runsettings"] = textwrap.dedent(
            '''
            <?xml version="1.0" encoding="utf-8"?>
            <RunSettings>
              <DataCollectionRunSettings>
                <DataCollectors>
                  <DataCollector friendlyName="XPlat code coverage">
                    <Configuration><Exclude>[*]*.Tests</Exclude></Configuration>
                  </DataCollector>
                </DataCollectors>
              </DataCollectionRunSettings>
            </RunSettings>
            '''
        ).strip() + "\n"
    return files, n_fn, pkg


def generate_branch_files(technique_code, metric_code, branch_type, version="2.6", language="python", strength=0):
    strength = effective_strength(strength)
    lang = (language or "python").strip().lower()
    if lang == "python":
        from lib.python_generator import generate_branch_files as py_gen
        return py_gen(technique_code, metric_code, branch_type, version, language, strength=strength)

    tech = technique_by_code(technique_code)
    _, metric = metric_entry(technique_code, metric_code)
    bname = metrics_branch_name(technique_code, metric_code, branch_type, version)

    if lang == "java":
        builder = lambda nf: (
            _java_files(tech, metric, technique_code, metric_code, branch_type, version, lang, strength, n_fn=nf),
            (".java",),
            ("src/main/java", "src/test/java", "main.java"),
        )
    elif lang == "javascript":
        builder = lambda nf: (
            _js_like_files(tech, metric, technique_code, metric_code, branch_type, version, lang, strength, "js", n_fn=nf),
            (".js", ".json"),
            ("sa", "tests", "main.js", package_name(technique_code).lower()),
        )
    elif lang == "typescript":
        builder = lambda nf: (
            _js_like_files(tech, metric, technique_code, metric_code, branch_type, version, lang, strength, "ts", n_fn=nf),
            (".ts", ".js", ".json"),
            ("sa", "tests", "src", "main.js", package_name(technique_code).lower()),
        )
    elif lang in ("csharp", "c#"):
        lang = "csharp"
        builder = lambda nf: (
            _csharp_files(tech, metric, technique_code, metric_code, branch_type, version, lang, strength, n_fn=nf),
            (".cs",),
            ("src", "tests", "Program.cs"),
        )
    else:
        raise NotImplementedError("language %r not supported" % language)

    n_fn = scaled_n_functions(DEFAULT_N_FUNCTIONS, strength)
    files = None
    loc = 0
    while n_fn <= 200:
        (files, _, pkg), exts, prefixes = builder(n_fn)
        loc = _count_loc(files, exts, prefixes)
        if loc >= MIN_LOC:
            break
        n_fn += 8

    if loc < MIN_LOC:
        raise ValueError("Generated %s has only %d LOC (need >= %d)" % (bname, loc, MIN_LOC))

    files[".gen_meta.json"] = _gen_meta(strength, technique_code, metric_code, branch_type, version, lang, n_fn, loc, bname)
    return files


def write_branch(root, technique_code, metric_code, branch_type, version="2.6", language="python", strength=0):
    import os
    import shutil

    files = generate_branch_files(technique_code, metric_code, branch_type, version, language, strength=strength)
    if os.path.isdir(root):
        try:
            from lib.python_generator import _safe_rmtree
            _safe_rmtree(root)
        except ImportError:
            shutil.rmtree(root, ignore_errors=True)
    os.makedirs(root)
    for rel, content in files.items():
        path = os.path.join(root, rel)
        os.makedirs(os.path.dirname(path) or root, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
    from lib.python_generator import _count_loc as py_count_loc, read_gen_meta
    from lib.registry import package_name as pkg_name

    pkg = pkg_name(technique_code)
    loc = py_count_loc(files, pkg) if language == "python" else int(
        (read_gen_meta(root) or {}).get("loc") or 0
    )
    if not loc:
        loc = sum(content.count("\n") + 1 for content in files.values())
    bname = files.get(".gen_meta.json") and json.loads(files[".gen_meta.json"]).get("branch_name")
    if not bname:
        from lib.metrics import branch_name as bn
        bname = bn(technique_code, metric_code, branch_type, version)
    return bname, loc
