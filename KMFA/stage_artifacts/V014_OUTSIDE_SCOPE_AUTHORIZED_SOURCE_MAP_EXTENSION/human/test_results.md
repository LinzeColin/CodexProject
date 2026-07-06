# Test Results

Planned commands:

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_outside_scope_authorized_source_map_extension.py KMFA/tools/check_v014_outside_scope_authorized_source_map_extension.py KMFA/tests/test_v014_outside_scope_authorized_source_map_extension.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_outside_scope_authorized_source_map_extension.py --generated-at 2026-07-06T00:00:00+10:00`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_outside_scope_authorized_source_map_extension.py --require-private-template`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_outside_scope_authorized_source_map_extension`

Current generated check matrix: `8` pass / `0` fail. This phase does not read, list, parse, copy, move, rename, delete, overwrite, normalize or mutate the raw inbox.
