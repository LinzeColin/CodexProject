# KMFA v0.1.4 S09-P3 Scope Reconciliation Test Results

- task_id: `KMFA-V014-S09-P3-SCOPE-RECONCILIATION-20260704`
- status: `final_validation_passed_local_only_no_go_upload_deferred`
- github_upload_performed: `false`
- raw_inbox_read_performed_by_this_phase: `false`
- raw_inbox_mutation_performed: `false`
- stage9_review_performed: `false`
- derived_metric_rerun_allowed: `false`
- formal_report_rerun_allowed: `false`
- formal_report_allowed: `false`
- business_execution_allowed: `false`

## Command Results

- PASS: `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_s09_p3_scope_reconciliation.py KMFA/tools/check_v014_s09_p3_scope_reconciliation.py KMFA/tests/test_v014_s09_p3_scope_reconciliation.py`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_s09_p3_scope_reconciliation.py`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s09_p2_margin_cash_margin.py`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s09_p3_scope_reconciliation.py`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s09_p3_scope_reconciliation_replay.py`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s09_p3_scope_reconciliation.py`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s09_p3_scope_reconciliation -q`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_project_scope_reconciliation -q`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_no_float_money.py`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --enforce-sync`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/no_omission_check.py`
- PASS: `git diff --check -- KMFA scripts`
- PASS: structured JSON/JSONL/CSV parse over changed/untracked KMFA files.
- PASS: Ruby YAML parse over changed/untracked KMFA YAML files with UTF-8 environment.
- PASS: changed/untracked raw/private suffix scan and high-signal secret scan.
- PASS: scoped S09-P3 evidence raw-path/raw-field/secret token scan.
