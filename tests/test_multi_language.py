"""Tests for multi-language generation and runtime version support."""

from __future__ import print_function

import json
import os
import shutil
import tempfile
import unittest

from lib.branch_pipeline import branch_materialized, generate_branches
from lib.branch_post_verify import verify_generated_branch
from lib.lang_support import (
    branch_language,
    branch_language_by_name,
    default_runtime,
    language_runtimes,
    normalize_runtime,
)
from lib.lang_generators import write_branch
from lib.lang_tool_runners import toolchain_available
from lib.registry_tools import get_metric_tools, SUPPORTED_UI_LANGUAGES


class LangSupportTests(unittest.TestCase):
    def test_all_ui_languages_have_runtimes(self):
        for lang in SUPPORTED_UI_LANGUAGES:
            runtimes = language_runtimes(lang)
            self.assertTrue(runtimes, lang)
            self.assertIn(default_runtime(lang), runtimes)

    def test_normalize_runtime_fallback(self):
        self.assertEqual(normalize_runtime("java", "99"), default_runtime("java"))

    def test_branch_language_from_gen_meta(self):
        base = tempfile.mkdtemp(prefix="ml_lang_")
        try:
            root = os.path.join(base, "branch")
            os.makedirs(root)
            meta = {"language": "java", "runtime": "17"}
            with open(os.path.join(root, ".gen_meta.json"), "w", encoding="utf-8") as fh:
                json.dump(meta, fh)
            self.assertEqual(branch_language(root), "java")
            self.assertEqual(branch_language(root, fallback="python"), "java")
        finally:
            shutil.rmtree(base, ignore_errors=True)

    def test_branch_language_by_name_fallback(self):
        repo = tempfile.mkdtemp(prefix="ml_repo_")
        try:
            by_name = branch_language_by_name(["Missing_Branch"], repo, fallback="csharp")
            self.assertEqual(by_name["Missing_Branch"], "csharp")
        finally:
            shutil.rmtree(repo, ignore_errors=True)


class ToolchainAvailabilityTests(unittest.TestCase):
    def test_toolchain_python_always_available(self):
        ok, _msg = toolchain_available("python")
        self.assertTrue(ok)

    def test_toolchain_returns_tuple(self):
        for lang in SUPPORTED_UI_LANGUAGES:
            result = toolchain_available(lang)
            self.assertIsInstance(result, tuple)
            self.assertEqual(len(result), 2)
            self.assertIsInstance(result[0], bool)
            self.assertIsInstance(result[1], str)


class RegistryToolsMultiLangTests(unittest.TestCase):
    def test_metric_tools_resolved_for_each_language(self):
        for lang in SUPPORTED_UI_LANGUAGES:
            info = get_metric_tools("SA", "DOV", lang)
            self.assertEqual(info["language"], lang)
            self.assertTrue(info["primary"])
            self.assertNotEqual(info["family"], "unknown")


class MultiLanguageGenerationTests(unittest.TestCase):
    CASES = [
        ("python", "3.12"),
        ("java", "17"),
        ("csharp", "net8.0"),
        ("typescript", "5.4"),
        ("javascript", "Node 20"),
    ]

    def test_generate_and_verify_sa_dov_bug(self):
        from lib.metrics import branch_name
        for language, runtime in self.CASES:
            base = tempfile.mkdtemp(prefix="ml_%s_" % language)
            root = os.path.join(base, branch_name("SA", "DOV", "Bug", "2.6"))
            try:
                bname, loc = write_branch(
                    root, "SA", "DOV", "Bug", "2.6", language, strength=4, runtime=runtime,
                )
                self.assertGreater(loc, 0, language)
                self.assertTrue(branch_materialized(root, "SA", language), language)
                vr = verify_generated_branch(root, "SA", "DOV", "Bug", "2.6", language)
                self.assertTrue(vr.get("ok"), "%s: %s" % (language, vr.get("messages")))
                with open(os.path.join(root, ".gen_meta.json"), encoding="utf-8") as fh:
                    import json
                    meta = json.load(fh)
                self.assertEqual(meta.get("language"), language)
                self.assertEqual(meta.get("runtime"), runtime)
            finally:
                shutil.rmtree(base, ignore_errors=True)

    def test_cc_complexity_neutral_marker_java(self):
        from lib.metrics import branch_name
        base = tempfile.mkdtemp(prefix="ml_java_cc_")
        root = os.path.join(base, branch_name("RM", "HCL", "CC", "2.6"))
        try:
            write_branch(root, "RM", "HCL", "CC", "2.6", "java", strength=4, runtime="17")
            from lib.registry import metric_entry
            _, metric = metric_entry("RM", "HCL")
            cls = metric["module_key"].title().replace("_", "")
            target = os.path.join(root, "src/main/java/com/testable/rm/%s.java" % cls)
            self.assertTrue(os.path.isfile(target), target)
            src = open(target, encoding="utf-8").read()
            self.assertIn("neutral-", src)
            vr = verify_generated_branch(root, "RM", "HCL", "CC", "2.6", "java")
            self.assertTrue(vr.get("ok"), vr.get("messages"))
        finally:
            shutil.rmtree(base, ignore_errors=True)

    def test_generate_branches_java_subset(self):
        root = tempfile.mkdtemp(prefix="ml_gen_")
        try:
            result = generate_branches(
                "SA", "DOV", "Bug", "2.6", "java", root, clear_existing=True, runtime="17",
            )
            self.assertTrue(result.get("success"), result.get("stop_reason"))
            self.assertEqual(len(result.get("generated", [])), 1)
        finally:
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
