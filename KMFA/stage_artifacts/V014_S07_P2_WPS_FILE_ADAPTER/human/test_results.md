# KMFA v0.1.4 S07-P2 WPS File Adapter Test Results

- status: `passed_final_validation_local_only_no_go_upload_deferred`
- task_id: `KMFA-V014-S07-P2-WPS-FILE-ADAPTER-20260704`
- acceptance_id: `ACC-V014-S07-P2-WPS-FILE-ADAPTER`
- generator: `PASS`
- s06_stage_review_dependency: `PASS`
- s07_p1_dependency: `PASS`
- legacy_wps_adapter: `PASS`
- legacy_wps_adapter_unit: `PASS`
- s07_p2_validator: `PASS`
- focused_unit_test: `PASS`
- governance_validators: `PASS`
- structured_parse: `PASS`
- ruby_yaml_parse: `PASS`
- raw_private_scan: `PASS`
- high_signal_secret_scan: `PASS`
- public_semantic_scan: `PASS`
- diff_check: `PASS`
- s07_p3_performed: `false`
- stage7_review_performed: `false`
- github_upload_performed: `false`
- raw_inbox_read_performed: `false`
- raw_inbox_listed_performed: `false`
- raw_inbox_stat_performed: `false`
- raw_inbox_hash_performed: `false`
- raw_inbox_mutation_performed: `false`
- raw_content_matching_performed: `false`
- formal_report_allowed: `false`
- business_execution_allowed: `false`

## Commands

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_s07_p2_wps_file_adapter.py KMFA/tools/check_v014_s07_p2_wps_file_adapter.py KMFA/tests/test_v014_s07_p2_wps_file_adapter.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_s07_p2_wps_file_adapter.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s07_p2_wps_file_adapter.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s07_p2_wps_file_adapter.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_wps_file_adapter -q`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s07_p2_wps_file_adapter -q`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/no_omission_check.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_no_float_money.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_project_governance.py --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/lean_governance.py validate --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_governance_sync.py --changed-only --enforce-sync`
- `structured JSON JSONL CSV parse check`
- `Ruby YAML parse check`
- `changed-path raw/private artifact scan`
- `changed-file high-signal secret scan`
- `S07-P2 public-safe semantic scan`
- `git diff --check -- KMFA scripts`

## Results

- `PASS`: generator returned `exports=4`, `field_mappings=20`, `conversion_guidance=4`, `q5_allowed=0`, `stage7_review=false`, `github_upload=false`.
- `PASS`: S07-P2 validator returned `exports=4`, `field_mappings=20`, `conversion_guidance=4`, `q5_allowed=0`, `stage7_review=false`, `github_upload=false`.
- `PASS`: legacy WPS validator returned `exports=4`, `field_mappings=20`, `conversion_guidance=4`, `rule_versions=1`, `source_header_hashes=20`, `finance_scope=false`, `redcircle_scope=false`, `formal_report_allowed=false`.
- `PASS`: legacy WPS unit test ran 3 tests in 0.006s and returned OK.
- `PASS`: focused v0.1.4 S07-P2 unit test ran 1 test in 540.926s and returned OK after the public-safe conversion guidance fix.
- `PASS`: no-omission, no-float, project governance, lean governance and governance sync validators passed.
- `PASS`: structured parse, Ruby YAML parse and diff check passed.
- `PASS`: changed-path raw/private scan, high-signal secret scan and S07-P2 public-safe semantic scan passed.
- `PASS`: raw inbox read/list/stat/hash/mutation, S07-P3, Stage 7 review, GitHub upload, raw value matching, lineage full check, formal report, live connector, OpMe deep coupling and business execution were not performed.
