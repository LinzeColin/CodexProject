# Test Results

Recorded validation commands for this phase:

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_linked_scope_raw_to_processed_comparison_dry_run.py KMFA/tools/check_v014_linked_scope_raw_to_processed_comparison_dry_run.py KMFA/tests/test_v014_linked_scope_raw_to_processed_comparison_dry_run.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_linked_scope_raw_to_processed_comparison_dry_run.py --generated-at 2026-07-06T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_linked_scope_raw_to_processed_comparison_dry_run.py --require-private-dry-run`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_linked_scope_raw_to_processed_comparison_dry_run`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --base-ref HEAD --enforce-sync`
- `git diff --check -- KMFA`

All listed commands must pass before local commit. This phase does not read, list, stat, hash, parse, copy, move, rename, delete, overwrite, normalize or mutate the raw inbox.
