# Test Results

- generator: PASS, `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_outside_scope_candidate_review_discrepancy_closure_readiness.py --generated-at 2026-07-07T00:00:00+10:00 --skip-governance-event`
- validator: PASS, `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_outside_scope_candidate_review_discrepancy_closure_readiness.py --require-private-readiness`
- focused unit test: PASS, `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_outside_scope_candidate_review_discrepancy_closure_readiness`, 5 tests OK.
- governance sync: PASS, `python3 scripts/validate_governance_sync.py --changed-only --base-ref HEAD --enforce-sync`
- project governance: PASS, `python3 scripts/validate_project_governance.py --project KMFA`
- lean governance: PASS, `python3 scripts/lean_governance.py validate --project KMFA`
- public-safe added-content scan: PASS after protected public gate field-name cleanup.
