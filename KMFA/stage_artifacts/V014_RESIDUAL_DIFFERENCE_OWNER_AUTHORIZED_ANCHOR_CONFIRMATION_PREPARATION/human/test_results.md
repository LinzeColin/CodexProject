# Test Results

- RED: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_v014_residual_difference_owner_authorized_anchor_confirmation_preparation.py` failed before implementation because the generator module did not exist.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_owner_authorized_anchor_confirmation_preparation.py --generated-at 2026-07-07T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_owner_authorized_anchor_confirmation_preparation.py --require-private-preparation`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_v014_residual_difference_owner_authorized_anchor_confirmation_preparation.py`
- Governance validators, diff check, raw/private marker scan, secret scan, private-output git-ignore scan and private-runtime tracked-file scan: PASS.

Expected matrix result: 15/15 PASS.
