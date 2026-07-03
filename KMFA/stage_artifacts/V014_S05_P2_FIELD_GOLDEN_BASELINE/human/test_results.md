# KMFA v0.1.4 S05-P2 Test Results

- status: `passed_final_validation_local_only_no_go_upload_deferred`
- task_id: `KMFA-V014-S05-P2-FIELD-GOLDEN-BASELINE-20260704`
- field_candidate_count: `45`
- field_contract_count: `5`
- pdf_field_candidate_count: `40`
- excel_field_candidate_count: `5`
- source_anchor_recorded_private_only_count: `40`
- owner_downgraded_excel_field_count: `5`
- q4_human_confirmed_count: `0`
- q5_calculation_baseline_allowed_count: `0`
- raw_inbox_read_by_this_phase: `false`
- github_upload_performed: `false`

## Commands

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_s05_p2_field_golden_baseline.py KMFA/tools/check_v014_s05_p2_field_golden_baseline.py KMFA/tests/test_v014_s05_p2_field_golden_baseline.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_s05_p2_field_golden_baseline.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s05_p1_a0_file_registration.py --require-private-diagnostic`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s05_p2_field_golden_baseline.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s05_p2_field_golden_baseline -q`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/no_omission_check.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_no_float_money.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --enforce-sync`
- structured JSON/JSONL/CSV parse check
- Ruby YAML parse check
- changed/untracked raw-private path scan
- high-signal secret scan
- public S05-P2 raw value/sheet/member leak token scan
- `git diff --check -- KMFA scripts`

## Results

- PASS: S05-P2 generator, S05-P1 dependency validator, S05-P2 validator and focused unit test passed.
- PASS: no-omission, no-float, project governance, lean governance, governance sync, structured parse, Ruby YAML parse and diff check passed.
- PASS: changed/untracked raw-private path scan, high-signal secret scan and public S05-P2 raw value/sheet/member leak token scan passed.
- PASS: raw inbox read/list/stat/hash/mutation, S05-P3, Stage 5 review, GitHub upload, raw value matching, lineage full check, formal report, live connector, OpMe deep coupling and business execution were not performed.
