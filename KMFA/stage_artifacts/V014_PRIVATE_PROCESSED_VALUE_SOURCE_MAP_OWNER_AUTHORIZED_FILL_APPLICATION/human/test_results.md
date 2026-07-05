# KMFA v0.1.4 Owner Authorized Fill Application Test Results

- status: `PASS`
- task_id: `KMFA-V014-PRIVATE-PROCESSED-VALUE-SOURCE-MAP-OWNER-AUTHORIZED-FILL-APPLICATION-20260705`
- py_compile: `PASS`
- focused_unit_test: `PASS`
- application_validator: `PASS`
- governance_validator: `PASS`
- lean_governance_validator: `PASS`
- governance_sync_validator: `PASS`
- no_float_money_check: `PASS`
- no_omission_check: `PASS`
- structured_parse_checks: `PASS`
- raw_private_suffix_scan: `PASS`
- high_signal_secret_scan: `PASS`
- current_phase_public_artifact_boundary_scan: `PASS`
- private_runtime_diagnostic_ignored_untracked: `PASS`
- diff_check: `PASS`

## Commands

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m py_compile KMFA/tools/v014_private_processed_value_source_map_owner_authorized_fill_application.py KMFA/tools/check_v014_private_processed_value_source_map_owner_authorized_fill_application.py KMFA/tests/test_v014_private_processed_value_source_map_owner_authorized_fill_application.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_private_processed_value_source_map_owner_authorized_fill_application -q`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_private_processed_value_source_map_owner_authorized_fill_application.py --require-private-application-diagnostic`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_project_governance.py --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/lean_governance.py validate --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_governance_sync.py --changed-only --enforce-sync`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_no_float_money.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/no_omission_check.py`
- `changed/untracked structured parse checks`
- `changed/untracked raw/private suffix scan`
- `high-signal secret scan across changed/untracked text files`
- `current phase public artifact boundary scan`
- `private runtime diagnostic ignored and untracked`
- `git diff --check -- KMFA scripts`
