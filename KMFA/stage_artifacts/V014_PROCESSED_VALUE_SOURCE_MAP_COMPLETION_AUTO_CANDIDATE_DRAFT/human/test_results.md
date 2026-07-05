# Test Results

Local verification completed on 2026-07-06.

- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 KMFA/tools/check_v014_processed_value_source_map_completion_auto_candidate_draft.py --require-private-draft`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m unittest KMFA.tests.test_v014_processed_value_source_map_completion_auto_candidate_draft -q`
- PASS: `git diff --check -- KMFA`
- PASS: tracked raw/private suffix scan returned no hits.
- PASS: strict credential scan returned no hits.
- PASS: `PYTHONDONTWRITEBYTECODE=1 python3 scripts/lean_governance.py validate --project KMFA`
- PASS: `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_project_governance.py --project KMFA`

Focused unittest result: `Ran 3 tests in 54.006s - OK`.
