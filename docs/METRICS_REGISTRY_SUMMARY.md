# Metrics registry summary

Parsed from **Book.xlsx** — 14 technique groups, 103 L5 metrics.

Tool-assert semantics (Bug / BugFX / TCC / CC per tool family): see [TOOL_ASSERTS.md](TOOL_ASSERTS.md).

| technique | metric | L5 metric | Python primary tool |
|-----------|--------|-----------|---------------------|
| SA | EPI | Execution Path Integrity | Crosshair |
| SA | DOV | Decision Outcome Verification | Coverage.py |
| SA | LSV | Logical Sub-expression Validation | Pymcdc |
| SA | TLCC | Total Logical Combinatorial Coverage | Crosshair |
| SA | TDI | Technical Debt Impact | Radon/Lizard |
| SA | QRA | QA Resource Allocation | testmon |
| RM | TDI | Technical Debt Impact | cognitive-ast |
| RM | UTC | Unit Test Complexity | cognitive-ast |
| RM | DEPR | Defect Probability | cognitive-ast |
| RM | MOOP | Modularization Opportunity | cognitive-ast |
| RM | RFF | Reviewer Fatigue Factor | cognitive-ast |
| RM | QRA | QA Resource Allocation | cognitive-ast |
| RM | HCL | Human Cognitive Load | cognitive-ast |
| CQ | MPFP | Multi-Point Failure Probability | jscpd |
| CQ | RELO | Redundancy Localization | jscpd |
| CQ | SCS | Structural Cleanliness Score | jscpd |
| CQ | TSS | Test Suite Streamlining | jscpd |
| CQ | ABPO | Abstraction Potential | jscpd |
| CQ | RFM | Regression Focus Mapping | jscpd |
| CQ | SYVE | Synchronization Verification | jscpd |
| LR | VDK | Violation Density per KLOC | pylint |
| LR | RWI | Resource Waste Identification | pylint |
| LR | SCS | Semantic Consistency Score | pylint |
| LR | SUS | Syntactic Uniformity Score | pylint |
| LR | STM | Structural Threshold Monitoring | pylint |
| LR | IMPR | Impact Prioritization | pylint |
| LR | ARA | Aggregated Risk Assessment | pylint |
| LR | ACTU | Accuracy Tuning | pylint |
| LR | PSE | Project-Specific Enforcement | pylint |
| LR | ENST | Environment Standardization | pylint |
| LR | AUGA | Automated Gatekeeping | pylint |
| LR | QAT | Quality Audit Trail | pylint |
| SX | BPC | Best Practice Compliance | Semgrep OSS
+
Bandit |
| SX | EPS | Entry Point Sanitization | Semgrep OSS
+
Bandit |
| SX | SIT | Sensitive Information Tracking | Semgrep OSS
+
Bandit |
| SX | ACV | Access Control Verification | Semgrep OSS
+
Bandit |
| SX | SCS | Supply Chain Security | Semgrep OSS
+
Bandit |
| SX | REAL | Regulatory Alignment | Semgrep OSS
+
Bandit |
| SX | ESI | Exploit Surface Identification | Semgrep OSS
+
Bandit |
| DR | HRM | Hidden Relationship Mapping | pip-audit |
| DR | LRV | Legal Risk Validation | pip-audit |
| DR | TIV | Trust Integrity Verification | pip-audit |
| DR | CVT | Community Vitality Tracking | pip-audit |
| DR | MER | Mitigation Effort Ranking | pip-audit |
| DR | RTA | Real-Time Alerting | pip-audit |
| DR | KCC | Known CVE Count | pip-audit |
| DR | VLA | Version Lag Assessment | pip-audit |
| ST | TCG | Test Case Granularity | Coverage.py |
| ST | ULI | Unreachable Logic Identification | Coverage.py |
| ST | CGA | Coverage Gap Analysis | Coverage.py |
| ST | SLC | Surface-Level Correctness | Coverage.py |
| ST | STCO | Statement Coverage % | Coverage.py |
| BR | BAC | Boolean Accuracy Check | Coverage.py |
| BR | SIM | Sequence Integrity Mapping | Coverage.py |
| BR | IBV | Iteration Boundary Verification | Coverage.py |
| BR | BFI | Boundary Failure Identification | Coverage.py |
| BR | BMD | Branch Misdirection Discovery | Coverage.py |
| BR | DCGA | Decision Coverage Gap Analysis | Coverage.py |
| BR | BRCO | Branch Coverage % | Coverage.py |
| PC | PET | Path Execution Tracking | Coverage.py |
| PC | FLV | Full Logic Validation | Coverage.py |
| PC | GAID | Gap Identification | Coverage.py |
| PC | DLP | Deep Logic Probing | Coverage.py |
| PC | IRA | Iterative Route Analysis | Coverage.py |
| PC | GCD | Ghost Code Discovery | Coverage.py |
| PC | EFV | Error Flow Verification | Coverage.py |
| PC | CCM | Cross-Component Mapping | Coverage.py |
| PC | AQE | Automated Quality Enforcement | Coverage.py |
| PC | PACO | Path Coverage % | Coverage.py |
| MU | LES | Logic Error Sensitivity | cosmic-ray |
| MU | TRA | Test Rigor Assessment | cosmic-ray |
| MU | WSL | Weak Spot Localization | cosmic-ray |
| MU | BMA | Boundary Mutant Analysis | cosmic-ray |
| MU | CRT | Change Resilience Testing | cosmic-ray |
| MU | SIC | Semantic Integrity Check | cosmic-ray |
| MU | MKR | Mutation Kill Rate % | cosmic-ray |
| CD | CODE | Coverage Delta % | Coverage.py |
| CD | DPA | Discovery Power Assessment | Coverage.py |
| CD | DRG | Deployment Readiness Guard | Coverage.py |
| CD | REM | Ripple Effect Mapping | Coverage.py |
| CD | FLP | Fresh Logic Proofing | Coverage.py |
| CD | SHB | Structural Health Benchmarking | Coverage.py |
| DF | DECO | All-Defs Coverage % | Beniget |
| DF | DPC | Data Path Correlation | coverage.py |
| DF | DPV | DU-Path Validation | Beniget |
| DF | DDI | Dead Data Identification | pylint |
| DF | NBFA | Null and Boundary Flow Analysis | CrossHair |
| DF | ATV | Audit Trail Verification | pydriller |
| DU | DPV | Data Processing Validation | coverage.py + beniget |
| DU | LIA | Logic Influence Assessment | coverage.py + beniget |
| DU | PCM | Path Correlation Mapping | coverage.py + beniget |
| DU | CDP | Comprehensive Data Proofing | coverage.py + beniget |
| DU | DFGA | Data Flow Gap Analysis | coverage.py + beniget |
| DU | AMRE | Ambiguity Resolution | coverage.py + beniget |
| DU | IPT | Inter-procedural Tracking | coverage.py + beniget |
| DU | GHID | Ghost Use Identification | coverage.py + beniget |
| DU | DIA | Data Integrity Audit | coverage.py + beniget |
| DU | COVER | All-Uses Coverage % | coverage.py + beniget |
| DP | CCS | Code Churn Score | pydriller |
| DP | IDV | Impact-Driven Verification | pydriller |
| DP | FPM | Fault Probability Modeling | pydriller |
| DP | VSU | Validation Suite Updates | pydriller |
| DP | SEM | Side Effect Mapping | pydriller |
