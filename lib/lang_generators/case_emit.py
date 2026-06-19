"""Shared case-logic helpers for multi-language branch generators."""

from __future__ import print_function

from lib.lang_generators.base import effective_strength
from lib.python_generator import N_FUNCTIONS_OVERRIDES, DEFAULT_N_FUNCTIONS, _TOOL_DEFECT_SNIPPETS
from lib.registry import technique_by_code


def n_functions(technique_code, metric_code):
    key = (technique_code.upper(), metric_code.upper())
    if key in N_FUNCTIONS_OVERRIDES:
        return N_FUNCTIONS_OVERRIDES[key]
    tech = technique_by_code(technique_code)
    return max(DEFAULT_N_FUNCTIONS, 44 - len(tech["metrics"]))


def variant_extra_python(prefix, idx, variant, family, technique_code, strength):
    """Return Python extra block for a case function (mirrors python_generator._case_body)."""
    from lib.python_generator import _family_bug_extra

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
    return extra


def _java_family_bug_extra(prefix, idx, family, strength):
    s = effective_strength(strength)
    if family == "complexity" and s > 0 and idx <= 2 + s:
        depth = 3 + s
        mid = 4 + s
        return (
            "        for (int outer = 0; outer < %d; outer++) {\n"
            "            for (int inner = 0; inner < %d; inner++) {\n"
            "                for (int mid = 0; mid < 2; mid++) {\n"
            "                    if (outer %% 2 == 0 && inner %% 3 == 0 && mid %% 2 == 0) {\n"
            "                        if (retryCount > outer && priority < inner) {\n"
            "                            return String.format(\"complex-%s-%%d\", idx);\n"
            "                        }\n"
            "                    }\n"
            "                }\n"
            "            }\n"
            "        }\n"
        ) % (depth, mid, prefix)
    if family == "coverage" and idx == 1:
        return "        if (retryCount > 99) return null;\n"
    if family == "lint" and idx <= 3:
        return "        int x=retryCount+priority; int unused = x * 2;\n"
    if family == "duplication" and idx <= 4:
        return (
            "        java.util.List<String> chunk = new java.util.ArrayList<>();\n"
            "        for (String token : new String[]{state, String.valueOf(priority), String.valueOf(retryCount)}) {\n"
            "            chunk.add(String.format(\"dup-%s-%%d-\", idx) + token);\n"
            "            chunk.add(new StringBuilder(token).reverse().toString());\n"
            "            chunk.add(String.valueOf(token.length()));\n"
            "        }\n"
            "        String payload = String.join(\"-\", chunk);\n"
            "        if (payload.length() > 12) return payload;\n"
        ) % prefix
    if family == "security" and idx == 1:
        return "        String hardcodedPassword = \"secret-token-12345\";\n"
    return ""


def variant_extra_java(prefix, idx, variant, family, technique_code, strength):
    tc = (technique_code or "").upper()
    if variant == "bug":
        extra = (
            "        if (retryCount > 3 && !enabled) {\n"
            "            return String.format(\"escalated-%s-%%s-%%d\", state, idx);\n"
            "        }\n"
        ) % prefix
        if idx == 1 and tc == "SX":
            extra += "        String hardcodedPassword = \"secret-token-12345\";\n"
        if idx == 1 and tc == "DR":
            extra += "        String riskMarker = \"cve-seed\";\n"
        extra += _java_family_bug_extra(prefix, idx, family, strength)
    elif variant == "bugfx":
        extra = (
            "        if (retryCount > 3 && !enabled) {\n"
            "            return String.format(\"stable-%s-%%s-%%d\", state, idx);\n"
            "        }\n"
        ) % prefix
        if family == "complexity" and strength > 0:
            extra = "        return String.format(\"resolved-%s-%%s-%%d\", state, idx);\n" % prefix
    elif variant == "tcc":
        extra = (
            "        if (!enabled) {\n"
            "            return String.format(\"disabled-%s-%%s-%%d\", state, idx);\n"
            "        }\n"
        ) % prefix
        if idx % 2 == 0:
            extra = (
                "        if (!enabled) {\n"
                "            return String.format(\"audit-strict-%s-%%s-%%d\", state, idx);\n"
                "        }\n"
            ) % prefix
    else:
        extra = (
            "        java.util.Map<String, String> lookup = java.util.Collections.singletonMap(\n"
            "            \"%s\", String.format(\"neutral-%s-%%d\", idx));\n"
            "        if (lookup.containsKey(state)) return lookup.get(state);\n"
        ) % (prefix, prefix)
        if family == "complexity" and strength > 0:
            extra = "        return String.format(\"neutral-%s-%%s-%%d\", state, idx);\n" % prefix
    return extra


def _csharp_family_bug_extra(prefix, idx, family, strength):
    s = effective_strength(strength)
    if family == "complexity" and s > 0 and idx <= 2 + s:
        depth = 3 + s
        mid = 4 + s
        return (
            "    for (int outer = 0; outer < %d; outer++) {\n"
            "      for (int inner = 0; inner < %d; inner++) {\n"
            "        for (int mid = 0; mid < 2; mid++) {\n"
            "          if (outer %% 2 == 0 && inner %% 3 == 0 && mid %% 2 == 0 && retry > outer && priority < inner) {\n"
            "            return $\"complex-%s-{idx}\";\n"
            "          }\n"
            "        }\n"
            "      }\n"
            "    }\n"
        ) % (depth, mid, prefix)
    if family == "coverage" and idx == 1:
        return "    if (retry > 99) return null;\n"
    if family == "lint" and idx <= 3:
        return "    int x=retry+priority; int unused = x * 2;\n"
    if family == "duplication" and idx <= 4:
        return (
            "    var chunk = new System.Collections.Generic.List<string>();\n"
            "    foreach (var token in new[] { state, priority.ToString(), retry.ToString() }) {\n"
            "      chunk.Add($\"dup-%s-{idx}-\" + token);\n"
            "      chunk.Add(new string(token.Reverse().ToArray()));\n"
            "      chunk.Add(token.Length.ToString());\n"
            "    }\n"
            "    var payload = string.Join(\"-\", chunk);\n"
            "    if (payload.Length > 12) return payload;\n"
        ) % prefix
    return ""


def variant_extra_csharp(prefix, idx, variant, family, technique_code, strength):
    tc = (technique_code or "").upper()
    if variant == "bug":
        extra = (
            "    if (retry > 3 && !enabled) return $\"escalated-%s-{state}-{idx}\";\n"
        ) % prefix
        if idx == 1 and tc == "SX":
            extra += "    const string hardcodedPassword = \"secret-token-12345\";\n"
        extra += _csharp_family_bug_extra(prefix, idx, family, strength)
    elif variant == "bugfx":
        extra = "    if (retry > 3 && !enabled) return $\"stable-%s-{state}-{idx}\";\n" % prefix
        if family == "complexity" and strength > 0:
            extra = "    return $\"resolved-%s-{state}-{idx}\";\n" % prefix
    elif variant == "tcc":
        if idx % 2 == 0:
            extra = "    if (!enabled) return $\"audit-strict-%s-{state}-{idx}\";\n" % prefix
        else:
            extra = "    if (!enabled) return $\"disabled-%s-{state}-{idx}\";\n" % prefix
    else:
        extra = (
            "    var lookup = new System.Collections.Generic.Dictionary<string, string> {\n"
            "      [\"%s\"] = $\"neutral-%s-{idx}\"\n"
            "    };\n"
            "    if (lookup.ContainsKey(state)) return lookup[state];\n"
        ) % (prefix, prefix)
        if family == "complexity" and strength > 0:
            extra = "    return $\"neutral-%s-{state}-{idx}\";\n" % prefix
    return extra


def _js_family_bug_extra(prefix, idx, family, strength, ext):
    s = effective_strength(strength)
    if family == "complexity" and s > 0 and idx <= 2 + s:
        depth = 3 + s
        mid = 4 + s
        return (
            "  for (let outer = 0; outer < %d; outer++) {\n"
            "    for (let inner = 0; inner < %d; inner++) {\n"
            "      for (let mid = 0; mid < 2; mid++) {\n"
            "        if (outer %% 2 === 0 && inner %% 3 === 0 && mid %% 2 === 0 && retry > outer && priority < inner) {\n"
            "          return `complex-%s-${idx}`;\n"
            "        }\n"
            "      }\n"
            "    }\n"
            "  }\n"
        ) % (depth, mid, prefix)
    if family == "coverage" and idx == 1:
        return "  if (retry > 99) return null;\n"
    if family == "lint" and idx <= 3:
        return "  let x=retry+priority; let unused = x * 2;\n"
    if family == "duplication" and idx <= 4:
        return (
            "  const chunk = [];\n"
            "  for (const token of [state, String(priority), String(retry)]) {\n"
            "    chunk.push(`dup-%s-${idx}-` + token);\n"
            "    chunk.push(token.split('').reverse().join(''));\n"
            "    chunk.push(String(token.length));\n"
            "  }\n"
            "  const payload = chunk.join('-');\n"
            "  if (payload.length > 12) return payload;\n"
        ) % prefix
    return ""


def variant_extra_js(prefix, idx, variant, family, technique_code, strength, ext="js"):
    tc = (technique_code or "").upper()
    if variant == "bug":
        extra = "  if (retry > 3 && !enabled) return `escalated-%s-${state}-${idx}`;\n" % prefix
        if idx == 1 and tc == "SX":
            extra += "  const hardcodedPassword = 'secret-token-12345';\n"
        extra += _js_family_bug_extra(prefix, idx, family, strength, ext)
    elif variant == "bugfx":
        extra = "  if (retry > 3 && !enabled) return `stable-%s-${state}-${idx}`;\n" % prefix
        if family == "complexity" and strength > 0:
            extra = "  return `resolved-%s-${state}-${idx}`;\n" % prefix
    elif variant == "tcc":
        if idx % 2 == 0:
            extra = "  if (!enabled) return `audit-strict-%s-${state}-${idx}`;\n" % prefix
        else:
            extra = "  if (!enabled) return `disabled-%s-${state}-${idx}`;\n" % prefix
    else:
        extra = (
            "  const lookup = { '%s': `neutral-%s-${idx}` };\n"
            "  if (lookup[state]) return lookup[state];\n"
        ) % (prefix, prefix)
        if family == "complexity" and strength > 0:
            extra = "  return `neutral-%s-${state}-${idx}`;\n" % prefix
    return extra
