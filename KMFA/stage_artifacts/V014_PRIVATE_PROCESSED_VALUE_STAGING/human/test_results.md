# KMFA v0.1.4 Private Processed Value Staging Test Results

status: PASS
phase: V014_PRIVATE_PROCESSED_VALUE_STAGING
task: KMFA-V014-PRIVATE-PROCESSED-VALUE-STAGING-20260705
validation_time: 2026-07-05T23:59:59+10:00

## Commands

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m py_compile KMFA/tools/v014_private_processed_value_staging.py KMFA/tools/check_v014_private_processed_value_staging.py KMFA/tests/test_v014_private_processed_value_staging.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_private_processed_value_staging.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_private_processed_value_staging.py --require-private-staging`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_private_processed_value_staging -q`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --enforce-sync`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_no_float_money.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/no_omission_check.py`
- `changed/untracked JSON JSONL CSV structured parse checks`
- `changed/untracked YAML parse checks`
- `changed/untracked raw/private suffix scan`
- `high-signal secret scan across changed/untracked KMFA text files`
- `scoped current-phase public artifact boundary scan`
- `private runtime tracked/untracked scan`
- `git diff --check -- KMFA scripts`

## Results

- PASS: py_compile
- PASS: generator target_slots=149 value_fingerprints=0 decision=NO_GO
- PASS: validator target_slots=149 value_fingerprints=0 business_consistency=false github_upload=false
- PASS: focused unit test ran 2 tests
- PASS: project governance errors=0 warnings=0
- PASS: lean governance errors=0 warnings=0
- PASS: changed-only governance sync errors=0 warnings=0
- PASS: no float money usage found
- PASS: no omission check passed status_records=914 tasks=162
- PASS: structured parse checks
- PASS: YAML parse checks
- PASS: raw/private suffix and high-signal secret scan
- PASS: scoped current-phase public artifact boundary scan
- PASS: private runtime not tracked and not untracked
- PASS: diff check clean

## Gate State

- processed_target_slot_count: `149`
- approved_private_processed_target_slot_count: `149`
- private_processed_value_fingerprint_count: `0`
- comparable_value_pair_count: `0`
- processed_value_materialization_complete: `false`
- raw_to_processed_value_comparison_performed: `false`
- business_value_consistency_verified: `false`
- raw_inbox_access_by_this_phase: `false`
- github_upload_performed: `false`
- app_reinstall_performed: `false`
- formal_report_performed: `false`
- business_execution_performed: `false`
- go_no_go: `NO_GO`
