# KMFA Stage 7 Review Test Results

- review_id: `KMFA-S07-STAGE-REVIEW-20260630`
- test_time: `2026-06-30T19:10:00+10:00`
- result: `PASS_UPLOAD_READY_LOCAL_ONLY`
- raw_business_data_used: `false`
- github_upload_status: `not_pushed`

## Commands

| Command | Result |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s07_p1_finance_file_adapter.py` | PASS: categories=9, field_candidates=45, field_reports=9, source_header_hashes=45, wps_scope=false, redcircle_scope=false, formal_report_allowed=false |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s07_p2_wps_file_adapter.py` | PASS: exports=4, field_mappings=20, conversion_guidance=4, rule_versions=1, source_header_hashes=20, finance_scope=false, redcircle_scope=false, formal_report_allowed=false |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s07_p3_redcircle_postponement.py` | PASS: templates=4, rollback_plans=4, d15_connector_allowed=false, read_only_required=true, hash_retention_required=true, rollback_plan_required=true, formal_report_allowed=false |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover KMFA/tests -q` | PASS: 77 tests |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/lean_governance.py validate --project KMFA` | PASS: errors 0 / warnings 0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_project_governance.py --project KMFA` | PASS: errors 0 / warnings 0 |
| `ruby -ryaml -e 'count=0; Dir.glob("KMFA/**/*.yaml").sort.each { \|p\| YAML.load_file(p); count += 1 }; puts "PASS: YAML parse ok (files=#{count})"'` | PASS: files=30 |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_no_float_money.py` | PASS |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/metadata_protocol_check.py` | PASS: dirs=8, files=19, identifiers=5 |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/no_omission_check.py` | PASS: requirements=20, P0=9, P1=8, status_records=331, tasks=162, v1.2_html=45+ |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/immutability_policy_check.py` | PASS |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_report_grade_gate.py` | PASS |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_required_html.py` | PASS: html=45, core=7 |
| JSON/JSONL/CSV parse check | PASS: json=66, jsonl=32, jsonl_records=638, csv=24, csv_rows=658 |
| `git diff --check -- README.md governance/projects.yaml KMFA` | PASS |
| raw artifact extension scan | PASS: no zip/xlsx/xls/pdf outside taskpack |
| high-signal secret scan | PASS: hits=0 |
| S07 stage review evidence consistency check | PASS: P1/P2/P3 artifacts and manifest schemas aligned |

## Evidence

- `KMFA/stage_artifacts/S07_STAGE_REVIEW/human/stage7_review_report.md`
- `KMFA/stage_artifacts/S07_STAGE_REVIEW/human/test_results.md`
- `KMFA/stage_artifacts/S07_STAGE_REVIEW/machine/stage7_review_manifest.json`
- `KMFA/stage_artifacts/S07_P1_finance_file_adapter/human/test_results.md`
- `KMFA/stage_artifacts/S07_P2_wps_file_adapter/human/test_results.md`
- `KMFA/stage_artifacts/S07_P3_redcircle_postponement_policy/human/test_results.md`

## Remaining Upload Validation

The final GitHub upload step must rerun this command set after reconciling with latest `origin/main`, then record the final commit and push proof.
