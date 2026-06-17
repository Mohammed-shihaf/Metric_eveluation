"""Language capability flags for UI gating."""

from __future__ import print_function

from lib.registry_tools import SUPPORTED_UI_LANGUAGES

# Testable whitebox: Python confirmed; others enabled when WHITEBOX_LANGUAGES env includes them.
import os as _os

_DEFAULT_WB = "python,java,javascript,typescript,csharp"
WHITEBOX_READY = {
    x.strip().lower()
    for x in _os.environ.get("WHITEBOX_LANGUAGES", _DEFAULT_WB).split(",")
    if x.strip()
}


def language_readiness(language):
    lang = (language or "python").strip().lower()
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
