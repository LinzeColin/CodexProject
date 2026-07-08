# Test Results

- RED: focused unittest failed before implementation because the processed-data reconciliation requirement generator was missing.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_external_action_required_before_processed_data_reconciliation.py --generated-at 2026-07-08T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_external_action_required_before_processed_data_reconciliation.py --require-private-processed-data-reconciliation-requirement`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_external_action_required_before_processed_data_reconciliation`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --base-ref HEAD --enforce-sync`
- `git diff --check -- KMFA`
- Raw/private file scan: PASS, no private runtime directory marker, external raw-data folder marker, Downloads path, raw workbook, zip, PDF, SQLite or DB path is included in tracked changed file names.
- Public-safe artifact marker scan: PASS, no exact raw file name, archive member, sheet name, cell address, raw value, normalized decimal, context text, value fingerprint, source record hash, Downloads path, external raw-data folder marker, workbook, zip, PDF, private key or OpenAI-style key marker found.
- Secret scan: PASS, no private key, OpenAI-style key, AWS key, GitHub token or Slack token marker found in the KMFA diff.
- Private runtime ignore check: PASS, all three generated private processed-data reconciliation requirement files are ignored by KMFA local ignore rules.
- CSV shape check: PASS, `parameter_registry.csv` has 1221 rows including header and stable width 34.

Expected matrix result: 12/12 PASS.
