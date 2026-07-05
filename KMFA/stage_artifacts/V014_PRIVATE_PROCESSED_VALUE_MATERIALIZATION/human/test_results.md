# Test Results

- phase: `V014_PRIVATE_PROCESSED_VALUE_MATERIALIZATION`
- status: `PASS`
- red_test_recorded: `true`
- focused_unit_tests: `2 PASS`
- validator_status: `PASS`
- governance_validator_status: `PASS`
- raw_secret_scan_status: `PASS`
- public_artifact_boundary_scan_status: `PASS`
- private_runtime_git_status: `ignored_not_tracked_not_untracked`
- raw_inbox_access_performed: `false`
- raw_inbox_mutation_performed: `false`

## Commands
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m py_compile KMFA/tools/v014_private_processed_value_materialization.py KMFA/tools/check_v014_private_processed_value_materialization.py KMFA/tests/test_v014_private_processed_value_materialization.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_private_processed_value_materialization.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_private_processed_value_materialization.py --require-private-materialization`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_private_processed_value_materialization -q`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --enforce-sync`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_no_float_money.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/no_omission_check.py`
- `changed/untracked JSON JSONL CSV YAML structured parse checks`
- `changed/untracked raw/private suffix scan`
- `high-signal secret scan across changed/untracked KMFA text files`
- `scoped current-phase public artifact boundary scan`
- `private runtime tracked/untracked/ignore scan`
- `git diff --check -- KMFA scripts`
