"""Full Java branch generator with per-technique/family parity."""

from __future__ import print_function

import textwrap

from lib.lang_generators.base import MIN_LOC, VARIANT_MAP, effective_strength, scaled_n_functions, scaled_test_count
from lib.lang_generators.case_emit import n_functions, variant_extra_java
from lib.lang_generators.meta_common import branch_label, config_fields, count_loc_files, gen_meta
from lib.registry import metric_entry, package_name, technique_by_code
from lib.registry_tools import get_metric_tools
from lib.tool_assert import tool_family


def _java_class_name(module_key):
    return module_key.title().replace("_", "")


def _java_case_method(prefix, idx, variant, metric_name, family, technique_code, strength):
    extra = variant_extra_java(prefix, idx, variant, family, technique_code, strength)
    return textwrap.dedent(
        '''
        public static String %(prefix)sCase%(idx)d(String state, boolean enabled, int retryCount, int priority) {
            if (state == null) throw new IllegalArgumentException("state required");
            if (retryCount < 0) retryCount = 0;
            int idx = %(idx)d;
            int severity = priority %% 5;
            boolean active = enabled;
            int score = (severity + idx) %% 7;
            if (!active && score < 2) return String.format("idle-%(prefix)s-%%s-%%d", state, idx);
            if (active && score >= 5) return String.format("active-%(prefix)s-%%s-%%d", state, idx);
        %(extra)s
            return String.format("default-%(prefix)s-%%s-%%d", state, idx);
        }
        '''
    ) % {"prefix": prefix, "idx": idx, "extra": extra}


def _pom_xml(pkg, runtime):
    release = (runtime or "17").strip()
    if release.lower().startswith("java"):
        release = release.split()[-1]
    return textwrap.dedent(
        '''
        <project xmlns="http://maven.apache.org/POM/4.0.0">
          <modelVersion>4.0.0</modelVersion>
          <groupId>com.testable</groupId>
          <artifactId>%(pkg)s</artifactId>
          <version>1.0.0</version>
          <properties>
            <maven.compiler.release>%(release)s</maven.compiler.release>
            <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
          </properties>
          <dependencies>
            <dependency>
              <groupId>org.junit.jupiter</groupId>
              <artifactId>junit-jupiter</artifactId>
              <version>5.10.2</version>
              <scope>test</scope>
            </dependency>
          </dependencies>
          <build>
            <plugins>
              <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-surefire-plugin</artifactId>
                <version>3.2.5</version>
              </plugin>
            </plugins>
          </build>
        </project>
        '''
    ).strip() % {"pkg": pkg, "release": release}


def _config_java(pkg_path, fields):
    return textwrap.dedent(
        '''
        package %(pkg_path)s;
        public final class Config {
            public static final String LANGUAGE = "%(language)s";
            public static final String RUNTIME_VERSION = "%(runtime)s";
            public static final String PYTHON_VERSION = "%(runtime)s";
            public static final String BRANCH_TYPE = "%(branch_type)s";
            public static final String TARGET_TECHNIQUE = "%(tech)s";
            public static final String TARGET_METRIC_ABBREV = "%(metric)s";
            public static final String TARGET_METRIC_NAME = "%(metric_name)s";
            public static final String TESTING_TYPE = "%(l2)s";
            public static final String TECHNIQUE = "%(l3)s";
        }
        '''
    ).strip() % dict(fields, pkg_path=pkg_path)


def _assemble_java_files(tech, metric, technique_code, metric_code, branch_type, version, language, runtime, strength, n_fn):
    pkg = package_name(technique_code).lower()
    pkg_path = "com.testable.%s" % pkg
    pkg_dir = pkg_path.replace(".", "/")
    variant = VARIANT_MAP[branch_type]
    prefix = metric_code.lower()
    module = _java_class_name(metric["module_key"])
    lang_tools = get_metric_tools(technique_code, metric_code, language)
    family = tool_family(lang_tools.get("primary") or "", technique_code)
    files = {}
    files["pom.xml"] = _pom_xml(pkg, runtime)
    cfg = config_fields(tech, metric, branch_type, version, language, runtime, lang_tools)
    files["src/main/java/%s/Config.java" % pkg_dir] = _config_java(pkg_path, cfg)

    target_lines = [
        "package %s;" % pkg_path,
        "public final class %s {" % module,
        "    private %s() {}" % module,
    ]
    for i in range(1, n_fn + 1):
        target_lines.append(_java_case_method(prefix, i, variant, metric["l5_metric"], family, technique_code, strength))
    target_lines.append("}")
    files["src/main/java/%s/%s.java" % (pkg_dir, module)] = "\n".join(target_lines)

    for m in tech["metrics"]:
        if m["metric_code"] == metric_code.upper():
            continue
        stub_cls = _java_class_name(m["module_key"])
        files["src/main/java/%s/%s.java" % (pkg_dir, stub_cls)] = textwrap.dedent(
            '''
            package %(pkg_path)s;
            public final class %(cls)s {
                public static String stub() { return "stub-%(key)s"; }
            }
            '''
        ).strip() % {"pkg_path": pkg_path, "cls": stub_cls, "key": m["module_key"]}

    test_count = scaled_test_count(n_fn, branch_type, strength)
    tests = [
        "package %s;" % pkg_path,
        "import org.junit.jupiter.api.Test;",
        "import static org.junit.jupiter.api.Assertions.*;",
        "public class %sTest {" % module,
    ]
    for i in range(1, test_count + 1):
        fn = "%sCase%d" % (prefix, min(i, n_fn))
        tests.append(
            "    @Test void test%d() { assertNotNull(%s.%s(\"s%d\", true, %d, %d)); }"
            % (i, module, fn, i, i % 3, i % 5)
        )
    tests.append("}")
    files["src/test/java/%s/%sTest.java" % (pkg_dir, module)] = "\n".join(tests)
    files["main.java"] = 'public class Main { public static void main(String[] args) { System.out.println("metric %s"); } }\n' % metric_code
    if branch_type == "TCC":
        files["checkstyle.xml"] = "<module name=\"Checker\"/>\n"
    return files


def generate_branch_files(technique_code, metric_code, branch_type, version="2.6", language="java", strength=0, runtime="17"):
    strength = effective_strength(strength)
    tech = technique_by_code(technique_code)
    _, metric = metric_entry(technique_code, metric_code)
    bname = branch_label(technique_code, metric_code, branch_type, version)
    n_fn = scaled_n_functions(n_functions(technique_code, metric_code), strength)
    files = None
    loc = 0
    while n_fn <= 200:
        files = _assemble_java_files(
            tech, metric, technique_code, metric_code, branch_type, version, language, runtime, strength, n_fn,
        )
        loc = count_loc_files(files, (".java",), ("src/main/java", "src/test/java", "main.java"))
        if loc >= MIN_LOC:
            break
        n_fn += 8
    if loc < MIN_LOC:
        raise ValueError("Generated %s has only %d LOC (need >= %d)" % (bname, loc, MIN_LOC))
    files[".gen_meta.json"] = gen_meta(
        strength, technique_code, metric_code, branch_type, version, language, runtime, n_fn, loc, bname,
    )
    return files
