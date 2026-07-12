# Test Results

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_owner_authorized_anchor_confirmation_blocker_audit.py --generated-at 2026-07-07T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_owner_authorized_anchor_confirmation_blocker_audit.py --require-private-audit`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_residual_difference_owner_authorized_anchor_confirmation_blocker_audit`
- Governance validators, diff check, raw/private marker scan, secret scan and private-output git-ignore scan must pass before local commit.

Expected matrix result: 13/13 PASS.

Final local scan result:

- `PASS: scoped raw/private path scan and high-signal secret scan clean (changed_files=35)`
