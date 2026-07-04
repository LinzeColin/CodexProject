# KMFA v0.1.4 S10-P3 Report Export Test Results

- task_id: `KMFA-V014-S10-P3-REPORT-EXPORT-20260704`
- status: `completed_validated_local_only_no_go_upload_deferred`
- github_upload_performed: `false`
- raw_inbox_read_by_this_phase: `false`
- raw_inbox_mutated_by_this_phase: `false`
- stage10_review_performed: `false`
- raw_value_matching_performed: `false`
- formal_report_allowed: `false`
- business_execution_allowed: `false`

## Command Results

- PASS: `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_s10_p3_report_export.py KMFA/tools/check_v014_s10_p3_report_export.py KMFA/tests/test_v014_s10_p3_report_export.py`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_s10_p3_report_export.py`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s10_p2_report_trust_grade.py`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s10_p3_report_export.py`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_report_export_runtime -q`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s10_p3_report_export_replay.py`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s10_p3_report_export.py`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s10_p3_report_export -q`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --enforce-sync`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_no_float_money.py`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/no_omission_check.py`
- PASS: `git diff --check -- KMFA scripts`
- PASS: changed/untracked parse and raw/private suffix scan.
- PASS: changed/untracked strict secret token scan.
- PASS: scoped S10-P3 public evidence raw/private semantic scan.

Note: Stage 10 overall review and GitHub upload were intentionally not performed in this phase.
