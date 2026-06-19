"""Full C# branch generator with per-technique/family parity."""

from __future__ import print_function

import textwrap

from lib.lang_generators.base import MIN_LOC, VARIANT_MAP, effective_strength, scaled_n_functions, scaled_test_count
from lib.lang_generators.case_emit import n_functions, variant_extra_csharp
from lib.lang_generators.meta_common import branch_label, config_fields, count_loc_files, gen_meta
from lib.registry import metric_entry, package_name, technique_by_code
from lib.registry_tools import get_metric_tools
from lib.tool_assert import tool_family


def _csharp_class_name(module_key):
    return module_key.title().replace("_", "")


def _csharp_case_method(prefix, idx, variant, family, technique_code, strength):
    extra = variant_extra_csharp(prefix, idx, variant, family, technique_code, strength)
    return textwrap.dedent(
        '''
        public static string %(prefix)sCase%(idx)d(string state, bool enabled, int retry, int priority) {
          if (state == null) throw new System.ArgumentException("state required");
          if (retry < 0) retry = 0;
          int idx = %(idx)d;
          int severity = priority %% 5;
          bool active = enabled;
          int score = (severity + idx) %% 7;
          if (!active && score < 2) return $"idle-%(prefix)s-{state}-{idx}";
          if (active && score >= 5) return $"active-%(prefix)s-{state}-{idx}";
        %(extra)s
          return $"default-%(prefix)s-{state}-{idx}";
        }
        '''
    ) % {"prefix": prefix, "idx": idx, "extra": extra}


def _csproj(pkg, runtime):
    tfm = (runtime or "net8.0").strip()
    if not tfm.startswith("net"):
        tfm = "net%s" % tfm
    return textwrap.dedent(
        '''
        <Project Sdk="Microsoft.NET.Sdk">
          <PropertyGroup>
            <TargetFramework>%(tfm)s</TargetFramework>
            <ImplicitUsings>enable</ImplicitUsings>
            <Nullable>enable</Nullable>
          </PropertyGroup>
          <ItemGroup>
            <PackageReference Include="Microsoft.NET.Test.Sdk" Version="17.11.1" />
            <PackageReference Include="xunit" Version="2.9.2" />
            <PackageReference Include="xunit.runner.visualstudio" Version="2.8.2" />
            <PackageReference Include="coverlet.collector" Version="6.0.2" />
          </ItemGroup>
        </Project>
        '''
    ).strip() % {"tfm": tfm}


def _config_cs(ns, fields):
    return textwrap.dedent(
        '''
        namespace %(ns)s {
          public static class Config {
            public const string LANGUAGE = "%(language)s";
            public const string RUNTIME_VERSION = "%(runtime)s";
            public const string PYTHON_VERSION = "%(runtime)s";
            public const string BRANCH_TYPE = "%(branch_type)s";
            public const string TARGET_TECHNIQUE = "%(tech)s";
            public const string TARGET_METRIC_ABBREV = "%(metric)s";
            public const string TARGET_METRIC_NAME = "%(metric_name)s";
            public const string TESTING_TYPE = "%(l2)s";
            public const string TECHNIQUE = "%(l3)s";
          }
        }
        '''
    ).strip() % dict(fields, ns=ns)


def _assemble_csharp_files(tech, metric, technique_code, metric_code, branch_type, version, language, runtime, strength, n_fn):
    pkg = package_name(technique_code)
    variant = VARIANT_MAP[branch_type]
    prefix = metric_code.lower()
    module = _csharp_class_name(metric["module_key"])
    ns = "Testable.%s" % pkg
    lang_tools = get_metric_tools(technique_code, metric_code, language)
    family = tool_family(lang_tools.get("primary") or "", technique_code)
    files = {}
    files["%s.csproj" % pkg] = _csproj(pkg, runtime)
    cfg = config_fields(tech, metric, branch_type, version, language, runtime, lang_tools)
    files["src/%s/Config.cs" % pkg] = _config_cs(ns, cfg)

    lines = ["namespace %s {" % ns, "public static class %s {" % module]
    for i in range(1, n_fn + 1):
        lines.append(_csharp_case_method(prefix, i, variant, family, technique_code, strength))
    lines.extend(["}", "}"])
    files["src/%s/%s.cs" % (pkg, module)] = "\n".join(lines)

    for m in tech["metrics"]:
        if m["metric_code"] == metric_code.upper():
            continue
        stub_cls = _csharp_class_name(m["module_key"])
        files["src/%s/%s.cs" % (pkg, stub_cls)] = (
            "namespace %s { public static class %s { public static string Stub() => \"stub-%s\"; } }\n"
            % (ns, stub_cls, m["module_key"])
        )

    test_count = scaled_test_count(n_fn, branch_type, strength)
    tests = ["using Xunit;", "namespace %s {" % ns, "public class %sTests {" % module]
    for i in range(1, test_count + 1):
        fn = "%sCase%d" % (prefix, min(i, n_fn))
        tests.append(
            "  [Fact] public void Test%d() { Assert.NotNull(%s.%s(\"s%d\", true, %d, %d)); }"
            % (i, module, fn, i, i % 3, i % 5)
        )
    tests.append("}}")
    files["tests/%sTests.cs" % module] = "\n".join(tests)
    files["Program.cs"] = 'Console.WriteLine("metric %s");\n' % metric_code
    if branch_type == "TCC":
        files["coverlet.runsettings"] = (
            '<?xml version="1.0" encoding="utf-8"?><RunSettings><DataCollectionRunSettings>'
            '<DataCollectors><DataCollector friendlyName="XPlat code coverage">'
            '<Configuration><Exclude>[*]*.Tests</Exclude></Configuration></DataCollector>'
            '</DataCollectors></DataCollectionRunSettings></RunSettings>\n'
        )
    return files


def generate_branch_files(technique_code, metric_code, branch_type, version="2.6", language="csharp", strength=0, runtime="net8.0"):
    strength = effective_strength(strength)
    tech = technique_by_code(technique_code)
    _, metric = metric_entry(technique_code, metric_code)
    bname = branch_label(technique_code, metric_code, branch_type, version)
    n_fn = scaled_n_functions(n_functions(technique_code, metric_code), strength)
    files = None
    loc = 0
    while n_fn <= 200:
        files = _assemble_csharp_files(
            tech, metric, technique_code, metric_code, branch_type, version, language, runtime, strength, n_fn,
        )
        loc = count_loc_files(files, (".cs",), ("src", "tests", "Program.cs"))
        if loc >= MIN_LOC:
            break
        n_fn += 8
    if loc < MIN_LOC:
        raise ValueError("Generated %s has only %d LOC (need >= %d)" % (bname, loc, MIN_LOC))
    files[".gen_meta.json"] = gen_meta(
        strength, technique_code, metric_code, branch_type, version, language, runtime, n_fn, loc, bname,
    )
    return files
