# KMFA Stage 9 Review Test Results

- review_id: `KMFA-S09-STAGE-REVIEW-20260630`
- test_time: `2026-06-30T23:59:00+10:00`
- result: `PASS_UPLOAD_READY_LOCAL_ONLY`
- raw_business_data_used: `false`
- github_upload_status: `not_pushed`

## Commands

| Command | Result |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s09_p1_project_cost_fact_layer.py` | PASS: fact_records=4, cost_categories=9, unallocated_pool=9, manual_review_queue=3, unresolved_differences=1, s09_p2_scope=false, s09_p3_scope=false, formal_report_allowed=false, github_upload_allowed=false |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s09_p2_margin_cash_margin.py` | PASS: margin_records=4, difference_summary=12, upstream_manual_review_queue=3, upstream_unresolved_differences=1, s09_p3_scope=false, formal_report_allowed=false, github_upload_allowed=false |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s09_p3_scope_reconciliation.py` | PASS: reconciliation_records=12, domain_controls=6, confirmed_resolutions=0, pending_resolutions=12, derived_metric_rerun_allowed=false, formal_report_allowed=false, stage9_review_allowed=false, github_upload_allowed=false |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_a0_golden_fixture -q` | PASS: 3 tests |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_a0_golden_fixture.py` | PASS: fixture_candidates=45, fields_per_candidate=5, private_value_hash_recorded=40, private_value_pending=5, source_anchor_recorded=40, source_anchor_pending=5 |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover KMFA/tests -q` | PASS: 100 tests |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/lean_governance.py validate --project KMFA` | PASS: errors 0 / warnings 0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_project_governance.py --project KMFA` | PASS: errors 0 / warnings 0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/no_omission_check.py` | PASS: requirements=20, P0=9, P1=8, status_records=368, tasks=162, v1.2_html=45+ |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_no_float_money.py` | PASS |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/metadata_protocol_check.py` | PASS: dirs=8, files=19, identifiers=5 |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/immutability_policy_check.py` | PASS |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_report_grade_gate.py` | PASS |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_required_html.py` | PASS: html=45, core=7 |
| `ruby -ryaml -e 'count=0; Dir.glob("KMFA/**/*.yaml").sort.each { \|p\| YAML.load_file(p); count += 1 }; puts "PASS: YAML parse ok (files=#{count})"'` | PASS: files=30 |
| JSON/JSONL/CSV parse check | PASS: json=84, jsonl=45, jsonl_records=807, csv=24, csv_rows=694 |
| raw artifact extension scan | PASS: no zip/xlsx/xls/xlsm/pdf/doc/docx/sqlite/db under `KMFA` |
| high-signal secret scan | PASS: hits=0 after renaming the false-positive `normalized_token` local variable |
| `git diff --check -- README.md governance/projects.yaml KMFA` | PASS |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s09_stage_review.py` | PASS: project_cost_fact_records=4, project_margin_records=4, scope_reconciliation_records=12, pending_owner_or_authorized_review_records=12, upload_allowed_after_review=true, s10_allowed=false, github_upload_status=not_pushed |

## Evidence

- `KMFA/stage_artifacts/S09_STAGE_REVIEW/human/stage9_review_report.md`
- `KMFA/stage_artifacts/S09_STAGE_REVIEW/human/test_results.md`
- `KMFA/stage_artifacts/S09_STAGE_REVIEW/machine/stage9_review_manifest.json`
- `KMFA/tools/check_s09_stage_review.py`
- `KMFA/stage_artifacts/S09_P1_project_cost_fact_layer/human/test_results.md`
- `KMFA/stage_artifacts/S09_P2_margin_cash_margin/human/test_results.md`
- `KMFA/stage_artifacts/S09_P3_scope_reconciliation/human/test_results.md`

## Remaining Upload Validation

The final GitHub upload step must rerun this command set after reconciling with latest `origin/main`, then record the final commit and push proof.
