# Test Results

- RED: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_v014_residual_difference_authorized_source_reference_or_exclusion_application_blocker_audit_after_raw_refresh.py` failed before implementation because the generator module did not exist.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_blocker_audit_after_raw_refresh.py --generated-at 2026-07-08T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_blocker_audit_after_raw_refresh.py --require-private-audit`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_v014_residual_difference_authorized_source_reference_or_exclusion_application_blocker_audit_after_raw_refresh.py`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_residual_difference_authorized_source_reference_or_exclusion_application_blocker_audit_after_raw_refresh.py --generated-at 2026-07-08T00:00:00+10:00`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_authorized_source_reference_or_exclusion_application_blocker_audit_after_raw_refresh.py --require-private-audit`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_v014_residual_difference_authorized_source_reference_or_exclusion_application_blocker_audit_after_raw_refresh.py` ran 5 tests.
- PASS: py_compile passed for generator, validator and focused unit test.
- PASS: project governance validator, lean governance validator and changed-only governance sync validator passed with errors=0.
- PASS: CSV shape checks, diff check, raw/private filename scan, added-line secret scan and private-runtime tracked-file scan passed before local commit.

Expected matrix result: 15/15 PASS.
