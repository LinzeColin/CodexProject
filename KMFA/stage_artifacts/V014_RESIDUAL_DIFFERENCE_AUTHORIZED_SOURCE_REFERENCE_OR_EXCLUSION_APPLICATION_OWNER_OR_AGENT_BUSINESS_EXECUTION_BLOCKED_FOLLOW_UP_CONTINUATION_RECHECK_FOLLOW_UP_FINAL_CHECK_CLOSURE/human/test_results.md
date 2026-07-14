# Test Results

- RED: focused unittest failed before implementation because the business execution blocked follow-up continuation recheck follow-up final check closure generator was missing.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_business_execution_blocked_follow_up_continuation_recheck_follow_up_final_check_closure.py --generated-at 2026-07-08T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_business_execution_blocked_follow_up_continuation_recheck_follow_up_final_check_closure.py --require-private-business-execution-blocked-follow-up-continuation-recheck-follow-up-final-check-closure`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_residual_difference_authorized_source_reference_or_exclusion_application_owner_or_agent_business_execution_blocked_follow_up_continuation_recheck_follow_up_final_check_closure`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --base-ref HEAD --enforce-sync`
- CSV shape check, diff raw-extension check, raw/private marker scan, secret scan and ignored-runtime tracked-file scan: PASS.

Expected matrix result: 12/12 PASS.
