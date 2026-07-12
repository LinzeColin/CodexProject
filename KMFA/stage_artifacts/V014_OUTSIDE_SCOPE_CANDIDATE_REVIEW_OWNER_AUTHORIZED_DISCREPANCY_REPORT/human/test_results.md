# Test Results

- generator: PASS - `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_outside_scope_candidate_review_owner_authorized_discrepancy_report.py --generated-at 2026-07-07T00:00:00+10:00`
- validator: PASS - `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_outside_scope_candidate_review_owner_authorized_discrepancy_report.py --require-private-discrepancy`
- focused unit test: PASS - `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_outside_scope_candidate_review_owner_authorized_discrepancy_report`
- governance sync: PASS - `python3 scripts/validate_governance_sync.py --changed-only --base-ref HEAD --enforce-sync`
- project governance: PASS - `python3 scripts/validate_project_governance.py --project KMFA`
- lean governance: PASS - `python3 scripts/lean_governance.py validate --project KMFA`
- whitespace: PASS - `git diff --check -- KMFA`
