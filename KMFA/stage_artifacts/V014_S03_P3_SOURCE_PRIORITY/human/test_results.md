# KMFA v0.1.4 S03-P3 Test Results

Status: `PASS_FINAL_VALIDATION_LOCAL_ONLY_NO_GO_UPLOAD_DEFERRED`

Validation commands:

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_s03_p3_source_priority.py KMFA/tools/check_v014_s03_p3_source_priority.py KMFA/tests/test_v014_s03_p3_source_priority.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_s03_p3_source_priority.py --write`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s03_p2_source_check_matrix.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s03_p3_source_priority.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s03_p3_source_priority -q`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_source_priority -q`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/no_omission_check.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_no_float_money.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --enforce-sync`
- `structured JSON/JSONL/CSV parse check`
- `Ruby YAML parse check`
- `changed/untracked raw/private artifact path scan`
- `public raw leak scan`
- `changed/untracked high-signal secret scan`
- `git diff --check -- KMFA scripts`

Results:

- PASS: S03-P3 generator built records=5, priority_order=9, same_source_events=1, difference_queue=1, raw_read=false, github_upload=false.
- PASS: S03-P2 dependency validator and S03-P3 validator passed.
- PASS: focused S03-P3 unit tests passed: `Ran 3 tests`.
- PASS: existing source priority unit tests passed: `Ran 4 tests`.
- PASS: no-omission and no-float validators passed.
- PASS: project governance, lean governance and governance sync validators passed.
- PASS: structured JSON/JSONL/CSV parse and Ruby YAML parse checks passed.
- PASS: changed/untracked raw/private artifact path scan, public raw leak scan, high-signal secret scan and diff check passed.

Boundary result:

- PASS: S03-P3 uses S03-P2 public matrix/status events only and does not read raw root.
- PASS: same-source inconsistency policy invalidates derived cache and requests rerun.
- PASS: cross-source conflict policy enters a manual difference queue and does not auto-select.
- PASS: Stage 3 review, GitHub upload, raw value matching, field mapping, formal report, live connector and business execution were not performed.
