# Metrics registry summary

Parsed from **Testable_Strategy_Metrics_Mapping_v0.2 (3).xlsx** — 14 technique groups, 103 L5 metrics.

| technique | slug | module_key | L5 metric | Python primary | emitted |
|-----------|------|------------|-----------|------------------|---------|
| SA | Execution-Path-Integrity | execution_path_integrity | Execution Path Integrity | Crosshair | No |
| SA | Decision-Outcome-Verification | decision_outcome_verification | Decision Outcome Verification | Coverage.py | No |
| SA | Logical-Sub-Expression-Validation | logical_sub_expression_validation | Logical Sub-expression Validation | Pymcdc | No |
| SA | Total-Logical-Combinatorial-Coverage | total_logical_combinatorial_coverage | Total Logical Combinatorial Coverage | Crosshair | No |
| SA | Technical-Debt-Impact | technical_debt_impact | Technical Debt Impact | Radon/Lizard | No |
| SA | QA-Resource-Allocation | qa_resource_allocation | QA Resource Allocation | testmon | No |
| RM | Technical-Debt-Impact | technical_debt_impact | Technical Debt Impact | cognitive-ast | No |
| RM | Unit-Test-Complexity | unit_test_complexity | Unit Test Complexity | cognitive-ast | No |
| RM | Defect-Probability | defect_probability | Defect Probability | cognitive-ast | No |
| RM | Modularization-Opportunity | modularization_opportunity | Modularization Opportunity | cognitive-ast | No |
| RM | Reviewer-Fatigue-Factor | reviewer_fatigue_factor | Reviewer Fatigue Factor | cognitive-ast | No |
| RM | QA-Resource-Allocation | qa_resource_allocation | QA Resource Allocation | cognitive-ast | No |
| RM | Human-Cognitive-Load | human_cognitive_load | Human Cognitive Load | cognitive-ast | No |
| CQ | Multi-Point-Failure-Probability | multi_point_failure_probability | Multi-Point Failure Probability | jscpd | No |
| CQ | Redundancy-Localization | redundancy_localization | Redundancy Localization | jscpd | No |
| CQ | Structural-Cleanliness-Score | structural_cleanliness_score | Structural Cleanliness Score | jscpd | No |
| CQ | Test-Suite-Streamlining | test_suite_streamlining | Test Suite Streamlining | jscpd | No |
| CQ | Abstraction-Potential | abstraction_potential | Abstraction Potential | jscpd | No |
| CQ | Regression-Focus-Mapping | regression_focus_mapping | Regression Focus Mapping | jscpd | No |
| CQ | Synchronization-Verification | synchronization_verification | Synchronization Verification | jscpd | No |
| LR | Violation-Density-Per-KLOC | violation_density_per_kloc | Violation Density per KLOC | pylint | No |
| LR | Resource-Waste-Identification | resource_waste_identification | Resource Waste Identification | pylint | No |
| LR | Semantic-Consistency-Score | semantic_consistency_score | Semantic Consistency Score | pylint | No |
| LR | Syntactic-Uniformity-Score | syntactic_uniformity_score | Syntactic Uniformity Score | pylint | No |
| LR | Structural-Threshold-Monitoring | structural_threshold_monitoring | Structural Threshold Monitoring | pylint | No |
| LR | Impact-Prioritization | impact_prioritization | Impact Prioritization | pylint | No |
| LR | Aggregated-Risk-Assessment | aggregated_risk_assessment | Aggregated Risk Assessment | pylint | No |
| LR | Accuracy-Tuning | accuracy_tuning | Accuracy Tuning | pylint | No |
| LR | Project-Specific-Enforcement | project_specific_enforcement | Project-Specific Enforcement | pylint | No |
| LR | Environment-Standardization | environment_standardization | Environment Standardization | pylint | No |
| LR | Automated-Gatekeeping | automated_gatekeeping | Automated Gatekeeping | pylint | No |
| LR | Quality-Audit-Trail | quality_audit_trail | Quality Audit Trail | pylint | No |
| SX | Best-Practice-Compliance | best_practice_compliance | Best Practice Compliance | Semgrep OSS + Bandit | No |
| SX | Entry-Point-Sanitization | entry_point_sanitization | Entry Point Sanitization | Semgrep OSS + Bandit | No |
| SX | Sensitive-Information-Tracking | sensitive_information_tracking | Sensitive Information Tracking | Semgrep OSS + Bandit | No |
| SX | Access-Control-Verification | access_control_verification | Access Control Verification | Semgrep OSS + Bandit | No |
| SX | Supply-Chain-Security | supply_chain_security | Supply Chain Security | Semgrep OSS + Bandit | No |
| SX | Regulatory-Alignment | regulatory_alignment | Regulatory Alignment | Semgrep OSS + Bandit | No |
| SX | Exploit-Surface-Identification | exploit_surface_identification | Exploit Surface Identification | Semgrep OSS + Bandit | No |
| DR | Hidden-Relationship-Mapping | hidden_relationship_mapping | Hidden Relationship Mapping | pip-audit | No |
| DR | Legal-Risk-Validation | legal_risk_validation | Legal Risk Validation | pip-audit | No |
| DR | Trust-Integrity-Verification | trust_integrity_verification | Trust Integrity Verification | pip-audit | No |
| DR | Community-Vitality-Tracking | community_vitality_tracking | Community Vitality Tracking | pip-audit | No |
| DR | Mitigation-Effort-Ranking | mitigation_effort_ranking | Mitigation Effort Ranking | pip-audit | No |
| DR | Real-Time-Alerting | real_time_alerting | Real-Time Alerting | pip-audit | No |
| DR | Known-CVE-Count | known_cve_count | Known CVE Count | pip-audit | No |
| DR | Version-Lag-Assessment | version_lag_assessment | Version Lag Assessment | pip-audit | No |
| ST | Test-Case-Granularity | test_case_granularity | Test Case Granularity | Coverage.py | No |
| ST | Unreachable-Logic-Identification | unreachable_logic_identification | Unreachable Logic Identification | Coverage.py | Yes |
| ST | Coverage-Gap-Analysis | coverage_gap_analysis | Coverage Gap Analysis | Coverage.py | No |
| ST | Surface-Level-Correctness | surface_level_correctness | Surface-Level Correctness | Coverage.py | Yes |
| ST | Statement-Coverage | statement_coverage | Statement Coverage % | Coverage.py | Yes |
| BR | Boolean-Accuracy-Check | boolean_accuracy_check | Boolean Accuracy Check | Coverage.py | No |
| BR | Sequence-Integrity-Mapping | sequence_integrity_mapping | Sequence Integrity Mapping | Coverage.py | No |
| BR | Iteration-Boundary-Verification | iteration_boundary_verification | Iteration Boundary Verification | Coverage.py | Yes |
| BR | Boundary-Failure-Identification | boundary_failure_identification | Boundary Failure Identification | Coverage.py | No |
| BR | Branch-Misdirection-Discovery | branch_misdirection_discovery | Branch Misdirection Discovery | Coverage.py | Yes |
| BR | Decision-Coverage-Gap-Analysis | decision_coverage_gap_analysis | Decision Coverage Gap Analysis | Coverage.py | No |
| BR | Branch-Coverage | branch_coverage | Branch Coverage % | Coverage.py | Yes |
| PC | Path-Execution-Tracking | path_execution_tracking | Path Execution Tracking | Coverage.py | No |
| PC | Full-Logic-Validation | full_logic_validation | Full Logic Validation | Coverage.py | No |
| PC | Gap-Identification | gap_identification | Gap Identification | Coverage.py | No |
| PC | Deep-Logic-Probing | deep_logic_probing | Deep Logic Probing | Coverage.py | No |
| PC | Iterative-Route-Analysis | iterative_route_analysis | Iterative Route Analysis | Coverage.py | No |
| PC | Ghost-Code-Discovery | ghost_code_discovery | Ghost Code Discovery | Coverage.py | No |
| PC | Error-Flow-Verification | error_flow_verification | Error Flow Verification | Coverage.py | Yes |
| PC | Cross-Component-Mapping | cross_component_mapping | Cross-Component Mapping | Coverage.py | No |
| PC | Automated-Quality-Enforcement | automated_quality_enforcement | Automated Quality Enforcement | Coverage.py | No |
| PC | Path-Coverage | path_coverage | Path Coverage % | Coverage.py | No |
| MU | Logic-Error-Sensitivity | logic_error_sensitivity | Logic Error Sensitivity | cosmic-ray | No |
| MU | Test-Rigor-Assessment | test_rigor_assessment | Test Rigor Assessment | cosmic-ray | No |
| MU | Weak-Spot-Localization | weak_spot_localization | Weak Spot Localization | cosmic-ray | No |
| MU | Boundary-Mutant-Analysis | boundary_mutant_analysis | Boundary Mutant Analysis | cosmic-ray | No |
| MU | Logic-Error-Sensitivity | logic_error_sensitivity | Logic Error Sensitivity | cosmic-ray | No |
| MU | Test-Rigor-Assessment | test_rigor_assessment | Test Rigor Assessment | cosmic-ray | No |
| MU | Logic-Error-Sensitivity | logic_error_sensitivity | Logic Error Sensitivity | cosmic-ray | No |
| CD | Coverage-Delta | coverage_delta | Coverage Delta % | Coverage.py | No |
| CD | Discovery-Power-Assessment | discovery_power_assessment | Discovery Power Assessment | Coverage.py | No |
| CD | Deployment-Readiness-Guard | deployment_readiness_guard | Deployment Readiness Guard | Coverage.py | No |
| CD | Ripple-Effect-Mapping | ripple_effect_mapping | Ripple Effect Mapping | Coverage.py | No |
| CD | Fresh-Logic-Proofing | fresh_logic_proofing | Fresh Logic Proofing | Coverage.py | No |
| CD | Structural-Health-Benchmarking | structural_health_benchmarking | Structural Health Benchmarking | Coverage.py | No |
| DF | All-Defs-Coverage | all_defs_coverage | All-Defs Coverage % | Beniget | No |
| DF | Data-Path-Correlation | data_path_correlation | Data Path Correlation | coverage.py | No |
| DF | DU-Path-Validation | du_path_validation | DU-Path Validation | Beniget | No |
| DF | Dead-Data-Identification | dead_data_identification | Dead Data Identification | pylint | No |
| DF | Null-And-Boundary-Flow-Analysis | null_and_boundary_flow_analysis | Null and Boundary Flow Analysis | CrossHair | No |
| DF | Audit-Trail-Verification | audit_trail_verification | Audit Trail Verification | pydriller | No |
| DU | Data-Processing-Validation | data_processing_validation | Data Processing Validation | coverage.py + beniget | No |
| DU | Logic-Influence-Assessment | logic_influence_assessment | Logic Influence Assessment | coverage.py + beniget | Yes |
| DU | Path-Correlation-Mapping | path_correlation_mapping | Path Correlation Mapping | coverage.py + beniget | No |
| DU | Comprehensive-Data-Proofing | comprehensive_data_proofing | Comprehensive Data Proofing | coverage.py + beniget | No |
| DU | Data-Flow-Gap-Analysis | data_flow_gap_analysis | Data Flow Gap Analysis | coverage.py + beniget | No |
| DU | Ambiguity-Resolution | ambiguity_resolution | Ambiguity Resolution | coverage.py + beniget | No |
| DU | Inter-Procedural-Tracking | inter_procedural_tracking | Inter-procedural Tracking | coverage.py + beniget | No |
| DU | Ghost-Use-Identification | ghost_use_identification | Ghost Use Identification | coverage.py + beniget | No |
| DU | Data-Integrity-Audit | data_integrity_audit | Data Integrity Audit | coverage.py + beniget | No |
| DU | All-Uses-Coverage | all_uses_coverage | All-Uses Coverage % | coverage.py + beniget | No |
| DP | Code-Churn-Score | code_churn_score | Code Churn Score | pydriller | Yes |
| DP | Impact-Driven-Verification | impact_driven_verification | Impact-Driven Verification | pydriller | No |
| DP | Fault-Probability-Modeling | fault_probability_modeling | Fault Probability Modeling | pydriller | No |
| DP | Validation-Suite-Updates | validation_suite_updates | Validation Suite Updates | pydriller | Yes |
| DP | Side-Effect-Mapping | side_effect_mapping | Side Effect Mapping | pydriller | No |
