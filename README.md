# Metric Evaluation

Registry-driven branch factory for Testable QA whitebox taxonomy validation.

## Scope

- **103 metrics** across **14 technique groups** (from `Book.xlsx` → `config/metrics_registry.yaml`)
- **4 branch types** per metric: `Bug`, `BugFX`, `TCC`, `CC`
- Naming: `<TECH>_<METRIC>_<TYPE>_<VERSION>` (e.g. `SA_DOV_Bug_2.6`, `RM_UTC_Bug_2.6`)
- Full matrix: **412 branches** per language/version (configurable via filters)

### Implemented today

| Area | Status |
|------|--------|
| Registry from `Book.xlsx` | ✅ `config/metrics_registry.yaml` (103 metrics) |
| Python generation — **SA** | ✅ Full (`lib/sa_generator.py`, regression-safe) |
| Python generation — **other techniques** | ✅ Generic (`lib/python_generator.py`) |
| Other languages (Java, C#, JS, …) | ⏳ `NotImplementedError` until templates added |
| Validation | ✅ `validate_branch.py` / `lib/validate.py` |
| QA batch + verify | ✅ `lib/sa_qa.py` + notebooks |

## Repository layout

```
config/metrics_registry.yaml   # single source of truth (L2/L3/L4/L5, tools, codes)
docs/METRICS_REGISTRY_SUMMARY.md
lib/
  build_registry.py            # regenerate YAML from Book.xlsx
  registry.py                  # load/filter registry
  metrics.py                   # branch naming, report paths
  generator.py                 # routes SA → sa_generator, else python_generator
  sa_generator.py              # SA reference implementation (Python)
  python_generator.py          # generic Python for non-SA techniques
  validate.py                  # registry-driven asserts
  sa_qa.py                     # Testable QA batch runner + HTML verify
  qa_reports.py                # save/commit reports on main
notebooks/
  generate_branches.ipynb      # Notebook 1 — generate + validate (+ optional git)
  run_whitebox_and_collect_reports.ipynb  # Notebook 2 — QA + reports on main
  01_generate_and_validate.ipynb           # legacy SA-only notebook
  02_run_qa_and_verify.ipynb               # legacy QA notebook
generate_branches.py           # CLI: generate + validate
validate_branch.py             # CLI: validate only
tools/export_taxonomy_html.ts
archive/                       # superseded scripts
```

## How to run

### Setup

```powershell
py -3 -m pip install -r requirements.txt
copy .env.example .env.local
# Regenerate registry when Book.xlsx changes:
py -3 lib/build_registry.py C:\Users\moham\Downloads\Book.xlsx
```

### Notebook 1 — Generate branches

Open `notebooks/generate_branches.ipynb`. Set:

- `LANGUAGE`, `VERSION`
- `TECHNIQUES` (`"SA"`, `"all"`, or `"SA,RM"`)
- `METRICS` (`"DOV"`, `"all"`, …)
- `DO_GIT` / `DO_PUSH` (optional)

Writes `build/<TECH>_<METRIC>_<TYPE>_<VERSION>/` and `build_manifest.json`.

CLI equivalent:

```powershell
py -3 generate_branches.py --techniques SA --metrics all --language python --version 2.6
py -3 validate_branch.py --techniques SA --metrics all
```

### Notebook 2 — QA + taxonomy reports

Open `notebooks/run_whitebox_and_collect_reports.ipynb`. Uses `.env.local` credentials.

Reports saved on **main** as:

```
taxonomy_reports/<L2 group>/<BRANCH_NAME>/<BRANCH_NAME>_<YYYYMMDD_HHMMSS>.html
```

### SA regression (24 branches)

```powershell
py -3 generate_branches.py --techniques SA --metrics all --version 2.6
```

All 24 existing `SA_*` branches remain valid under the generalized naming parser.
