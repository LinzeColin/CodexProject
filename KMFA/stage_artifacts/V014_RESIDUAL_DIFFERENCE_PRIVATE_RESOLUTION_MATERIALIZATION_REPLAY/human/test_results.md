# Test Results

Recorded validation commands for this phase:

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_residual_difference_private_resolution_materialization_replay.py KMFA/tools/check_v014_residual_difference_private_resolution_materialization_replay.py KMFA/tests/test_v014_residual_difference_private_resolution_materialization_replay.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_private_resolution_materialization_replay.py --generated-at 2026-07-07T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_private_resolution_materialization_replay.py --require-private-replay`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_residual_difference_private_resolution_materialization_replay`
- `python3 scripts/validate_governance_sync.py --changed-only --base-ref HEAD --enforce-sync`
- `python3 scripts/validate_project_governance.py --changed-only --base-ref HEAD --enforce-sync`
- `python3 scripts/lean_governance.py validate --changed-only --base-ref HEAD --enforce-sync`
- `git diff --check`

All listed commands must pass before local commit. This phase does not read, list, parse, copy, move, rename, delete, overwrite, normalize or mutate the raw inbox.
