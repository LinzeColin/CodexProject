# KMFA v0.1.3 S02-P1 Test Results

## Scope

- Phase: `S02-P1`
- Task: `KMFA-V013-S02-P1-RAW-READINESS-20260702`
- Raw directory: `/Users/linzezhang/Downloads/KMFA_MetaData`
- Raw directory policy: read-only; no modify, delete, move, or GitHub commit.

## Results

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v013_s02_p1_raw_readiness.py`
  - PASS: evidence generated with `files=5`, `raw_dir_readable=true`, `private_ignored=true`, `github_upload=false`.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s02_p1_raw_readiness.py`
  - PASS: raw readiness validated with `files=5`, `private_ignored=true`, `raw_value_matching=false`, `github_upload=false`.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v013_s02_p1_raw_readiness -q`
  - PASS: 1 test OK.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest discover -s KMFA/tests -q`
  - PASS: 284 tests OK.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA`
  - PASS: errors 0, warnings 0.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA`
  - PASS: errors 0, warnings 0.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --enforce-sync`
  - PASS after adding the S02-P1 development event: errors 0, warnings 0.
- Structured parse checks for changed JSON/YAML/JSONL files
  - PASS.
- Tracked raw/private artifact scan
  - PASS: no tracked `.zip`, `.xlsx`, `.xls`, `.pdf`, `.sqlite`, `.db`, or `.codex_private_runtime/` files.
- High-signal secret scan
  - PASS with strict key-shaped regex. An initial broad substring scan for `sk-` produced historical false positives in synthetic policy/test text and was replaced by the stricter high-signal scan.
- `git diff --check -- KMFA scripts`
  - PASS.

## Non-Scope Confirmed

- Raw value matching was not performed in S02-P1.
- Stage 2 review was not performed.
- GitHub upload was not performed.
- Formal report release, lineage full check, live connector, OpMe deep coupling, and business execution were not performed.
