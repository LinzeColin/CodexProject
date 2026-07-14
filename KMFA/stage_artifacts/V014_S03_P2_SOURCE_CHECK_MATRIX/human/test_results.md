# KMFA v0.1.4 S03-P2 Test Results

Status: `PASS_FINAL_VALIDATION_LOCAL_ONLY_NO_GO_UPLOAD_DEFERRED`

Validation commands:

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_s03_p2_source_check_matrix.py KMFA/tools/check_v014_s03_p2_source_check_matrix.py KMFA/tests/test_v014_s03_p2_source_check_matrix.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_s03_p2_source_check_matrix.py --write`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s03_p1_file_registration.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s03_p2_source_check_matrix.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s03_p2_source_check_matrix -q`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_source_check_matrix -q`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/no_omission_check.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_no_float_money.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --enforce-sync`
- structured JSON/JSONL/CSV parse check
- Ruby YAML parse check
- changed/untracked raw-private path scan
- S03-P1 private manifest based public raw leak scan
- strict high-signal secret scan
- `git diff --check -- KMFA`

Results:

- PASS: generator built matrix rows `5`, status events `5`, allowed statuses `5`, `raw_read=false`, `github_upload=false`.
- PASS: S03-P1 dependency validator passed with files `5`, supported `5`, unsupported `0`.
- PASS: S03-P2 validator passed with rows `5`, events `5`, statuses `5`, next `S03-P3`.
- PASS: focused S03-P2 unit tests passed, `2` tests OK.
- PASS: existing source_check_matrix unit tests passed, `4` tests OK.
- PASS: no-omission passed with requirements `20`, P0 `9`, P1 `8`, status_records `587`, v1.2_html `45+`.
- PASS: no-float money scan passed.
- PASS: project governance validator, lean governance validator and governance sync validator passed with `0` errors and `0` warnings.
- PASS: structured JSON/JSONL/CSV and YAML parse checks passed.
- PASS: raw/private path scan, public raw leak scan and high-signal secret scan passed.
- PASS: `git diff --check -- KMFA` passed.

Boundary result:

- PASS: S03-P2 used S03-P1 public register only and did not read raw root.
- PASS: raw root was not written, deleted, moved, renamed, overwritten or converted.
- PASS: matrix/status event public outputs contain no raw file names, raw hashes, field/header plaintext, row values or business values.
- PASS: S03-P3, Stage 3 review, GitHub upload, raw value matching, field mapping, formal report, live connector and business execution were not performed.
