# Test Results

- RED: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_external_action_blocked_handoff_final_threshold_recheck_after_reminder` failed before implementation because the generator module did not exist.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_external_action_blocked_handoff_final_threshold_recheck_after_reminder.py --generated-at 2026-07-08T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_external_action_blocked_handoff_final_threshold_recheck_after_reminder.py --require-private-final-threshold`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_external_action_blocked_handoff_final_threshold_recheck_after_reminder`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_external_action_blocked_handoff_final_threshold_recheck_after_reminder.py KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_external_action_blocked_handoff_final_threshold_recheck_after_reminder.py KMFA/tests/test_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_external_action_blocked_handoff_final_threshold_recheck_after_reminder.py` passed.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA` passed.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA` passed.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --base-ref HEAD --enforce-sync` passed.
- CSV/JSONL shape check passed: `TRACEABILITY_MATRIX.csv` 421 rows x 12 columns, `parameter_registry.csv` 1203 rows x 34 columns, `development_events.jsonl` 528 records, `stage_status.jsonl` 1221 records, `v1_4_stage_phase_task_status.jsonl` 666 records.
- `git diff --check` passed.
- Public artifact/tool/test marker scan, public path scan, added-line raw/secret scan and private-runtime ignore check passed before commit.

Expected matrix result: 12/12 PASS. Actual matrix result: 12/12 PASS.
