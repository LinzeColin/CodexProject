# KMFA v0.1.3 S04-P1 Test Results

- status: `passed_local_only`

## RED

- command: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v013_s04_p1_amount_precision -q`
- result: `FAIL_EXPECTED`
- evidence: `ModuleNotFoundError: No module named 'KMFA.tools.check_v013_s04_p1_amount_precision'`

## GREEN

- command: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v013_s04_p1_amount_precision.py`
- result: `PASS`
- output: `amount_cases=9`, `rejections=9`, `no_float=true`, `raw_read=false`, `github_upload=false`

- command: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s04_p1_amount_precision.py`
- result: `PASS`
- output: `amount_cases=9`, `rejections=9`, `no_float=true`, `raw_read=false`, `github_upload=false`

- command: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v013_s04_p1_amount_precision -q`
- result: `PASS`
- output: `Ran 1 test`

## FINAL VALIDATION

- command: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_amount_tools -q`
- result: `PASS`
- output: `Ran 6 tests`

- command: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_no_float_money.py`
- result: `PASS`
- output: `no KMFA Python float money usage found`

- command: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v013_s03_stage_review.py`
- result: `PASS`
- output: `phases=3`, `findings_open=0`, `quality=Q2`, `report=D`, `release=blocked`, `github_upload=false`

- command: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest discover -s KMFA/tests -q`
- result: `PASS_AFTER_FIX`
- output: `Ran 293 tests`
- finding_fixed: `no_omission baseline validator was made append-safe so v0.1.3 replay status records do not inflate the v1.2 54-phase baseline count`

- command: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA`
- result: `PASS`
- output: `errors=0`, `warnings=0`

- command: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA`
- result: `PASS`
- output: `errors=0`, `warnings=0`

- command: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --enforce-sync`
- result: `PASS_AFTER_EVENT_BINDING`
- output: `errors=0`, `warnings=0`

- command: `structured YAML/JSON/CSV/JSONL parse checks`
- result: `PASS`

- command: `changed and untracked public-safe raw/private artifact scan`
- result: `PASS`

- command: `changed and untracked high-signal secret scan`
- result: `PASS`

- command: `git diff --check -- KMFA scripts`
- result: `PASS`

## Boundaries

- raw_dir_read_performed: `false`
- raw_dir_mutation_performed: `false`
- raw_value_matching_performed: `false`
- stage4_review_performed: `false`
- github_upload_performed: `false`
- formal_report_allowed: `false`
- business_execution_allowed: `false`
