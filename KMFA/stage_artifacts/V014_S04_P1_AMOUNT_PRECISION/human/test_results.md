# KMFA v0.1.4 S04-P1 Test Results

- status: `PASS_FINAL_VALIDATION_LOCAL_ONLY_NO_GO_UPLOAD_DEFERRED`
- commands:
  - `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_s04_p1_amount_precision.py KMFA/tools/check_v014_s04_p1_amount_precision.py KMFA/tests/test_v014_s04_p1_amount_precision.py`
  - `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_s04_p1_amount_precision.py`
  - `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s04_p1_amount_precision.py`
  - `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s04_p1_amount_precision -q`
  - `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_amount_tools -q`
  - `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_no_float_money.py`
- result: `PASS`
- amount_case_count: `9`
- amount_rejection_count: `9`
- forbidden_float_fixture_findings: `3`
- repository_no_float_scan_passed: `true`
- raw_inbox_read_list_hash_mutation_performed: `false;false;false;false`
- github_upload_performed: `false`
- non_scope: `S04-P2/S04-P3/Stage 4 review/raw value matching/formal report/business execution not performed`
