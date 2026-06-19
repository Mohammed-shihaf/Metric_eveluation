# Setup & Configuration

## 1. System requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| OS | Windows 10+, Linux, macOS | Windows 11 / Ubuntu 22.04 |
| Python | 3.10+ | 3.12 |
| RAM | 4 GB | 8 GB+ (full 412-branch generation) |
| Disk | 5 GB free | 20 GB+ (pipeline work + proofs) |
| Network | Outbound HTTPS | GitHub, Testable QA, AWS S3 |

### Optional toolchains (non-Python verify)

| Language | Tools |
|----------|-------|
| Java | JDK 11/17/21, Maven |
| C# | .NET SDK 6/7/8 |
| TypeScript/JS | Node.js 18+, npm |

Missing toolchains skip compile verify gracefully; generation and structure asserts still run.

### Optional services

| Service | Purpose |
|---------|---------|
| Docker Desktop | SonarQube Community scans |
| Playwright | Browser E2E tests and screenshot capture |

```bash
pip install playwright
playwright install chromium
```

---

## 2. Installation

```bash
git clone <repo-url> Metric_evaluation
cd Metric_evaluation

py -3 -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
```

---

## 3. Configuration file

Copy the template:

```bash
copy .env.example .env.local    # Windows
cp .env.example .env.local      # Linux/macOS
```

The app loads `.env.local` at startup via `lib/sa_qa.load_env()`.

**Never commit `.env.local`** — it contains secrets.

---

## 4. Environment variables reference

### 4.1 Testable QA (required for whitebox)

| Variable | Example | Description |
|----------|---------|-------------|
| `IDENTITY_URL` | `https://qa-api.testable.cc` | Auth API |
| `RUNTIME_URL` | `https://qa-runtime.testable.cc` | Run execution API |
| `VIEWS_URL` | `https://qa-views.testable.cc` | Views API |
| `FRONTEND_URL` | `https://qa-frontend.testable.cc` | Frontend URL |
| `AUTH_EMAIL` | `user@testable.cloud` | Default login (UI can override) |
| `AUTH_PASSWORD` | `***` | Default password (session-only in UI) |

Optional: `TENANT_ID`, `USER_ID`, `PROJECT_ID` (auto-resolved on login)

### 4.2 GitHub (required for push)

| Variable | Description |
|----------|-------------|
| `GITHUB_OAUTH_CLIENT_ID` | GitHub App OAuth client ID |
| `GITHUB_OAUTH_CLIENT_SECRET` | OAuth secret |
| `GITHUB_OAUTH_REDIRECT_URI` | Must match app callback (default `http://localhost:8501/`) |
| `GITHUB_APP_SLUG` | App slug for install URL |
| `SCM_TOKEN_SECRET` | Random string for encrypting tokens in SQLite |
| `SCM_DB_PATH` | OAuth token store (default `scm_connections.db`) |
| `GITHUB_TOKEN` | Optional classic PAT with `repo` scope (push fallback) |

**GitHub App setup:**

1. Create GitHub App at https://github.com/settings/apps
2. Callback URL: `http://localhost:8501/` (or production URL)
3. Permissions: **Contents: Read & write**
4. Install app on target organization/repo

### 4.3 AWS S3 (required for S3 proofs)

| Variable | Description |
|----------|-------------|
| `S3_BUCKET` | Bucket name (e.g. `us2-qa-testable`) |
| `S3_SEARCH_PREFIX` | Prefix for tool bundles |
| `S3_DOWNLOAD_ROOT` | Local download dir (default `s3_downloads`) |
| `AWS_ACCESS_KEY_ID` | STS access key |
| `AWS_SECRET_ACCESS_KEY` | STS secret |
| `AWS_SESSION_TOKEN` | STS session token (refresh hourly) |
| `AWS_DEFAULT_REGION` | e.g. `us-east-2` |

Use `lib/sa_qa.reload_s3_credentials()` or sidebar refresh when STS expires.

### 4.4 Pipeline tuning

| Variable | Default | Description |
|----------|---------|-------------|
| `BRANCHES` | SA_DOV set | CLI default branch list |
| `OUTPUT_DIR` | `taxonomy_reports` | Taxonomy HTML export dir |
| `POLL_INTERVAL_SEC` | 30 | Whitebox poll interval |
| `POLL_TIMEOUT_SEC` | 3600 | Whitebox timeout |
| `BRANCH_DELAY_SEC` | 90 | Delay between branch operations |
| `LOCAL_TOOL_ISOLATED` | true | Isolated venv per local tool batch |
| `CONTINUE_ON_FAILURE` | true | Continue batch on single branch failure |

### 4.5 SonarQube (optional)

| Variable | Default |
|----------|---------|
| `SONAR_HOST_URL` | `http://localhost:9000` |
| `SONAR_CONTAINER_NAME` | `tas-sonarqube` |
| `SONAR_DOCKER_IMAGE` | `sonarqube:community` |
| `SONAR_SCANNER_IMAGE` | `sonarsource/sonar-scanner-cli` |

---

## 5. Running the application

### Development

```bash
py -3 -m streamlit run ui/app.py
```

Custom port:

```bash
py -3 -m streamlit run ui/app.py --server.port 8501 --server.headless true
```

### Credential verification

On startup the sidebar runs a credential audit:

- **QA:** Can reach identity API
- **S3:** AWS credentials valid
- **GitHub:** OAuth configured or PAT present

---

## 6. Directory layout (runtime)

```
Metric_evaluation/
├── ui/app.py                 # Streamlit entry point
├── lib/                      # Core library
├── config/metrics_registry.yaml
├── .env.local                # Secrets (gitignored)
├── scm_connections.db        # Per-user GitHub tokens
├── .pipeline_work/
│   └── {user-hash}/          # Generated branches per user
│       └── SA_Metric-Type_2.6/
├── proofs/                   # Proof bundles per branch
├── taxonomy_reports/         # Whitebox HTML exports
├── s3_downloads/             # Raw S3 artifacts
└── Testabel_Assurance_Studio_Docs/  # Documentation
```

---

## 7. Running tests

```bash
# Full test suite
py -3 -m pytest tests/ -q

# Multi-language generation tests
py -3 -m pytest tests/test_multi_language.py -v

# Branch-type tool assert tests
py -3 -m pytest tests/test_tool_assert_branch_types.py -v
```

### Browser E2E

```bash
# Terminal 1: start app
py -3 -m streamlit run ui/app.py --server.port 8501 --server.headless true

# Terminal 2: smoke test + screenshots
py -3 tools/e2e_browser_verify.py
py -3 tools/capture_docs_screenshots.py
```

---

## 8. Notebooks (CLI alternative)

| Notebook | Purpose |
|----------|---------|
| `notebooks/01_generate_and_validate.ipynb` | Generate + validate without UI |
| `notebooks/02_run_qa_and_verify.ipynb` | QA whitebox from notebook |

Notebooks use the same `lib/` modules as the Streamlit app.

---

## 9. Production deployment (planned)

See Jira [TP-2263](https://testable.atlassian.net/browse/TP-2263).

High-level steps:

1. Provision server (8 GB RAM, Python 3.12, 20 GB disk)
2. Clone repo, create venv, install requirements
3. Place `.env.local` with production URLs and secrets
4. Run as systemd service or Windows Service:

```bash
streamlit run ui/app.py \
  --server.port 8501 \
  --server.headless true \
  --server.address 0.0.0.0
```

5. Configure reverse proxy (nginx/IIS) with TLS
6. Restrict network access to internal VPN
7. Rotate AWS STS credentials on schedule
8. Smoke test: login → generate 1 branch → compare export

---

## 10. Troubleshooting

| Issue | Fix |
|-------|-----|
| `PyYAML required` | `pip install pyyaml` |
| GitHub OAuth redirect mismatch | Match `GITHUB_OAUTH_REDIRECT_URI` to app callback exactly |
| Push 403 | Install GitHub App on repo; set Contents Read & write |
| S3 access denied | Refresh STS token in `.env.local` |
| Whitebox 0 branches ready | Wait for catalog sync; verify branch names match registry |
| Streamlit port in use | `--server.port 8502` or kill existing process |
| Playwright not found | `pip install playwright && playwright install chromium` |

For functional behavior see [02-functional-guide.md](02-functional-guide.md).
