# KMFA Stage 10 Review Test Results

- review_id: `KMFA-S10-STAGE-REVIEW-20260630`
- test_time: `2026-06-30T23:59:59+10:00`
- result: `PASS_UPLOAD_READY_LOCAL_ONLY`
- raw_business_data_used: `false`
- github_upload_status: `not_pushed`

## Commands

| Command | Result |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_s10_stage_review -q` | PASS: 1 test |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s10_stage_review.py` | PASS: report_templates=2, sections=11, grade_records=2, export_records=2, html_exports=2, csv_appendices=2, pending_owner_or_authorized_review_records=12, upload_allowed_after_review=true, s11_allowed=false, github_upload_status=not_pushed |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s10_p1_report_templates.py` | PASS: templates=2, sections=11, project_cost_sections=4, business_overview_sections=7, formal_report_allowed=false, trusted_grade_assignment_allowed=false, s10_p2_scope=false, s10_p3_scope=false, ui_scope=false, lineage_full_check_scope=false, external_connector_scope=false |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s10_p2_report_grade_runtime.py` | PASS: grade_records=2, grade_distribution=D:2, pending_reconciliation_count=12, complete_trusted_report_display_allowed=false, formal_report_allowed=false, business_decision_basis_allowed=false, s10_p3_scope=false, export_artifact_count=0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s10_p3_report_export.py` | PASS: export_records=2, html_exports=2, csv_appendices=2, excel_compatible_downloads=2, pdf_private_runtime_enabled=true, committed_pdf_files=0, committed_excel_files=0, formal_report_allowed=false, business_decision_basis_allowed=false, stage10_review=false, github_upload=false |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover KMFA/tests -q` | PASS: 116 tests |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/no_omission_check.py` | PASS: requirements=20, P0=9, P1=8, status_records=386, tasks=162, v1.2_html=45+ |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_required_html.py` | PASS: html=45, core=7 |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_no_float_money.py` | PASS: no KMFA Python float money usage found |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/metadata_protocol_check.py` | PASS: dirs=8, files=19, identifiers=5 |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/immutability_policy_check.py` | PASS: raw_manifest=append_only, derived_versions=append_only, control_events=no_raw_writes |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_report_grade_gate.py` | PASS: quality_grades=Q0-Q5, report_grades=A-D, release_gate=blocked_by_missing_evidence |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/lean_governance.py validate --project KMFA` | PASS: errors 0 / warnings 0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_project_governance.py --project KMFA` | PASS: errors 0 / warnings 0 |
| `ruby -ryaml -e 'count=0; Dir.glob("KMFA/**/*.yaml").sort.each { \|p\| YAML.load_file(p); count += 1 }; puts "PASS: YAML parse ok (files=#{count})"'` | PASS: files=30 |
| JSON/JSONL/CSV parse check | PASS: json=92, jsonl=49, jsonl_records=851, csv=26, csv_rows=718 |
| raw artifact extension scan | PASS: no zip/xlsx/xls/xlsm/pdf/doc/docx/sqlite/db under `KMFA` |
| high-signal secret scan | PASS: hits=0 |
| `git diff --check -- README.md governance/projects.yaml KMFA` | PASS |

## Evidence

- `KMFA/stage_artifacts/S10_STAGE_REVIEW/human/stage10_review_report.md`
- `KMFA/stage_artifacts/S10_STAGE_REVIEW/human/test_results.md`
- `KMFA/stage_artifacts/S10_STAGE_REVIEW/machine/stage10_review_manifest.json`
- `KMFA/tools/check_s10_stage_review.py`
- `KMFA/stage_artifacts/S10_P1_report_templates/human/test_results.md`
- `KMFA/stage_artifacts/S10_P2_report_grade_runtime/human/test_results.md`
- `KMFA/stage_artifacts/S10_P3_report_export/human/test_results.md`

## Remaining Upload Validation

The final GitHub upload step must rerun this command set after reconciling with latest `origin/main`, then record the final commit and push proof.
