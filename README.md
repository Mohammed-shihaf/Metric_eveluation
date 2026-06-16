# Testable Assurance Studio

Metric evaluation pipeline: generate branches, whitebox QA, local tools, SonarQube Community, and 4-way comparison.

## Pipeline (Streamlit UI)

```bash
py -3 -m streamlit run ui/app.py
```

| Step | Tab | Output |
|------|-----|--------|
| 1 | Branches | GitHub OAuth push (per-user encrypted token) + in-memory validate |
| 2 | Whitebox | taxonomy HTML + S3 reports |
| 3 | Local tools | `proofs/<TECH>/<branch>/local_report.json` (isolated throwaway venv) |
| 4 | SonarQube | `proofs/<TECH>/<branch>/sonar_report.json` |
| 5 | Compare | `comparison.json` (taxonomy / S3 / local / sonar) |

## SonarQube Community (Docker)

Step 4 auto-manages SonarQube via Docker:

- Pulls `sonarqube:community` and `sonarsource/sonar-scanner-cli` on first run (~600MB).
- Starts container `tas-sonarqube` on port **9000**; cold start takes **1–2 minutes**.
- Generates `coverage.xml` per branch, runs the scanner, and writes a standard `sonar_report.json`.
- Token cached in `.sonar_token` (gitignored).

Optional overrides in `.env.local` — see [`.env.example`](.env.example) (`SONAR_HOST_URL`, `SONAR_CONTAINER_NAME`, etc.).

**Requirements:** Docker Desktop running (Windows: scanner uses `host.docker.internal` to reach the server).

## GitHub connect (Branches tab)

Same flow as Testable SCM integrations (`ai-testable-platform`):

1. Create or open your GitHub App at [github.com/settings/apps](https://github.com/settings/apps) (e.g. **Testable Assurance Studio**)
2. **General** → **Callback URL** = `http://localhost:8501/` (local dev)
3. **Permissions & events** → user authorization (OAuth) + **Repository contents: Read & write**
4. Copy **Client ID** / **Client secret** into `.env.local` (`GITHUB_OAUTH_CLIENT_ID`, `GITHUB_OAUTH_CLIENT_SECRET`, `GITHUB_OAUTH_REDIRECT_URI`)
5. Set `GITHUB_APP_SLUG` and `SCM_TOKEN_SECRET`; optionally `SCM_DB_PATH`
6. Open **Account** in the sidebar → sign in with QA email/password
7. Open **Branches** → click **Connect GitHub** → authorize on GitHub
8. On the callback screen, click **View my repositories** → pick a repo → **Use this repository**
9. Install the GitHub App on the selected repo if prompted (**Contents: Read & write**)

Token refresh for `ghu_…` user tokens is automatic.

**Multi-user:** Each browser session signs in with its own QA account. GitHub OAuth and repo selection are stored per user in `scm_connections.db` (keyed by session email). Branch push and whitebox run as that user — not a shared identity from `.env.local`.

Optional server PAT: set `GITHUB_TOKEN` in `.env.local` only for unattended/CLI push when nobody is signed in. Signed-in users must connect GitHub OAuth; pushes never fall back to the shared PAT.

Optional CLI only: `REPOSITORY_MATCH` in `.env.local` for notebook/CLI whitebox runs when not using the UI.

## Local tools — isolated throwaway session

Step 3 runs tools inside a **temporary virtual environment** per batch (default on):

1. Create `tas_session_*` venv under the system temp directory
2. Install the union of required pip packages once (coverage, pytest, radon, etc.)
3. Run each selected branch in a subprocess using the venv Python
4. Write `local_report.json` under `proofs/`
5. Delete the venv and all installed tools

The host Python environment is never modified. First run per batch is slower due to pip install.
Disable via UI checkbox or set `LOCAL_TOOL_ISOLATED=false` in `.env.local`.

## Credentials

Copy `.env.example` to `.env.local` and fill in Testable QA + AWS S3 values.
