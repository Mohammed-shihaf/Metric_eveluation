# Metric Evaluation Scripts

## Generate SA branch codebases

```powershell
py -3 scripts/generate_sa_codebase.py all --out build
## Metric-level branches (24 total: 6 metrics × Bug, BugFX, TCC, CC)

```powershell
# Generate + create git branches (one-time)
py -3 scripts/generate_sa_metric_codebase.py --metric all --branch-type all
py -3 scripts/create_metric_branches.py
git push -u origin SA_EPI_Bug_2.6 SA_EPI_BugFX_2.6 ...  # all 24

# Combined runner — all 24 metric branches, HTML export, verification
py -3 scripts/run_sa_metric_taxonomy_batch.py --refresh-branches

# One metric only (4 branches)
py -3 scripts/run_sa_metric_taxonomy_batch.py --refresh-branches --metric EPI

# Dry-run catalog check
py -3 scripts/run_sa_metric_taxonomy_batch.py --dry-run --refresh-branches
```

## Legacy technique-level branches

py -3 scripts/deploy_one_branch.py SA_bug_2.6
```

## Run taxonomy batch (Testable platform)

1. Copy `.env.example` to `.env.local` and fill credentials.
2. Ensure platform is reachable (QA: [qa-frontend.testable.cc](https://qa-frontend.testable.cc/auth/login); local: `http://localhost:3000`).
3. Connect GitHub SCM in the UI (required for all branches to appear).
4. Run:

```powershell
py -3 scripts/run_sa_taxonomy_batch.py --ensure-project --refresh-branches
```

Partial run (only branches already in catalog):

```powershell
py -3 scripts/run_sa_taxonomy_batch.py --allow-partial-branches --branches SA_bug_2.6
```

Reports are saved under `taxonomy_reports/<batch_id>/` **only after**:
1. The whitebox run reaches `completed` status (`REQUIRE_RUN_COMPLETED=true` by default)
2. The taxonomy gate reports `gate_status: completed`

Set `REQUIRE_RUN_COMPLETED=false` to save reports on failed/partial runs once the gate is ready.
