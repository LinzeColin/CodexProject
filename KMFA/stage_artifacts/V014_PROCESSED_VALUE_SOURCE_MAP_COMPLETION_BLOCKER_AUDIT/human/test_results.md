# KMFA v0.1.4 Processed Value Source-map Completion Blocker Audit Test Results

- status: `PASS`
- task_id: `KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-BLOCKER-AUDIT-20260706`
- generator: `PASS`
- validator: `PASS`
- focused_unit_test: `PASS`
- structured_parse: `PASS`
- yaml_parse: `PASS`
- governance_validator: `PASS`
- no_omission_check: `PASS`
- no_float_money_check: `PASS`
- raw_private_scan: `PASS`
- secret_scan: `PASS`
- public_artifact_boundary_scan: `PASS`
- diff_check: `PASS`

## Commands

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m py_compile KMFA/tools/v014_processed_value_source_map_completion_blocker_audit.py KMFA/tools/check_v014_processed_value_source_map_completion_blocker_audit.py KMFA/tests/test_v014_processed_value_source_map_completion_blocker_audit.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_processed_value_source_map_completion_blocker_audit.py --generated-at 2026-07-06T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_source_map_completion_blocker_audit.py --require-private-diagnostic`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_processed_value_source_map_completion_blocker_audit -q`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --enforce-sync`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/no_omission_check.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_no_float_money.py`
