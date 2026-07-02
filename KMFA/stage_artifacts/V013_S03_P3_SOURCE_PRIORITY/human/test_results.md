# KMFA v0.1.3 S03-P3 Test Results

- status: `passed_local_only_no_go_upload_deferred`
- red_step: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v013_s03_p3_source_priority -q` failed before validator implementation with `ModuleNotFoundError: No module named 'KMFA.tools.check_v013_s03_p3_source_priority'`.
- generator: `PASS: KMFA v0.1.3 S03-P3 source priority evidence generated (priority_count=9, same_source_event=true, difference_queue=true, raw_read=false, github_upload=false)`
- validator: `PASS: KMFA v0.1.3 S03-P3 source priority validator passed (priority_count=9, same_source_event=true, difference_queue=true, raw_read=false, github_upload=false)`
- unit_test: `Ran 1 test in 1.165s - OK`
- legacy_source_priority_test: `Ran 4 tests in 0.056s - OK`
- s03_p2_dependency: `PASS: KMFA v0.1.3 S03-P2 source check matrix validator passed (dimensions=6, statuses=5, metadata_event=true, raw_read=false, github_upload=false)`
- full_kmfa_unittest: `Ran 290 tests in 8.642s - OK`
- governance_validator: `PASS: validate_project_governance.py --project KMFA errors=0 warnings=0`
- lean_governance_validator: `PASS: lean_governance.py validate --project KMFA errors=0 warnings=0`
- governance_sync_validator: `PASS: validate_governance_sync.py --changed-only --enforce-sync errors=0 warnings=0`
- structured_parse: `PASS: YAML parse checks passed; PASS: JSON/CSV/JSONL parse checks passed`
- raw_private_scan: `PASS: changed/untracked raw/private artifact scan passed (21 paths checked)`
- secret_scan: `PASS: high-signal secret scan passed`
- diff_check: `PASS: git diff --check -- KMFA scripts`
- raw_data_boundary: `/Users/linzezhang/Downloads/KMFA_MetaData` was not read, modified, deleted, moved, renamed, overwritten, or used for generated outputs in this phase.
- not_performed: `Stage 3 review`, `GitHub upload`, `raw value matching`, `formal report release`, `live connector`, `business execution`
