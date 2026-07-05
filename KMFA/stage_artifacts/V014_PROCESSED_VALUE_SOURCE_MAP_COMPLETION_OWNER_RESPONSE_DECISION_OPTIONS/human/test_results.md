# Test Results

Local verification completed on 2026-07-06.

- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_processed_value_source_map_completion_owner_response_decision_options.py --generated-at 2026-07-06T00:00:00+10:00`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_source_map_completion_owner_response_decision_options.py --require-private-options`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_processed_value_source_map_completion_owner_response_decision_options -q`
- PASS: `PYTHONDONTWRITEBYTECODE=1 python3 scripts/lean_governance.py validate --project KMFA`
- PASS: `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_project_governance.py --project KMFA`
- PASS: `git diff --check -- KMFA`
- PASS: tracked raw/private suffix scan returned no hits.
- PASS: strict credential scan returned no hits.

Focused unittest result: `Ran 3 tests in 0.350s - OK`.
