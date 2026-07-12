# Test Results

- RED: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_action_intake_blocker_final_threshold_recheck_after_blocked_handoff` failed before implementation because the generator module did not exist.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_action_intake_blocker_final_threshold_recheck_after_blocked_handoff.py --generated-at 2026-07-08T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_action_intake_blocker_final_threshold_recheck_after_blocked_handoff.py --require-private-final-threshold`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_action_intake_blocker_final_threshold_recheck_after_blocked_handoff`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_governance_sync.py --changed-only --base-ref HEAD --enforce-sync`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_project_governance.py --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/lean_governance.py validate --project KMFA`
- CSV shape checks: PASS.
- `git diff --check -- KMFA`: PASS.
- tracked raw/private scan: PASS, no tracked raw/private/runtime files.
- diff raw/private/secret marker scan: PASS, no raw inbox path, raw file extension, private runtime content, credential or secret marker detected.

Expected matrix result: 12/12 PASS.
