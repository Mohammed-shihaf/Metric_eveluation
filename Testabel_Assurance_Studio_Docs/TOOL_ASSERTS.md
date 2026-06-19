# Tool-Assert Semantics

Registry-driven **tool_assert** checks run the `primary_tool` (and `secondary_tool` when relevant) from `config/metrics_registry.yaml` against each generated branch in `build/<BRANCH_NAME>/`, then compare the raw measurement to the expected outcome for that branch type.

Structural validation (`lib/validate.py`) confirms markers, LOC, stubs, and config files exist. **Tool asserts** confirm the assigned QA tool would classify the branch correctly in the Testable whitebox pipeline.

## Branch-type expectations

| Type | Tool metric outcome | Config | Notes |
|------|---------------------|--------|-------|
| **Bug** | **FAIL** — violation/defect present | No TCC tool configs | Target module drives the failure |
| **BugFX** | **PASS** or **WARN** — defect resolved | No TCC tool configs | Not necessarily tool-optimized |
| **TCC** | **PASS** or **WARN** | TCC config present **and effective** | e.g. `.coveragerc` changes scope, `jscpd.json` honored |
| **CC** | **PASS** or **WARN** | No TCC configs (default path) | Smoke-level pass only |

**Isolation:** For every branch, findings/violations that determine PASS vs FAIL must come from the **target metric module**, not from stub modules. Stubs may have benign complexity or style noise but must not alone trigger the target-metric FAIL condition.

## Outcome vocabulary

| Label | Meaning |
|-------|---------|
| `FAIL` | Tool reports a metric violation (below threshold, findings > 0, audit hit, etc.) |
| `PASS` | Tool reports no violation for the target metric |
| `WARN` | Borderline / advisory only — acceptable for BugFX, TCC, CC |
| `SKIPPED` | Primary tool not installed or not runnable in this environment |

## Tool families (Python)

Primary tool strings from the registry are normalized into families:

| Family | Registry tools | Measurement | Bug = FAIL when |
|--------|----------------|-------------|-----------------|
| `coverage` | Coverage.py | Branch coverage % on target module | Coverage &lt; 50% **and** ≤2 tests (partial suite) |
| `complexity` | Radon/Lizard, cognitive-ast | Max cyclomatic complexity (radon proxy) | Max CC &gt; 15 on target |
| `lint` | pylint, flake8 | Lint issue count on target | Issues &gt; 0 |
| `security` | Semgrep OSS + Bandit | Security findings in target module | Findings &gt; 0 |
| `sca` | pip-audit, safety | Known vulnerable deps in requirements | Vulns &gt; 0 |
| `mutation` | cosmic-ray, mutmut | Mutation-kill proxy (test÷function ratio) | Ratio &lt; 0.25 |
| `churn` | pydriller, git_churn | Churn risk score (`.churn_meta.json` or pydriller) | Score &gt; 70 |
| `duplication` | jscpd | Duplication % in target module | Dup % &gt; 5 |
| `crosshair` | Crosshair | Branch-path proxy via coverage branch % | Branch cov &lt; 50% |
| `pymcdc` | Pymcdc | Condition-coverage proxy via branch % | Branch cov &lt; 50% |
| `testmon` | testmon | `.testmondata.ini` + adequate tests | Missing config / tests |

When the primary CLI is unavailable, the check is **SKIPPED** (never silently passed or failed).

## Multi-language tool runners

Non-Python branches use the same tool-assert pipeline as Python. Language is resolved from `.gen_meta.json` via `branch_language()`.

| Language | Native tools (when toolchain present) | Fallback |
|----------|---------------------------------------|----------|
| Java | JaCoCo, PMD/Checkstyle, SpotBugs, CPD, PIT, `mvn test` | Structural surrogate → SKIPPED |
| C# | coverlet, `dotnet build` warnings, SecurityCodeScan, Stryker.NET, `dotnet test` | Structural surrogate → SKIPPED |
| TypeScript / JavaScript | eslint, nyc/c8, jscpd, Stryker, npm audit | Structural surrogate → SKIPPED |

**Auto-detect:** `RUN_NATIVE_BUILD` is no longer required. `lang_tool_runners.toolchain_available()` decides whether to invoke real CLIs. Results include `real_tool: true` when a native runner succeeds.

**Isolated local-tools batch:** The worker receives `--language`; pip venv is used only for Python branches. JS/TS branches run `npm install` in the branch directory when needed.

## Per-technique nuance: SX, DR, MU, DP

These four groups use conceptually different defect models. Tool-assert semantics are explicit:

### SX — Static Application Security Testing (SAST)

| Type | Expected | Tool behavior |
|------|----------|---------------|
| Bug | FAIL | **Bandit** and/or **Semgrep** report ≥1 finding in the **target** module (intentional insecure pattern, e.g. hardcoded secret, `eval`, `pickle.loads`) |
| BugFX | PASS | Zero findings in target module |
| TCC | PASS + config | Zero findings; TCC lint/security config present if applicable |
| CC | PASS | Zero findings via default rules (smoke) |

**Isolation:** Stubs must have zero SAST findings at high/medium severity.

### DR — Software Composition Analysis (SCA)

| Type | Expected | Tool behavior |
|------|----------|---------------|
| Bug | FAIL | **pip-audit** flags ≥1 known vulnerable pin in `requirements.txt` |
| BugFX | PASS | Clean audit (no known CVEs) |
| TCC | PASS + config | Clean audit; dependency-audit config honored if present |
| CC | PASS | Clean audit on default scan |

**Isolation:** Vulnerability must come from `requirements.txt`, not from stub Python modules.

### MU — Mutation testing

| Type | Expected | Tool behavior |
|------|----------|---------------|
| Bug | FAIL | **cosmic-ray** mutation score below threshold (&lt; 50%), or proxy: tests÷functions &lt; 0.25 (weak suite) |
| BugFX | PASS | Mutation score ≥ 50% (proxy: tests÷functions ≥ 0.25) |
| TCC | PASS + config | Score meets threshold; mutation/coverage TCC config present |
| CC | PASS | Score meets threshold via default test run |

**Isolation:** Weak testing must affect the target module's score, not be masked by stub tests.

### DP — Development process / code churn

| Type | Expected | Tool behavior |
|------|----------|---------------|
| Bug | FAIL | **pydriller**-derived churn/risk score for target module &gt; 70 (seeded via `.churn_meta.json` or git history) |
| BugFX | PASS | Churn score ≤ 70 |
| TCC | PASS + config | Score within range; process-analysis config present if applicable |
| CC | PASS | Score within range on default path |

**Isolation:** High churn is attributed to the target module path, not stub modules.

## TCC config effectiveness

| Tool | Effectiveness check |
|------|---------------------|
| Coverage.py | `.coveragerc` exists and `source` omits `tests/*` |
| jscpd | `jscpd.json` exists with `threshold` key |
| pylint/flake8 | `setup.cfg` or `.pylintrc` / config present |
| testmon | `.testmondata.ini` exists |

## CLI usage

```bash
# Structural only (fast, default)
python validate_branch.py --quick

# Structural + tool execution
python validate_branch.py --tool-asserts

# Parallel tool pass
python validate_branch.py --tool-asserts --parallel 8

# Filtered
python validate_branch.py --tool-asserts --techniques SA,SX --types Bug,BugFX
```

## Generator artifacts (Bug branches)

For SX, DR, MU, and DP, `lib/python_generator.py` embeds tool-detectable defects on **Bug** branches only:

- **SX:** `hardcoded_password` + `eval()` snippet in target module (Bandit/Semgrep-detectable)
- **DR:** Known-vulnerable pin in `requirements.txt` (e.g. `urllib3==1.24.1`)
- **MU:** Partial test suite (≤2 tests) — already structural
- **DP:** `.churn_meta.json` with `churn_score` &gt; 70 for target module

Branches generated before these artifacts were added may fail tool_assert on SX/DR/DP Bug rows until regenerated.
