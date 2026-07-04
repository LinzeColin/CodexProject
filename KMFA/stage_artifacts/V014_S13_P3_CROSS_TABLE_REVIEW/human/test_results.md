# KMFA v0.1.4 S13-P3 Test Results

- task_id: `KMFA-V014-S13-P3-CROSS-TABLE-REVIEW-20260705`
- status: `PASS`
- final_validation_time: `2026-07-05T05:43:00+10:00`

## Commands

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_s13_p3_cross_table_review.py KMFA/tools/check_v014_s13_p3_cross_table_review.py KMFA/tests/test_v014_s13_p3_cross_table_review.py`
  - result: `PASS`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_s13_p3_cross_table_review.py`
  - result: `PASS: KMFA v0.1.4 S13-P3 cross-table review evidence generated (review_dimensions=4, difference_queue=4, quality_report=1, html=1, pending_reconciliation=12, report_grade=D, formal_report=false, difference_auto_resolution=false, stage13_review=false, github_upload=false)`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s13_p3_cross_table_review.py`
  - result: `PASS: KMFA v0.1.4 S13-P3 cross-table review validated (review_dimensions=4, difference_queue=4, quality_report=1, pending_reconciliation=12, report_grade=D, formal_report=false, difference_auto_resolution=false, stage13_review=false, github_upload=false)`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s13_p3_cross_table_review -q`
  - result: `Ran 1 test in 439.461s; OK`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA`
  - result: `PASS: errors=0 warnings=0`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA`
  - result: `PASS: errors=0 warnings=0`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --enforce-sync`
  - result: `PASS: errors=0 warnings=0`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_no_float_money.py`
  - result: `PASS: no KMFA Python float money usage found`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/no_omission_check.py`
  - result: `PASS: KMFA no omission check passed (requirements=20, P0=9, P1=8, status_records=775, tasks=162, v1.2_html=45+)`
- changed/untracked JSON/JSONL/CSV structured parse checks
  - result: `PASS: json=2 jsonl=5 csv=2`
- changed/untracked Ruby YAML parse checks
  - result: `PASS: yaml_files=6`
- changed/untracked raw/private suffix scan
  - result: `PASS: files=35`
- high-signal secret scan across changed/untracked KMFA text files
  - result: `PASS: files=35`
- scoped S13-P3 artifact boundary scan
  - result: `PASS: files=9`
- `git diff --check -- KMFA scripts`
  - result: `PASS`

## Scope Confirmed False

- Stage 13 review: `false`
- S14: `false`
- GitHub upload: `false`
- protected source matching: `false`
- lineage full check: `false`
- formal report: `false`
- business decision basis: `false`
- difference auto resolution: `false`
- difference closure: `false`
- legal collection/payment/invoice/tax/business execution: `false`
- raw/private inbox read/list/stat/hash/mutation/write: `false`
