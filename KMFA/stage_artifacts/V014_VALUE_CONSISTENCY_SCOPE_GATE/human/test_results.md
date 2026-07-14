# KMFA v0.1.4 Value Consistency Scope Test Results

- status: `PASS`
- generator: `PASS`
- validator: `PASS`
- focused_unit_test: `PASS`
- governance_validator: `PASS`
- governance_sync_validator: `PASS`
- no_float_money_check: `PASS`
- no_omission_check: `PASS`
- structured_parse: `PASS`
- yaml_parse: `PASS`
- raw_private_scan: `PASS`
- secret_scan: `PASS`
- scoped_public_artifact_boundary_scan: `PASS`
- diff_check: `PASS`

## Commands

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m py_compile KMFA/tools/v014_value_consistency_scope_gate.py KMFA/tools/check_v014_value_consistency_scope_gate.py KMFA/tests/test_v014_value_consistency_scope_gate.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_value_consistency_scope_gate.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_value_consistency_scope_gate.py --require-private-diagnostic`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_value_consistency_scope_gate -q`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --enforce-sync`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_no_float_money.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/no_omission_check.py`
- `changed/untracked JSON JSONL CSV structured parse checks`
- `changed/untracked YAML parse checks using Ruby stdlib`
- `current-change raw/private suffix scan`
- `high-signal secret scan across changed/untracked KMFA text files`
- `scoped value consistency public artifact boundary scan`
- `git diff --check -- KMFA scripts`

## Scope Assertions

- raw inbox mutation: `not_performed`
- raw value matching: `not_performed`
- processed data reconciliation: `not_performed`
- business value consistency verification: `not_performed`
- repeated mismatch final-closeout difference report obligation: `locked`
