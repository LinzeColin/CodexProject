# Test Results

- RED: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_v014_residual_difference_authorized_source_reference_or_exclusion_application_blocker_threshold_recheck_after_raw_refresh.py` failed before implementation because the generator module did not exist.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_blocker_threshold_recheck_after_raw_refresh.py --generated-at 2026-07-08T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_blocker_threshold_recheck_after_raw_refresh.py --require-private-threshold`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_v014_residual_difference_authorized_source_reference_or_exclusion_application_blocker_threshold_recheck_after_raw_refresh.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m py_compile KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_blocker_threshold_recheck_after_raw_refresh.py KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_blocker_threshold_recheck_after_raw_refresh.py KMFA/tests/test_v014_residual_difference_authorized_source_reference_or_exclusion_application_blocker_threshold_recheck_after_raw_refresh.py`
- `python3 scripts/validate_project_governance.py --project KMFA`
- `python3 scripts/lean_governance.py validate --project KMFA`
- `python3 scripts/validate_governance_sync.py --changed-only --base-ref HEAD --enforce-sync`
- CSV width check, diff check, raw/private filename scan, added-line secret scan, private-output git-ignore scan and private-runtime tracked-file scan: PASS before local commit.

Matrix result: 14/14 PASS.
