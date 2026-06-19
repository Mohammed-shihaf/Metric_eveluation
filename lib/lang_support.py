"""Language capability flags and runtime version catalog for UI gating."""

from __future__ import print_function

import os as _os

from lib.registry_tools import SUPPORTED_UI_LANGUAGES

_DEFAULT_WB = "python,java,javascript,typescript,csharp"
WHITEBOX_READY = {
    x.strip().lower()
    for x in _os.environ.get("WHITEBOX_LANGUAGES", _DEFAULT_WB).split(",")
    if x.strip()
}

# Per-language runtime/toolchain versions exposed in the UI.
LANGUAGE_RUNTIMES = {
    "python": ("3.10", "3.11", "3.12", "3.13"),
    "java": ("11", "17", "21"),
    "csharp": ("net6.0", "net7.0", "net8.0"),
    "typescript": ("5.3", "5.4", "5.5"),
    "javascript": ("Node 18", "Node 20", "Node 22"),
}

DEFAULT_RUNTIME = {
    "python": "3.12",
    "java": "17",
    "csharp": "net8.0",
    "typescript": "5.4",
    "javascript": "Node 20",
}


def normalize_language(language):
    lang = (language or "python").strip().lower()
    if lang == "c#":
        return "csharp"
    return lang


def language_runtimes(language):
    """Return supported runtime versions for a language."""
    lang = normalize_language(language)
    return list(LANGUAGE_RUNTIMES.get(lang, LANGUAGE_RUNTIMES["python"]))


def default_runtime(language):
    """Default runtime version for a language."""
    lang = normalize_language(language)
    return DEFAULT_RUNTIME.get(lang, DEFAULT_RUNTIME["python"])


def normalize_runtime(language, runtime):
    """Validate and normalize a runtime selection."""
    lang = normalize_language(language)
    runtimes = language_runtimes(lang)
    rt = (runtime or "").strip()
    if rt in runtimes:
        return rt
    return default_runtime(lang)


def language_readiness(language):
    lang = normalize_language(language)
    return {
        "generate": lang in SUPPORTED_UI_LANGUAGES,
        "validate": lang in SUPPORTED_UI_LANGUAGES,
        "whitebox": lang in WHITEBOX_READY,
        "label": lang,
    }


def sidebar_language_caption(language):
    info = language_readiness(language)
    if not info["generate"]:
        return "Language **%s** is not supported yet." % language
    parts = ["Generate + validate enabled"]
    if info["whitebox"]:
        parts.append("whitebox enabled")
    else:
        parts.append("whitebox pending platform support")
    return "**%s**: %s." % (language, ", ".join(parts))
