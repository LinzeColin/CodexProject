# KMFA v0.1.4 S05-P3 Test Results

- status: `passed_final_validation_local_only_no_go_upload_deferred`
- task_id: `KMFA-V014-S05-P3-AUTHORITY-BASELINE-LOCK-20260704`
- authority_record_count: `45`
- q5_calculation_baseline_locked_count: `40`
- excluded_cross_source_support_only_count: `5`
- github_upload_performed: `false`

## Commands

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_s05_p3_authority_baseline_lock.py KMFA/tools/check_v014_s05_p3_authority_baseline_lock.py KMFA/tests/test_v014_s05_p3_authority_baseline_lock.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_s05_p3_authority_baseline_lock.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s05_p2_field_golden_baseline.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s05_p3_authority_baseline_lock.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s05_p3_authority_baseline_lock -q`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/no_omission_check.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_no_float_money.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --enforce-sync`
- `structured JSON/JSONL/CSV parse check`
- `Ruby YAML parse check`
- `changed/untracked raw-private artifact path scan`
- `changed/untracked high-signal secret scan`
- `public S05-P3 exact forbidden key scan`
- `public S05-P3 high-signal text leak scan`
- `git diff --check -- KMFA scripts`

## Results

- PASS: S05-P3 generator, S05-P2 dependency validator, S05-P3 validator and focused unit test passed.
- PASS: no-omission, no-float, project governance, lean governance and governance sync passed with zero errors and zero warnings.
- PASS: structured JSON/JSONL/CSV parse, Ruby YAML parse and diff whitespace check passed.
- PASS: changed/untracked raw-private artifact path scan and high-signal secret scan passed.
- PASS: public S05-P3 exact forbidden key scan and high-signal text leak scan passed.
- PASS: raw inbox read/list/stat/hash/mutation, Stage 5 review, GitHub upload, raw value matching, zero-delta validation, lineage full check, formal report, live connector, OpMe deep coupling and business execution were not performed.
