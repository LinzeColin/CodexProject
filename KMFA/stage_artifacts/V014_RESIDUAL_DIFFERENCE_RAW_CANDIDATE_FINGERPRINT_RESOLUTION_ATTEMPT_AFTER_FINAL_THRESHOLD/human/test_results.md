# Test Results

- RED: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_v014_residual_difference_raw_candidate_fingerprint_resolution_attempt_after_final_threshold.py` failed before implementation because the generator module did not exist.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_raw_candidate_fingerprint_resolution_attempt_after_final_threshold.py --generated-at 2026-07-07T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_raw_candidate_fingerprint_resolution_attempt_after_final_threshold.py --require-private-resolution`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_v014_residual_difference_raw_candidate_fingerprint_resolution_attempt_after_final_threshold.py`
- Governance validators, diff check, raw/private marker scan, secret scan, private-output git-ignore scan and private-runtime tracked-file scan: PASS.

Expected matrix result: 15/15 PASS.
