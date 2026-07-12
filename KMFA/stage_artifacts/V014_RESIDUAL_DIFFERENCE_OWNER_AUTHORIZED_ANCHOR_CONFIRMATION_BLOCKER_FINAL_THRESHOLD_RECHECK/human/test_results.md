# Test Results

- RED: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_v014_residual_difference_owner_authorized_anchor_confirmation_blocker_final_threshold_recheck.py` failed before implementation because the generator module did not exist.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_owner_authorized_anchor_confirmation_blocker_final_threshold_recheck.py --generated-at 2026-07-07T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_owner_authorized_anchor_confirmation_blocker_final_threshold_recheck.py --require-private-final-threshold`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_v014_residual_difference_owner_authorized_anchor_confirmation_blocker_final_threshold_recheck.py`
- Governance validators, structured parsers, diff check, raw/private marker scan, secret scan, private-output git-ignore scan and private-runtime tracked-file scan: PASS.

Expected matrix result: 13/13 PASS.
