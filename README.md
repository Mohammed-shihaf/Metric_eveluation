# Testable Assurance Studio

Streamlit application for **metric branch generation, validation, GitHub push, Testable whitebox analysis, S3/local/Sonar comparison, and Excel proof export**.

Part of the Testable metric evaluation pipeline (`Metric_evaluation` repository).

## Quick start

```bash
pip install -r requirements.txt
copy .env.example .env.local   # configure credentials
streamlit run ui/app.py
```

Open **http://localhost:8501**

## Documentation

Full documentation lives in **[Testabel_Assurance_Studio_Docs/](Testabel_Assurance_Studio_Docs/README.md)**:

| Document | Description |
|----------|-------------|
| [Documentation index](Testabel_Assurance_Studio_Docs/README.md) | Start here |
| [High-Level Design](Testabel_Assurance_Studio_Docs/01-high-level-design.md) | Architecture, data model, integrations |
| [Functional Guide](Testabel_Assurance_Studio_Docs/02-functional-guide.md) | UI walkthrough with screenshots |
| [Process & Workflows](Testabel_Assurance_Studio_Docs/03-process-workflows.md) | End-to-end assurance procedures |
| [Setup & Configuration](Testabel_Assurance_Studio_Docs/04-setup-and-configuration.md) | Install, `.env.local`, deployment |
| [Module Reference](Testabel_Assurance_Studio_Docs/05-module-reference.md) | Code layout for developers |
| [Tool Assert Semantics](Testabel_Assurance_Studio_Docs/TOOL_ASSERTS.md) | Branch-type expectations |
| [Metrics Registry](Testabel_Assurance_Studio_Docs/METRICS_REGISTRY_SUMMARY.md) | 14 techniques, 103 metrics |

## Pipeline

```
Generate → Validate → Push → Whitebox → Local tools → SonarQube → Compare → Excel
```

## Features

- **412 metric branches** across 14 techniques (SA, RM, CQ, LR, SX, DR, ST, BR, PC, MU, DP, DF, …)
- **4 branch types** per metric: Bug, BugFX, TCC, CC
- **5 languages**: Python, Java, C#, TypeScript, JavaScript
- Registry-driven tool asserts with strength escalation
- GitHub OAuth push, Testable QA whitebox, AWS S3 proofs
- Comparison with mismatch highlighting and Excel export

## Tests

```bash
pytest tests/ -q
python tools/e2e_browser_verify.py
```

## License

Internal Testable project.
