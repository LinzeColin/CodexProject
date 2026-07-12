# Test Results

Recorded validation commands for this phase:

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_processed_value_source_map_completion_owner_22_group_decision_response_intake.py KMFA/tools/check_v014_processed_value_source_map_completion_owner_22_group_decision_response_intake.py KMFA/tests/test_v014_processed_value_source_map_completion_owner_22_group_decision_response_intake.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_processed_value_source_map_completion_owner_22_group_decision_response_intake.py --generated-at 2026-07-06T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_source_map_completion_owner_22_group_decision_response_intake.py --require-private-response`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_processed_value_source_map_completion_owner_22_group_decision_response_intake`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA`
- `git diff --check -- KMFA`

All listed commands passed in this run. The raw inbox was not read, listed, parsed, copied, moved, renamed, deleted, overwritten, normalized or mutated by this phase.
