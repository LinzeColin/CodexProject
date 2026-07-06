# Test Results

Recorded validation commands for this phase:

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_input.py KMFA/tools/check_v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_input.py KMFA/tests/test_v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_input.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_input.py --generated-at 2026-07-06T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_input.py --require-private-template`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_input`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA`
- `git diff --check -- KMFA`

All listed commands must pass before local commit. The raw inbox is not read, listed, parsed, copied, moved, renamed, deleted, overwritten, normalized or mutated by this phase.
