# KMFA Stage 8 Review Test Results

- review_id: `KMFA-S08-STAGE-REVIEW-20260630`
- test_time: `2026-06-30T23:00:00+10:00`
- result: `PASS_UPLOAD_READY_LOCAL_ONLY`
- raw_business_data_used: `false`
- github_upload_status: `not_pushed`

## Commands

| Command | Result |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s08_p1_project_composite_key.py` | PASS: components=8, profiles=4, matches=3, manual_review_queue=2, strong_threshold_bps=8500, human_review_threshold_bps=7000, formal_report_allowed=false, github_upload_allowed=false |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s08_p2_business_entity_model.py` | PASS: entities=8, relationships=14, lifecycle_statuses=32, s08_p3_scope=false, fact_layer_scope=false, formal_report_allowed=false, github_upload_allowed=false |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s08_p3_entity_matching_quality.py` | PASS: scenarios=4, quality_cases=4, manual_review_queue=3, stage8_review_scope=false, fact_layer_scope=false, formal_report_allowed=false, github_upload_allowed=false |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover KMFA/tests -q` | PASS: 88 tests |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/lean_governance.py validate --project KMFA` | PASS: errors 0 / warnings 0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_project_governance.py --project KMFA` | PASS: errors 0 / warnings 0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_no_float_money.py` | PASS |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_required_html.py` | PASS: html=45, core=7 |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/no_omission_check.py` | PASS: requirements=20, P0=9, P1=8, status_records=350, tasks=162, v1.2_html=45+ |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/metadata_protocol_check.py` | PASS: dirs=8, files=19, identifiers=5 |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/immutability_policy_check.py` | PASS |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_report_grade_gate.py` | PASS |
| `ruby -ryaml -e 'count=0; Dir.glob("KMFA/**/*.yaml").sort.each { \|p\| YAML.load_file(p); count += 1 }; puts "PASS: YAML parse ok (files=#{count})"'` | PASS: files=30 |
| JSON/JSONL/CSV parse check | PASS: json=76, jsonl=39, jsonl_records=729, csv=24, csv_rows=676 |
| raw artifact extension scan | PASS: no zip/xlsx/xls/pdf/docx files under `KMFA` |
| high-signal secret scan | PASS: hits=0 |
| `git diff --check -- README.md governance/projects.yaml KMFA` | PASS |
| S08 stage review evidence consistency check | PASS: P1/P2/P3/review artifacts and manifest schemas aligned |

## Evidence

- `KMFA/stage_artifacts/S08_STAGE_REVIEW/human/stage8_review_report.md`
- `KMFA/stage_artifacts/S08_STAGE_REVIEW/human/test_results.md`
- `KMFA/stage_artifacts/S08_STAGE_REVIEW/machine/stage8_review_manifest.json`
- `KMFA/stage_artifacts/S08_P1_project_composite_key/human/test_results.md`
- `KMFA/stage_artifacts/S08_P2_business_entity_model/human/test_results.md`
- `KMFA/stage_artifacts/S08_P3_entity_matching_quality/human/test_results.md`

## Remaining Upload Validation

The final GitHub upload step must rerun this command set after reconciling with latest `origin/main`, then record the final commit and push proof.
