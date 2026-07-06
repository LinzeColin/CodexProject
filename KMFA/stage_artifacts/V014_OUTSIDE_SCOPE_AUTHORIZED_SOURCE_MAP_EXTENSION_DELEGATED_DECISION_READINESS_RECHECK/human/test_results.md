# Test Results

Recorded validation commands for this phase:

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_outside_scope_authorized_source_map_extension_delegated_decision_readiness_recheck.py KMFA/tools/check_v014_outside_scope_authorized_source_map_extension_delegated_decision_readiness_recheck.py KMFA/tests/test_v014_outside_scope_authorized_source_map_extension_delegated_decision_readiness_recheck.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_outside_scope_authorized_source_map_extension_delegated_decision_readiness_recheck.py --generated-at 2026-07-06T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_outside_scope_authorized_source_map_extension_delegated_decision_readiness_recheck.py --require-private-diagnostic`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_outside_scope_authorized_source_map_extension_delegated_decision_readiness_recheck`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --base-ref HEAD --enforce-sync`
- CSV/JSONL structural parse check for changed governance registries and traceability logs.
- `git diff --check -- KMFA`
- Public-safe artifact scan for raw/private path markers, raw file markers, raw value markers, raw hash markers, and secret-like tokens.
- Git tracked-file boundary scan for private runtime, raw inbox paths, and disallowed raw/private file extensions under `KMFA`.
- Strict secret scan over changed and untracked `KMFA` files.

Current generated check matrix: `9` pass / `0` fail.

Final local review result: all commands above passed before local commit. GitHub upload and app reinstall were not performed.
