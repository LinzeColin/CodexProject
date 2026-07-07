# Test Results

- RED: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_v014_residual_difference_authorized_source_reference_or_exclusion_application_blocker_final_threshold_recheck_after_raw_refresh.py` failed before implementation because the generator module did not exist.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_blocker_final_threshold_recheck_after_raw_refresh.py --generated-at 2026-07-08T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_blocker_final_threshold_recheck_after_raw_refresh.py --require-private-final-threshold`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_v014_residual_difference_authorized_source_reference_or_exclusion_application_blocker_final_threshold_recheck_after_raw_refresh.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_blocker_final_threshold_recheck_after_raw_refresh.py KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_blocker_final_threshold_recheck_after_raw_refresh.py KMFA/tests/test_v014_residual_difference_authorized_source_reference_or_exclusion_application_blocker_final_threshold_recheck_after_raw_refresh.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --base-ref HEAD --enforce-sync`
- CSV shape checks, diff check, raw/private scan, secret scan and private-runtime tracked-file scan: PASS before commit.

Expected matrix result: 14/14 PASS.
