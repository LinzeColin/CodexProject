# KMFA v0.1.4 S11-P1 Home Navigation Test Results

- task_id: `KMFA-V014-S11-P1-HOME-NAVIGATION-20260704`
- status: `completed_validated_local_only_no_go_upload_deferred`
- github_upload_performed: `false`
- raw_inbox_read_by_this_phase: `false`
- raw_inbox_mutated_by_this_phase: `false`
- s11_p2_performed: `false`
- s11_p3_performed: `false`
- stage11_review_performed: `false`
- formal_report_allowed: `false`
- business_execution_allowed: `false`

## Command Results

- PASS: `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_s11_p1_home_navigation.py KMFA/tools/check_v014_s11_p1_home_navigation.py KMFA/tests/test_v014_s11_p1_home_navigation.py`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s10_stage_review.py`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s11_p1_home_navigation.py`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_s11_p1_home_navigation.py`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s11_p1_home_navigation.py`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s11_p1_home_navigation -q`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --enforce-sync`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_no_float_money.py`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/no_omission_check.py`
- PASS: `git diff --check -- KMFA scripts`
- PASS: changed/untracked structured parse scan.
- PASS: changed/untracked raw/private suffix scan.
- PASS: changed/untracked strict secret token scan.
- PASS: scoped S11-P1 public evidence raw/private semantic scan.

Note: S11-P2, S11-P3, Stage 11 overall review, GitHub upload, raw value matching, lineage full check, formal report release, live connector, app reinstall, and business execution were intentionally not performed in this phase.
