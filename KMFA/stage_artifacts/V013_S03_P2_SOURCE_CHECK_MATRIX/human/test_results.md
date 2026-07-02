# KMFA v0.1.3 S03-P2 Test Results

- status: `final_local_validation_passed`

## RED

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v013_s03_p2_source_check_matrix -q`
- result: `FAILED as expected before implementation`
- failure: `ModuleNotFoundError: No module named 'KMFA.tools.check_v013_s03_p2_source_check_matrix'`

## GREEN

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v013_s03_p2_source_check_matrix.py`
- result: `PASS: dimensions=6, statuses=5, metadata_event=true, raw_read=false, github_upload=false`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s03_p2_source_check_matrix.py`
- result: `PASS: dimensions=6, statuses=5, metadata_event=true, raw_read=false, github_upload=false`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v013_s03_p2_source_check_matrix -q`
- result: `PASS: 1 test`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_source_check_matrix -q`
- result: `PASS: 4 tests`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s03_p1_file_import_register.py`
- result: `PASS: S03-P1 dependency`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest discover -s KMFA/tests -q`
- result: `PASS: 289 tests`

## Governance And Safety

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA`
- result: `PASS: errors=0 warnings=0`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA`
- result: `PASS: errors=0 warnings=0`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --enforce-sync`
- result: `PASS: errors=0 warnings=0`
- `parameter_registry.csv` / `TRACEABILITY_MATRIX.csv` shape check
- result: `PASS`
- `development_events.jsonl` parse check
- result: `PASS`
- YAML parse check for `VERSION_MATRIX.yaml`, `ASSURANCE_STATUS.yaml`, `delivery_tasks.yaml`
- result: `PASS`
- changed and untracked raw/private artifact scan
- result: `PASS: forbidden_raw_private_artifacts=0`
- changed and untracked high-signal secret scan
- result: `PASS: high_signal_secret_findings=0`
- `git diff --check -- KMFA scripts`
- result: `PASS`

## Boundary

- raw_dir_read_performed: `false`
- raw_dir_mutation_performed: `false`
- raw_layer_write_allowed: `false`
- raw_source_mutation_allowed: `false`
- github_upload_performed: `false`
- stage3_review_performed: `false`
