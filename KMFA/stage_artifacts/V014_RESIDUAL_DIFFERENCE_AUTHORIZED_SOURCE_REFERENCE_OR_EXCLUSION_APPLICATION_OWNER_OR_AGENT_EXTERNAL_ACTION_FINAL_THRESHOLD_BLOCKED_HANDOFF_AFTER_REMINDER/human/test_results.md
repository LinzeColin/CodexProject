# Test Results

- RED: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_external_action_final_threshold_blocked_handoff_after_reminder` failed before implementation because the generator module did not exist.
- PASS: `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_external_action_final_threshold_blocked_handoff_after_reminder.py KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_external_action_final_threshold_blocked_handoff_after_reminder.py KMFA/tests/test_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_external_action_final_threshold_blocked_handoff_after_reminder.py`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_external_action_final_threshold_blocked_handoff_after_reminder.py --generated-at 2026-07-08T00:00:00+10:00`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_external_action_final_threshold_blocked_handoff_after_reminder.py --require-private-blocked-handoff`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_external_action_final_threshold_blocked_handoff_after_reminder`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --base-ref HEAD --enforce-sync`
- PASS: CSV/JSONL shape check: parameter registry 1206 rows x 34 columns; traceability matrix 422 rows x 12 columns; JSONL files parse successfully.
- PASS: `git diff --check`
- PASS: added public governance/doc lines scan, new artifact raw/private scan, added code/test raw/secret scan, and private runtime git-ignore check.

Expected matrix result: 12/12 PASS.
