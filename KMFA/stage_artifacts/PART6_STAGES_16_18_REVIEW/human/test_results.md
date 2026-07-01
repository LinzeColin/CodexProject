# KMFA Post-S18 Part 6 Test Results

review_id: `KMFA-PART6-STAGES-16-18-REVIEW-20260702`

## Baseline Validators Rerun

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s16_p1_subcontract_procurement.py
PASS: KMFA S16-P1 subcontract procurement aggregation check passed (source_lanes=4, project_matches=5, unallocated_pool=2, duplicate_payment_candidates=2, cross_project_candidates=2, report_grade_visible=D, formal_report_allowed=false, payment_execution=false, bank_operation=false, github_upload=false)

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s16_p2_project_status_lifecycle.py
PASS: KMFA S16-P2 project status lifecycle check passed (source_lanes=6, lifecycle_records=4, exception_items=3, handoff_guards=3, site_construction=false, safety_signature=false, technical_signature=false, invoice_issuance=false, collection_action=false)

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s16_p3_customer_business_analysis.py
PASS: KMFA S16-P3 customer business analysis check passed (source_lanes=5, customer_summaries=4, exception_items=4, business_decision_basis=false, collection_action=false, legal_collection_decision=false)

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s16_stage_review.py
PASS: KMFA Stage 16 review check passed (subcontract_matches=5, lifecycle_records=4, customer_summaries=4, formal_report=false, business_decision_basis=false, payment=false, bank=false, collection=false, legal=false, github_upload=false)

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s17_p1_access_security.py
PASS: KMFA S17-P1 access security policy check passed (roles=4, sensitive_categories=15, audit_actions=5, raw_sensitive_public_repo=false, notification_delivery=false)

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s17_p2_notifications.py
PASS: KMFA S17-P2 notification reminders check passed (rules=3, events=3, dispatch_logs=3, email_reminder_only=true, full_report_body=false, attachments=false, metadata_logs=true)

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s17_p3_operations_sop.py
PASS: KMFA S17-P3 operations SOP check passed (runbooks=4, knowledge_items=2, drill_logs=2, metadata_only=true, manual_execution_only=true)

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s17_stage_review.py
PASS: KMFA Stage 17 review check passed (roles=4, notification_rules=3, runbooks=4, knowledge_items=2, drill_logs=2, github_upload=0, full_tests=246)

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s18_p1_precision_stress.py
PASS: KMFA S18-P1 precision stress validation check passed (scenarios=5, runs=3, large_batch_files=1200, elapsed_ms=348, errors=2)

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s18_p2_full_regression_acceptance.py
PASS: KMFA S18-P2 full regression acceptance check passed (checks=5, stages=18, decision=NO_GO, delivery_allowed=false)

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s18_p3_integration_preparation.py
PASS: KMFA S18-P3 integration preparation check passed (connectors=3, opme_surfaces=4, backlog=6, live_connector_called=false)

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s18_stage_review.py
PASS: KMFA Stage 18 review check passed (precision_scenarios=5, regression_checks=5, stage_evidence=18, connectors=3, backlog=6, decision_blockers=4, github_upload=0, full_tests=268)
```

## Unit Tests

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_subcontract_procurement_aggregation KMFA.tests.test_project_status_lifecycle KMFA.tests.test_customer_business_analysis KMFA.tests.test_s16_stage_review KMFA.tests.test_access_security_policy KMFA.tests.test_notification_reminders KMFA.tests.test_operations_sop KMFA.tests.test_s17_stage_review KMFA.tests.test_precision_stress_validation KMFA.tests.test_full_regression_acceptance KMFA.tests.test_integration_preparation KMFA.tests.test_s18_stage_review -q
Ran 61 tests in 0.027s
OK
```

## Part6 Validator

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_part6_stages_16_18_review.py
PASS: KMFA Part 6 Stage 16-18 review check passed (stages=3, phases=9, stage_artifacts=48, baseline_refs=74, part6_tests=62, full_tests=274, github_upload=0, delivery_allowed=0)
```

## Full Local Gate

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s KMFA/tests -q
Ran 274 tests
OK

PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/no_omission_check.py
PASS

PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_required_html.py
PASS

PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/metadata_protocol_check.py
PASS

PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/immutability_policy_check.py
PASS

PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_report_grade_gate.py
PASS

PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_no_float_money.py
PASS

PYTHONDONTWRITEBYTECODE=1 python3 scripts/lean_governance.py validate --project KMFA
PASS

PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_project_governance.py --project KMFA
PASS

PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_governance_sync.py --changed-only --enforce-sync
PASS
```

## Safety Scan Result

- Raw/private file scan: pass; no zip, Excel, PDF, sqlite/db, private CSV, bank statement, contract, payroll/salary or tax filing artifact added.
- High-signal secret scan: pass; no credentials or secret material added.
- Stage 18 delivery state: `NO_GO`, `delivery_allowed=false`.
