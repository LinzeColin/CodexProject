# KMFA v0.1.3 S08-P1 Project Composite Key Replay Test Results

- task_id: `KMFA-V013-S08-P1-PROJECT-COMPOSITE-KEY-REPLAY-20260703`
- status: `passed_final_validation_local_only_upload_deferred_no_go`
- github_upload_performed: `false`
- raw_dir_read_performed_by_this_phase: `false`
- raw_dir_mutation_performed: `false`
- s08_p2_performed: `false`
- s08_p3_performed: `false`
- stage8_review_performed: `false`
- raw_value_matching_performed: `false`
- formal_report_allowed: `false`
- business_execution_allowed: `false`

## Command Results

- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m py_compile KMFA/tools/v013_s08_p1_project_composite_key_replay.py KMFA/tools/check_v013_s08_p1_project_composite_key_replay.py KMFA/tests/test_v013_s08_p1_project_composite_key_replay.py`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v013_s08_p1_project_composite_key_replay.py`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s08_p1_project_composite_key_replay.py`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v013_s08_p1_project_composite_key_replay -q`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s08_p1_project_composite_key.py`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_project_composite_key -q`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s07_stage_review.py`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest discover -s KMFA/tests -q` ran 313 tests in 717.302s.
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_no_float_money.py`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/no_omission_check.py`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --enforce-sync`
- PASS: parameter registry shape and S08-P1 rows validated for `PARAM-KMFA-903` through `PARAM-KMFA-910`.
- PASS: structured JSON/JSONL/CSV parse check.
- PASS: structured YAML parse check via Ruby stdlib because system Python has no PyYAML.
- PASS: changed/untracked raw/private artifact path scan.
- PASS: S08-P1 public-safe evidence scan.
- PASS: changed/untracked high-signal secret scan.
- PASS: `git diff --check -- KMFA`
- FIXED: `check_no_float_money.py` initially flagged a non-money Python float literal in `derived_percent`; the generator now records `derived_percent_bps=3333` and `derived_percent_label="33.33%"`, then no-float passed.
- NOT PERFORMED: S08-P2, S08-P3, Stage 8 review, GitHub upload, raw value matching, lineage full check, formal report, live connector, Redcircle automatic connector, or business execution.
- RAW BOUNDARY: this phase did not read, list, modify, delete, move, rename, overwrite, or write `/Users/linzezhang/Downloads/KMFA_MetaData`.
