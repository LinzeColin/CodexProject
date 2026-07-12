# Test Results

Status: passed locally.

Commands:

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_processed_value_source_map_completion_private_raw_value_matching_dry_run.py --generated-at 2026-07-06T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_source_map_completion_private_raw_value_matching_dry_run.py --require-private-dry-run`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_processed_value_source_map_completion_private_raw_value_matching_dry_run`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA`
- `git diff --check -- KMFA`
- `git ls-files KMFA | rg -n '\.(zip|xlsx|xlsm|xls|pdf|sqlite|sqlite3|db|pem|key|p12|pfx)$|\.codex_private_runtime'`
- high-confidence tracked secret marker scan under `KMFA`
