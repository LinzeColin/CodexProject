# Test Results

- generator: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_outside_scope_candidate_review_residual_difference_diagnostic_handoff.py --generated-at 2026-07-07T00:00:00+10:00` PASS
- validator: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_outside_scope_candidate_review_residual_difference_diagnostic_handoff.py --require-private-handoff` PASS
- focused unit test: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_outside_scope_candidate_review_residual_difference_diagnostic_handoff` PASS; 7 tests OK
- governance sync validator: PASS
- project governance validator: PASS
- lean governance validator: PASS
- raw/private/secret/public-safe scans: pending staged and commit gates
