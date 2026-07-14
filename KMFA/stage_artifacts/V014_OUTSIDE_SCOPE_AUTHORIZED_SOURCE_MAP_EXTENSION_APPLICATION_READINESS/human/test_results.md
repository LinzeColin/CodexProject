# Test Results

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_outside_scope_authorized_source_map_extension_application_readiness.py KMFA/tools/check_v014_outside_scope_authorized_source_map_extension_application_readiness.py KMFA/tests/test_v014_outside_scope_authorized_source_map_extension_application_readiness.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_outside_scope_authorized_source_map_extension_application_readiness.py --generated-at 2026-07-07T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_outside_scope_authorized_source_map_extension_application_readiness.py --require-private-readiness`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_outside_scope_authorized_source_map_extension_application_readiness`
- status: `PASS`
- result: generator PASS; validator PASS; focused unittest 5 tests OK.
