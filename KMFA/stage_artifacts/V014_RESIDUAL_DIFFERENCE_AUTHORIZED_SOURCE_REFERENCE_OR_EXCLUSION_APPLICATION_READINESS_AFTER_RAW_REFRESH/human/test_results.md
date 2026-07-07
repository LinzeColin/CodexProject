# Test Results

- RED: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_v014_residual_difference_authorized_source_reference_or_exclusion_application_readiness_after_raw_refresh.py` failed before implementation because the generator module did not exist.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_readiness_after_raw_refresh.py --generated-at 2026-07-08T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_readiness_after_raw_refresh.py --require-private-readiness`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_v014_residual_difference_authorized_source_reference_or_exclusion_application_readiness_after_raw_refresh.py`
- Governance validators, CSV shape checks, diff check and phase validator: PASS before local commit.
- Raw/private scan, secret scan and private-runtime tracked-file scan: PASS before local commit.

Expected matrix result: 15/15 PASS.
