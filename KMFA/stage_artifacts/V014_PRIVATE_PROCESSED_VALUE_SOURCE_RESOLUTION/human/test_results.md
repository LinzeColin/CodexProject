# Test Results

- phase: `V014_PRIVATE_PROCESSED_VALUE_SOURCE_RESOLUTION`
- status: `PASS_LOCAL_VALIDATION_NO_GO_SOURCE_MAP_MISSING`
- red_test_recorded: `true`
- red_test_failure: `ModuleNotFoundError: No module named 'KMFA.tools.check_v014_private_processed_value_source_resolution'`
- py_compile: `PASS`
- generator: `PASS`
- validator: `PASS`
- focused_unit_test: `PASS`
- project_governance_required: `PASS`
- lean_governance: `PASS`
- governance_sync_changed_only: `PASS`
- no_float_money_scan: `PASS`
- no_omission_check: `PASS`
- diff_whitespace_check: `PASS`
- public_artifact_boundary_scan: `PASS`
- raw_private_suffix_scan: `PASS`
- high_signal_secret_scan: `PASS`
- private_runtime_git_boundary_scan: `PASS`
- raw_inbox_access_performed: `false`
- raw_inbox_mutation_performed: `false`
- raw_private_source_folder_mutation_performed: `false`
- raw_to_processed_value_comparison_performed: `false`
- business_value_consistency_verified: `false`
- difference_report_required_now: `false`
- github_upload_performed: `false`
- local_commit_required: `true`

## Commands Completed

- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m py_compile KMFA/tools/v014_private_processed_value_source_resolution.py KMFA/tools/check_v014_private_processed_value_source_resolution.py KMFA/tests/test_v014_private_processed_value_source_resolution.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_private_processed_value_source_resolution.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_private_processed_value_source_resolution.py --require-private-source-resolution`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_private_processed_value_source_resolution -q`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_project_governance.py --project KMFA --mode required`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/lean_governance.py validate --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_governance_sync.py --changed-only --enforce-sync`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_no_float_money.py KMFA/tools KMFA/tests`
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/no_omission_check.py`
- `git diff --check -- KMFA scripts`
- `changed/untracked JSON JSONL CSV YAML structured parse checks`
- `scoped current-phase public artifact boundary scan`
- `changed/untracked raw/private suffix scan`
- `high-signal secret scan across changed/untracked KMFA text files`
- `private runtime tracked/untracked/ignore scan`

## Result

The phase validated that 149 processed target slots still have no usable private processed value source map, so source resolution remains incomplete and the Go/No-Go decision is `NO_GO`. No raw-to-processed value comparison was performed and no business-value consistency claim is made.

The raw/private source folder was not accessed or mutated by this phase. If a later value-comparison phase repeatedly cannot reconcile processed outputs with raw-source evidence after source-map capture and cross-validation, the final goal closeout must include a public-safe difference report.

## Non-Blocking Legacy Observations

- A broader semantic governance sync run still reports legacy planned/test reference placeholders in pre-existing model registry entries. That finding is outside this one-phase acceptance gate and was not changed here.
- A broader information-quality run still reports historical long-line and metadata quality issues. That finding is outside this one-phase acceptance gate and was not changed here.
