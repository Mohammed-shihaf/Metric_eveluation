# Testable Assurance Studio — Documentation

**Testable Assurance Studio** (TAS) is a Streamlit application in the `Metric_evaluation` repository. It generates metric evaluation branches from a central registry, validates them with local QA tools, pushes to GitHub, runs Testable whitebox analysis, collects S3 proofs, executes tools locally, optionally scans with SonarQube, and compares all report sources.

---

## Document map

| Document | Audience | Contents |
|----------|----------|----------|
| [High-Level Design](01-high-level-design.md) | Architects, leads | Purpose, scope, architecture, integrations, data model |
| [Functional Guide](02-functional-guide.md) | QA engineers, users | UI tabs, sidebar filters, screenshots, feature walkthrough |
| [Process & Workflows](03-process-workflows.md) | Operators | End-to-end pipeline, gates, branch types, comparison verdicts |
| [Setup & Configuration](04-setup-and-configuration.md) | DevOps, developers | Install, `.env.local`, credentials, deployment notes |
| [Module Reference](05-module-reference.md) | Developers | Code layout, key modules, extension points |
| [Tool Assert Semantics](TOOL_ASSERTS.md) | QA, developers | Branch-type expectations, tool families, per-technique rules |
| [Metrics Registry Summary](METRICS_REGISTRY_SUMMARY.md) | All | 14 techniques, 103 metrics, primary tools |
| [E2E Demo Walkthrough](e2e-demo/E2E_WALKTHROUGH.md) | Presenters | Scripted demo with historical screenshots |

---

## Quick start

```bash
# 1. Clone and install
cd Metric_evaluation
py -3 -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt

# 2. Configure credentials
copy .env.example .env.local    # edit with your values

# 3. Run the app
py -3 -m streamlit run ui/app.py
```

Open **http://localhost:8501**

---

## Pipeline at a glance

```
Sidebar selection → Generate → Validate → Push (GitHub)
                              ↓
                    Whitebox (Testable QA)
                              ↓
              S3 sync + Taxonomy export + Local tools + SonarQube
                              ↓
                    Compare (S3 vs Local vs Sonar)
                              ↓
                    Excel proof workbook export
```

---

## Screenshots

UI captures live in [`images/`](images/). Demo walkthrough screenshots are in [`e2e-demo/`](e2e-demo/).

Regenerate UI screenshots (from repo root):

```bash
py -3 -m streamlit run ui/app.py --server.port 8501 --server.headless true
py -3 tools/capture_docs_screenshots.py
```

---

## Related Jira work

| Key | Summary |
|-----|---------|
| [TP-2264](https://testable.atlassian.net/browse/TP-2264) | Testable Assurance Studio (dev complete) |
| [TP-2263](https://testable.atlassian.net/browse/TP-2263) | Hosting / server deployment (pending) |
