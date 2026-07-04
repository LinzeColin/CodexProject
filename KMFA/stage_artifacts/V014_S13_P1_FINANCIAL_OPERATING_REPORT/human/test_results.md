# KMFA v0.1.4 S13-P1 Test Results

- task_id: `KMFA-V014-S13-P1-FINANCIAL-OPERATING-REPORT-20260705`
- status: `PASS`
- final_validation_time: `2026-07-05T04:58:00+10:00`

## Commands

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_s13_p1_financial_operating_report.py KMFA/tools/check_v014_s13_p1_financial_operating_report.py KMFA/tests/test_v014_s13_p1_financial_operating_report.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_s13_p1_financial_operating_report.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s12_stage_review.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s13_p1_financial_operating_report.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s13_p1_financial_operating_report.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s13_p1_financial_operating_report -q`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --enforce-sync`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_no_float_money.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/no_omission_check.py`
- structured JSON/JSONL/CSV parse checks over changed/untracked KMFA and scripts paths
- Ruby YAML structured parse checks over changed/untracked YAML files
- changed/untracked raw/private suffix scan
- high-signal secret scan over changed/untracked KMFA and scripts text paths
- scoped S13-P1 artifact boundary scan
- `git diff --check -- KMFA scripts`

## Results

- PASS: py_compile completed with no syntax errors.
- PASS: generator refreshed S13-P1 evidence with source_lanes=4, drafts=2, html=2, field_mappings=39, formal_report=false, S13-P2=false, S13-P3=false, Stage13 review=false and GitHub upload=false.
- PASS: Stage 12 review dependency validator passed and routed to S13-P1 with GitHub upload false.
- PASS: legacy S13-P1 validator passed.
- PASS: v0.1.4 S13-P1 validator passed with pending_reconciliation=12 and report_grade=D.
- PASS: focused unit test ran 1 test in 435.416s and passed.
- PASS: project governance, lean governance and changed-only governance sync validators returned errors=0.
- PASS: no-float and no-omission checks passed.
- PASS: structured parse, Ruby YAML parse, raw/private suffix scan, high-signal secret scan, scoped S13-P1 artifact boundary scan and diff check passed.

## Boundary

- raw_private_inbox_access: `false`
- s13_p2_performed: `false`
- s13_p3_performed: `false`
- stage13_review_performed: `false`
- github_upload_performed: `false`
- formal_report_release_performed: `false`
- business_execution_performed: `false`
