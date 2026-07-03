# KMFA v0.1.4 S07-P1 Finance File Adapter Test Results

- status: `passed_final_validation_local_only_no_go_upload_deferred`
- task_id: `KMFA-V014-S07-P1-FINANCE-FILE-ADAPTER-20260704`
- acceptance_id: `ACC-V014-S07-P1-FINANCE-FILE-ADAPTER`
- generator: `PASS`
- s06_stage_review_dependency: `PASS`
- legacy_finance_adapter: `PASS`
- source_category_count: `9`
- source_registry_count: `9`
- field_candidate_count: `45`
- hash_only_field_candidate_count: `45`
- readonly_field_report_count: `9`
- source_header_fingerprint_count: `45`
- q4_human_confirmed_count: `0`
- q5_allowed_count: `0`
- formal_report_allowed_count: `0`
- s07_p2_performed: `false`
- s07_p3_performed: `false`
- stage7_review_performed: `false`
- github_upload_performed: `false`
- raw_inbox_read_performed: `false`
- raw_inbox_mutation_performed: `false`

## Commands

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_s07_p1_finance_file_adapter.py KMFA/tools/check_v014_s07_p1_finance_file_adapter.py KMFA/tests/test_v014_s07_p1_finance_file_adapter.py` -> PASS
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_s07_p1_finance_file_adapter.py` -> PASS
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s07_p1_finance_file_adapter.py` -> PASS
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_finance_file_adapter -q` -> PASS, 2 tests
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s07_p1_finance_file_adapter.py` -> PASS
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s07_p1_finance_file_adapter -q` -> PASS, 1 test
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/no_omission_check.py` -> PASS
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_no_float_money.py` -> PASS
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_project_governance.py --project KMFA` -> PASS
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/lean_governance.py validate --project KMFA` -> PASS
- `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_governance_sync.py --changed-only --enforce-sync` -> PASS
- structured JSON/JSONL/CSV parse check -> PASS
- Ruby YAML parse check -> PASS
- changed-path raw/private artifact scan -> PASS
- changed-file high-signal secret scan -> PASS
- S07-P1 public-safe semantic scan -> PASS after removing a forbidden boundary-key token from public evidence
- `git diff --check -- KMFA scripts` -> PASS

## Boundary

S07-P1 remains local-only and upload-deferred. This phase did not read/list/stat/hash/mutate the raw inbox, did not start S07-P2 or S07-P3, did not run Stage 7 review, did not upload to GitHub, did not run raw content matching, did not run lineage full check, did not create a formal report, did not call a live connector, and did not perform business execution.
