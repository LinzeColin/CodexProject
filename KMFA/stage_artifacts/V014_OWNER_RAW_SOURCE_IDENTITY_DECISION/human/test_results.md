# KMFA v0.1.4 Owner Raw Source Identity Decision Test Results

- status: `PASS`
- task_id: `KMFA-V014-OWNER-RAW-SOURCE-IDENTITY-DECISION-20260705`
- phase_id: `V014_OWNER_RAW_SOURCE_IDENTITY_DECISION`
- focused_unit_test: `PASS`
- owner_decision_validator: `PASS`
- governance_validator: `PASS`
- lean_governance_validator: `PASS`
- governance_sync_validator: `PASS`
- no_float_money_check: `PASS`
- no_omission_check: `PASS`
- structured_parse_checks: `PASS`
- yaml_parse_checks: `PASS`
- raw_private_scan: `PASS`
- secret_scan: `PASS`
- public_artifact_boundary_scan: `PASS`
- diff_check: `PASS`
- note: focused unit test includes an expected negative invalid-decision validation path; command exit code was 0.
- final_go_no_go: `NO_GO`
- owner_decision_supplied: `false`
- github_upload_performed: `false`
- app_reinstall_performed: `false`
- lineage_full_check_complete: `false`
- formal_report_allowed: `false`
- business_execution_performed: `false`

## Commands

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m py_compile KMFA/tools/v014_owner_raw_source_identity_decision.py KMFA/tools/check_v014_owner_raw_source_identity_decision.py KMFA/tests/test_v014_owner_raw_source_identity_decision.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_owner_raw_source_identity_decision -q`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_owner_raw_source_identity_decision.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --enforce-sync`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_no_float_money.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/no_omission_check.py`
- `changed/untracked JSON JSONL CSV structured parse checks`
- `changed/untracked YAML parse checks`
- `changed/untracked raw/private suffix scan`
- `high-signal secret scan across changed/untracked KMFA text files`
- `scoped owner raw source identity public artifact boundary scan`
- `git diff --check -- KMFA scripts`

## Evidence

- `KMFA/stage_artifacts/V014_OWNER_RAW_SOURCE_IDENTITY_DECISION/machine/owner_raw_source_identity_decision_manifest.json`
- `KMFA/stage_artifacts/V014_OWNER_RAW_SOURCE_IDENTITY_DECISION/machine/owner_raw_source_identity_go_no_go_report.json`
- `KMFA/stage_artifacts/V014_OWNER_RAW_SOURCE_IDENTITY_DECISION/machine/owner_raw_source_identity_decision_packet.json`
- `KMFA/stage_artifacts/V014_OWNER_RAW_SOURCE_IDENTITY_DECISION/machine/owner_raw_source_identity_decision_intake_contract.json`
- `KMFA/metadata/quality/v014_owner_raw_source_identity_decision_manifest.json`
- `KMFA/metadata/approvals/v014_raw_source_identity_decision_packet.json`
