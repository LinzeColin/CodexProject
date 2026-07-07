# Test Results

- generator: PASS `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_outside_scope_candidate_review_residual_difference_report.py --generated-at 2026-07-07T00:00:00+10:00`
- validator: PASS `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_outside_scope_candidate_review_residual_difference_report.py --require-private-report`
- focused unit test: PASS `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_outside_scope_candidate_review_residual_difference_report`
