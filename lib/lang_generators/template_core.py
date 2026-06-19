"""Template-based multi-language branch file generation — dispatches to full generators."""

from __future__ import print_function

import json
import os
import shutil

from lib.lang_generators.base import effective_strength
from lib.lang_support import default_runtime, normalize_language, normalize_runtime
from lib.metrics import branch_name as metrics_branch_name


def generate_branch_files(
    technique_code, metric_code, branch_type, version="2.6", language="python",
    strength=0, runtime=None,
):
    strength = effective_strength(strength)
    lang = normalize_language(language)
    rt = normalize_runtime(lang, runtime or default_runtime(lang))
    if lang == "python":
        from lib.python_generator import generate_branch_files as py_gen
        return py_gen(technique_code, metric_code, branch_type, version, lang, strength=strength, runtime=rt)
    if lang == "java":
        from lib.lang_generators.java import generate_branch_files as java_gen
        return java_gen(technique_code, metric_code, branch_type, version, lang, strength=strength, runtime=rt)
    if lang == "csharp":
        from lib.lang_generators.csharp import generate_branch_files as cs_gen
        return cs_gen(technique_code, metric_code, branch_type, version, lang, strength=strength, runtime=rt)
    if lang in ("javascript", "typescript"):
        from lib.lang_generators.ts_js import generate_branch_files as js_gen
        return js_gen(technique_code, metric_code, branch_type, version, lang, strength=strength, runtime=rt)
    raise NotImplementedError("language %r not supported" % language)


def write_branch(
    root, technique_code, metric_code, branch_type, version="2.6", language="python",
    strength=0, runtime=None,
):
    lang = normalize_language(language)
    rt = normalize_runtime(lang, runtime or default_runtime(lang))
    files = generate_branch_files(
        technique_code, metric_code, branch_type, version, lang, strength=strength, runtime=rt,
    )
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
    from lib.python_generator import read_gen_meta

    meta = read_gen_meta(root) or {}
    loc = int(meta.get("loc") or 0)
    if not loc:
        loc = sum(content.count("\n") + 1 for content in files.values())
    bname = meta.get("branch_name")
    if not bname:
        bname = metrics_branch_name(technique_code, metric_code, branch_type, version)
    return bname, loc
