# KMFA Stage 11 Review Test Results

- review_id: `KMFA-S11-STAGE-REVIEW-20260701`
- test_time: `2026-07-01T11:30:00+10:00`
- result: `PASS_UPLOAD_READY_LOCAL_ONLY`
- raw_business_data_used: `false`
- github_upload_status: `not_pushed`

## Commands

| Command | Result |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_s11_stage_review -q` | PASS: 1 test |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s11_stage_review.py` | PASS: home_modules=8, source_rows=13, project_rows=4, html_exports=3, pending_owner_or_authorized_review_records=12, upload_allowed_after_review=true, s12_allowed=false, github_upload_status=not_pushed |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s11_p1_home_navigation.py` | PASS: navigation_modules=8, html_exports=1, formal_report_allowed=false, s11_p2_scope=false, s11_p3_scope=false, stage11_review=false, github_upload=false |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s11_p2_source_check_board.py` | PASS: matrix_rows=13, html_exports=1, columns=11, statuses=5, status_click_detail=true, large_yellow_surface_count=0, formal_report_allowed=false, s11_p3_scope=false, stage11_review=false, github_upload=false |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s11_p3_project_cost_page.py` | PASS: projects=4, margin_records=4, cost_categories=9, pending_reconciliations=12, report_preview=true, report_grade=D, quality_bypass=false, formal_report_allowed=false, stage11_review=false, github_upload=false |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s KMFA/tests -q` | PASS: 132 tests |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/no_omission_check.py` | PASS: requirements=20, P0=9, P1=8, status_records=406, tasks=162, v1.2_html=45+ |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_required_html.py` | PASS: html=45, core=7 |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_no_float_money.py` | PASS: no KMFA Python float money usage found |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/metadata_protocol_check.py` | PASS: metadata protocol check passed |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/immutability_policy_check.py` | PASS: immutability policy check passed |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_report_grade_gate.py` | PASS: report grade gate check passed |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/lean_governance.py validate --project KMFA` | PASS: errors 0 / warnings 0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_project_governance.py --project KMFA` | PASS: errors 0 / warnings 0 |
| `ruby -e 'require "yaml"; Dir.glob("KMFA/**/*.yaml").each { \|p\| YAML.load_file(p) }'` | PASS: YAML parse ok |
| JSON/JSONL parse check | PASS |
| raw artifact extension scan | PASS: no forbidden raw/private file extensions committed outside taskpack baseline |
| high-signal secret scan | PASS: hits=0 |
| `git diff --check -- README.md governance/projects.yaml KMFA` | PASS |

## Evidence

- `KMFA/stage_artifacts/S11_STAGE_REVIEW/human/stage11_review_report.md`
- `KMFA/stage_artifacts/S11_STAGE_REVIEW/human/test_results.md`
- `KMFA/stage_artifacts/S11_STAGE_REVIEW/machine/stage11_review_manifest.json`
- `KMFA/tools/check_s11_stage_review.py`
- `KMFA/stage_artifacts/S11_P1_home_navigation/human/test_results.md`
- `KMFA/stage_artifacts/S11_P2_source_check_board/human/test_results.md`
- `KMFA/stage_artifacts/S11_P3_project_cost_page/human/test_results.md`

## Remaining Upload Validation

The final GitHub upload step must rerun this command set after reconciling with latest `origin/main`, then record the final commit and push proof.
