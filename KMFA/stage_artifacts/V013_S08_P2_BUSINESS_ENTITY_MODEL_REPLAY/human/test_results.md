# KMFA v0.1.3 S08-P2 Business Entity Model Replay Test Results

- task_id: `KMFA-V013-S08-P2-BUSINESS-ENTITY-MODEL-REPLAY-20260703`
- status: `final_validation_passed_local_only_no_go_upload_deferred`
- github_upload_performed: `false`
- raw_dir_read_performed_by_this_phase: `false`
- raw_dir_mutation_performed: `false`
- s08_p1_dependency_validated: `true`
- s08_p2_performed: `true`
- s08_p3_performed: `false`
- stage8_review_performed: `false`
- fact_layer_scope_included: `false`
- raw_value_matching_performed: `false`
- formal_report_allowed: `false`
- business_execution_allowed: `false`

## Command Results

- PASS: `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v013_s08_p2_business_entity_model_replay.py KMFA/tools/check_v013_s08_p2_business_entity_model_replay.py KMFA/tests/test_v013_s08_p2_business_entity_model_replay.py`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v013_s08_p2_business_entity_model_replay.py`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s08_p2_business_entity_model_replay.py`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v013_s08_p2_business_entity_model_replay -q`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s08_p2_business_entity_model.py`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_business_entity_model -q`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s08_p1_project_composite_key_replay.py`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest discover -s KMFA/tests -q` ran 314 tests in 659.725s.
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_no_float_money.py`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/no_omission_check.py`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --enforce-sync`
- PASS: structured JSON/JSONL/CSV parse check.
- PASS: structured YAML parse check.
- PASS: changed/untracked raw/private artifact path scan.
- PASS: S08-P2 public-safe evidence scan.
- PASS: changed/untracked high-signal secret scan.
- PASS: `git diff --check -- KMFA`
- PASS: S08-P3, Stage 8 review, GitHub upload, raw value matching, lineage full check, formal report, live connector, Redcircle automatic connector and business execution were not performed.
