# KMFA v0.1.4 S03-P1 Test Results

Status: `PASS_LOCAL_ONLY`

Validation commands:

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_s03_p1_raw_file_registration.py KMFA/tools/check_v014_s03_p1_file_registration.py KMFA/tests/test_v014_s03_p1_file_registration.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_s03_p1_raw_file_registration.py --write`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s02_stage_review.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s03_p1_file_registration.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s03_p1_file_registration -q`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/no_omission_check.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_no_float_money.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --enforce-sync`
- structured changed-file parse check
- changed/untracked raw-private artifact path scan
- strict key-shaped secret scan
- `git diff --check -- KMFA`

Results:

- PASS: py_compile, S02 Stage review dependency validator, S03-P1 validator and focused unit test passed.
- PASS: no-omission, no-float, project governance, lean governance and governance sync validators passed.
- PASS: structured JSON/JSONL/CSV parse, Ruby YAML parse, changed/untracked raw-private path scan, public raw leak scan, strict key-shaped secret scan and `git diff --check -- KMFA` passed.
- PASS: raw root read-only registration produced file_count=5, supported_file_count=5 and total_size_bytes=62788056.

Boundary result:

- PASS: `/Users/linzezhang/Downloads/KMFA_MetaData` was used only for this phase authorized read-only list/stat/read/hash.
- PASS: `/Users/linzezhang/Downloads/KMFA_MetaData` was not written, deleted, moved, renamed, overwritten or converted.
- PASS: raw details remained in git-ignored private runtime; public artifacts contain only aggregate counts, type/size/status and private refs.
- PASS: S03-P2, S03-P3, Stage 3 review, GitHub upload, raw value matching, field mapping, formal report, live connector and business execution were not performed.
