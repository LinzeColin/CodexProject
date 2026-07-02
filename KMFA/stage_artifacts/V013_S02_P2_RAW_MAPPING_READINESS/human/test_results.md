# KMFA v0.1.3 S02-P2 Test Results

## Scope

- Phase: `S02-P2`
- Task: `KMFA-V013-S02-P2-RAW-MAPPING-READINESS-20260702`
- Raw directory: `/Users/linzezhang/Downloads/KMFA_MetaData`
- Raw directory policy: read-only; no modify, delete, move, or GitHub commit.

## Results

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v013_s02_p2_raw_mapping_readiness.py`
  - PASS: evidence generated with `raw_files=5`, `zip_openable=3`, `workbooks_parseable=25`, `private_ignored=true`, `github_upload=false`.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s02_p2_raw_mapping_readiness.py`
  - PASS: raw mapping readiness validated with `raw_files=5`, `workbooks_parseable=25`, `raw_value_matching_status=blocked_authorized_mapping_required`, `github_upload=false`.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v013_s02_p2_raw_mapping_readiness -q`
  - PASS: 1 test OK.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest discover -s KMFA/tests -q`
  - PASS: 285 tests OK.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA`
  - PASS: errors 0, warnings 0.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA`
  - PASS: errors 0, warnings 0.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --enforce-sync`
  - PASS after adding the S02-P2 development event: errors 0, warnings 0.
- Structured parse checks for changed JSON/YAML/JSONL files
  - PASS.
- Tracked raw/private artifact scan
  - PASS: no tracked `.zip`, `.xlsx`, `.xls`, `.pdf`, `.sqlite`, `.db`, or `.codex_private_runtime/` files.
- High-signal secret scan
  - PASS with strict key-shaped regex.
- `git diff --check -- KMFA scripts`
  - PASS.

## Non-Scope Confirmed

- Raw row-value extraction was not performed in S02-P2.
- Raw value matching was not performed; status is `blocked_authorized_mapping_required`.
- S02-P3 data quality/error gate was not performed.
- Stage 2 review was not performed.
- GitHub upload was not performed.
- Formal report release, lineage full check, live connector, OpMe deep coupling, and business execution were not performed.
