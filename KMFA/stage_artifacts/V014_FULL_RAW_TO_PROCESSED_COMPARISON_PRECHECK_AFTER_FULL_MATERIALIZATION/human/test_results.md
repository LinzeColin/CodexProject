# Test Results

Recorded validation commands for this phase:

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_full_raw_to_processed_comparison_precheck_after_full_materialization.py KMFA/tools/check_v014_full_raw_to_processed_comparison_precheck_after_full_materialization.py KMFA/tests/test_v014_full_raw_to_processed_comparison_precheck_after_full_materialization.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_full_raw_to_processed_comparison_precheck_after_full_materialization.py --generated-at 2026-07-07T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_full_raw_to_processed_comparison_precheck_after_full_materialization.py --require-private-precheck`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_full_raw_to_processed_comparison_precheck_after_full_materialization`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_project_governance.py --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/lean_governance.py validate --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_governance_sync.py --changed-only --base-ref HEAD --enforce-sync`
- `git diff --check`

All listed commands must pass before local commit. This phase does not read, list, stat, hash, parse, copy, move, rename, delete, overwrite, normalize or mutate the raw inbox.
