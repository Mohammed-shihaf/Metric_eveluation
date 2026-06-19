# Module Reference

Developer-oriented map of the `Metric_evaluation` codebase.

---

## 1. Repository structure

```
Metric_evaluation/
├── ui/
│   ├── app.py              # Streamlit application (main entry)
│   └── assets/logo.png
├── lib/
│   ├── branch_pipeline.py  # Generate → validate → push orchestration
│   ├── python_generator.py # Python branch codegen
│   ├── lang_generators/    # Java, C#, TS/JS generators
│   ├── tool_assert.py      # Run tools + branch-type asserts
│   ├── report_schema.py    # Normalize S3/local report JSON
│   ├── validate.py         # Single-branch structural validation
│   ├── validate_multi.py   # Multi-branch validation loop
│   ├── registry.py         # metrics_registry.yaml queries
│   ├── proofs.py           # Proof collection + comparison readiness
│   ├── compare.py          # Field-level diff logic
│   ├── compare_export.py   # Excel workbook builder
│   ├── sa_qa.py            # Testable QA API client
│   ├── s3_sync.py          # AWS S3 download + parse
│   ├── github_api.py       # Branch fetch/push
│   ├── github_auth.py      # OAuth + PAT resolution
│   ├── scm/                # Connection store + OAuth flow
│   ├── sonar_runner.py     # Docker SonarQube integration
│   └── ...
├── config/
│   └── metrics_registry.yaml
├── tests/
├── tools/
│   ├── e2e_browser_verify.py
│   └── capture_docs_screenshots.py
├── notebooks/
└── Testabel_Assurance_Studio_Docs/
```

---

## 2. Entry points

| Entry | Command | Purpose |
|-------|---------|---------|
| Streamlit UI | `streamlit run ui/app.py` | Primary user interface |
| Pytest | `pytest tests/` | Unit and integration tests |
| E2E | `python tools/e2e_browser_verify.py` | Browser smoke test |
| Notebooks | Jupyter | Scripted pipeline without UI |

---

## 3. Core modules

### 3.1 `ui/app.py`

Streamlit presentation layer. Key functions:

| Function | Tab | Role |
|----------|-----|------|
| `_sidebar_filters()` | Sidebar | Scope selection, language/runtime |
| `_tab_branches()` | Branches | Generate / validate / push UI |
| `_tab_whitebox()` | Whitebox | QA batch, taxonomy, S3 |
| `_tab_local_tools()` | Local tools | Tool install + local execution |
| `_tab_sonar()` | SonarQube | Docker scan UI |
| `_tab_comparison()` | Compare | Diff view + Excel export |
| `_pipeline_scope_key()` | — | Cache invalidation on filter change |

Session state keys: `gen_rows`, `validate_rows`, `pipeline_*_status`, `last_comparisons`.

### 3.2 `lib/branch_pipeline.py`

Central orchestrator.

| Function | Description |
|----------|-------------|
| `generate_branches()` | Iterate registry scope, call language generator |
| `validate_branches()` | Run structural + tool asserts |
| `validate_with_regeneration()` | Fix-until-pass with strength escalation |
| `push_branches()` | Push validated dirs to GitHub |
| `branch_materialized()` | Language-aware check for generated source |
| `pipeline_work_dir()` | Per-user isolated work directory |
| `hydrate_gen_rows_from_work()` | Restore state after Streamlit rerun |

### 3.3 `lib/python_generator.py`

Full Python codegen: technique packages, target metric module, stub modules, tests, config, branch-type markers (`bug-`, `fix-`, `tcc-`, `neutral-`), `.gen_meta.json`.

### 3.4 `lib/lang_generators/`

| Module | Language |
|--------|----------|
| `java.py` | Java (Maven, JUnit 5) |
| `csharp.py` | C# (xUnit, coverlet) |
| `ts_js.py` | TypeScript + JavaScript |
| `case_emit.py` | Shared branch-type body emission |
| `meta_common.py` | Shared `.gen_meta.json` fields |
| `template_core.py` | Dispatch by language |

### 3.5 `lib/registry.py`

YAML registry access:

| Function | Purpose |
|----------|---------|
| `load_registry()` | Cached YAML load |
| `iter_branches()` | Yield (tech, metric, type, branch_name) for scope |
| `parse_qualified_metrics()` | Parse `TECH:CODE` filter tokens |
| `parse_metrics_filter()` | Apply metric filter per technique |
| `metric_entry()` | Lookup technique + metric metadata |

### 3.6 `lib/tool_assert.py`

| Function | Purpose |
|----------|---------|
| `metric_violation()` | Single source of truth for FAIL/PASS/WARN |
| `run_tool_assert()` | Execute primary tool, return raw values |
| `tool_outcome_for_branch()` | Branch-type-aware expected outcome |

Tool families: coverage, complexity, lint, security, sca, mutation, churn, duplication, crosshair, pymcdc, testmon.

### 3.7 `lib/report_schema.py`

Normalizes heterogeneous tool output into canonical report JSON:

| Function | Purpose |
|----------|---------|
| `from_tool_assert_result()` | Build report from local assert |
| `_status_from_metric_values()` | Derive status; prefers `tool_outcome` when real tool ran |
| `normalize_s3_report()` | Parse S3 bundle format |

### 3.8 `lib/proofs.py`

| Function | Purpose |
|----------|---------|
| `whitebox_completion()` | Per-branch whitebox status map |
| `collect_s3_proof()` | Download + parse S3 bundle |
| `collect_local_batch()` | Run local tools for scope |
| `collect_comparison_proof()` | Build comparison.json |
| `compare_readiness()` | What reports exist per branch |
| `load_proof_bundle()` | Load all artifacts for a branch |

### 3.9 `lib/compare_export.py`

Excel export with:

- `_difference_rows()` — field-level mismatches
- `_summary_mismatch_detail()` — human-readable summary
- Green/red row highlighting via openpyxl

### 3.10 `lib/sa_qa.py`

Testable QA integration: login, catalog sync, run creation, polling, taxonomy HTML export.

### 3.11 `lib/s3_sync.py`

AWS S3 listing, download, JSON extraction for tool reports.

### 3.12 `lib/scm/`

| Module | Purpose |
|--------|---------|
| `connection_service.py` | GitHub OAuth token management |
| `store.py` | SQLite encrypted token storage |

---

## 4. Configuration

### `config/metrics_registry.yaml`

Schema (simplified):

```yaml
version: '3.1'
branch_types: [Bug, BugFX, TCC, CC]
techniques:
  - technique_code: SA
    metrics:
      - metric_code: DOV
        module_key: decision_outcome_verification
        branch_slug: Decision-Outcome-Verification
        tools:
          python:
            primary: Coverage.py
            secondary: Mccabe
          java:
            primary: JaCoCo
```

Regenerate summary: see [METRICS_REGISTRY_SUMMARY.md](METRICS_REGISTRY_SUMMARY.md).

---

## 5. Extension points

### Add a new metric

1. Add entry to `config/metrics_registry.yaml`
2. Ensure generator emits correct module_key and branch_slug
3. Map primary tool in `lib/tool_map.py` if new tool family
4. Add assert thresholds in `lib/tool_assert.py` if new family
5. Run generate + validate for all 4 branch types

### Add a new language

1. Create `lib/lang_generators/{lang}.py`
2. Register in `lib/lang_generators/template_core.py`
3. Add runtime catalog to `lib/lang_support.py`
4. Add `branch_materialized()` path in `branch_pipeline.py`
5. Add post-verify in `lib/branch_post_verify.py`
6. Add tests in `tests/test_multi_language.py`

### Add a new tool family

1. Implement runner in `lib/lang_tool_runners.py` (or Python-specific path)
2. Add `metric_violation()` branch in `tool_assert.py`
3. Document in [TOOL_ASSERTS.md](TOOL_ASSERTS.md)

---

## 6. Test modules

| Test file | Coverage |
|-----------|----------|
| `test_multi_language.py` | Per-language generate + verify |
| `test_tool_assert_branch_types.py` | Bug/BugFX/TCC/CC outcomes |
| `test_registry_metrics.py` | TECH:CODE filter parsing |
| `test_comparison.py` | Compare logic |
| `test_branch_pipeline.py` | Pipeline integration |
| `test_whitebox_completion.py` | Whitebox status helpers |

---

## 7. Key constants

| Constant | Location | Value | Purpose |
|----------|----------|-------|---------|
| `WHITEBOX_AUTO_PREVIEW_LIMIT` | `ui/app.py` | 12 | Gate expensive API previews |
| `STALL_ROUNDS_LIMIT` | `branch_pipeline.py` | 3 | Stop regeneration loops |
| `LANGUAGE_RUNTIMES` | `lang_support.py` | per lang | UI runtime selector options |

---

## 8. Related documentation

- [High-Level Design](01-high-level-design.md) — architecture diagrams
- [Functional Guide](02-functional-guide.md) — UI features with screenshots
- [Process Workflows](03-process-workflows.md) — operating procedures
- [Tool Assert Semantics](TOOL_ASSERTS.md) — branch-type rules
