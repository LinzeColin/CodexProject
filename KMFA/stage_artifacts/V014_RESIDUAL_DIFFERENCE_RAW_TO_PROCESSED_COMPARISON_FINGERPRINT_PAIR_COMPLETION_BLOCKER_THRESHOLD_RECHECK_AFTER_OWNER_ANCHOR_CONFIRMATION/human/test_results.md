# Test Results

- RED: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_v014_residual_difference_raw_to_processed_comparison_fingerprint_pair_completion_blocker_threshold_recheck_after_owner_anchor_confirmation.py` failed before implementation because the generator module did not exist.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_raw_to_processed_comparison_fingerprint_pair_completion_blocker_threshold_recheck_after_owner_anchor_confirmation.py --generated-at 2026-07-07T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_raw_to_processed_comparison_fingerprint_pair_completion_blocker_threshold_recheck_after_owner_anchor_confirmation.py --require-private-threshold`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_v014_residual_difference_raw_to_processed_comparison_fingerprint_pair_completion_blocker_threshold_recheck_after_owner_anchor_confirmation.py`
- Governance validators, diff check, raw/private marker scan, secret scan, private-output git-ignore scan and private-runtime tracked-file scan: PASS.

Expected matrix result: 14/14 PASS.
