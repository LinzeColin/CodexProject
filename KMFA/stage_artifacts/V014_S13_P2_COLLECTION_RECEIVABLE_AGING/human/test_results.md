# KMFA v0.1.4 S13-P2 Test Results

- task_id: `KMFA-V014-S13-P2-COLLECTION-RECEIVABLE-AGING-20260705`
- status: `passed_local_validation_pre_commit`

## Expected Commands

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_s13_p2_collection_receivable_aging.py KMFA/tools/check_v014_s13_p2_collection_receivable_aging.py KMFA/tests/test_v014_s13_p2_collection_receivable_aging.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_s13_p2_collection_receivable_aging.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s13_p2_collection_receivable_aging.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s13_p2_collection_receivable_aging -q`
- governance validators and safety scans before commit

## Captured Results

- PASS: `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_s13_p2_collection_receivable_aging.py KMFA/tools/check_v014_s13_p2_collection_receivable_aging.py KMFA/tests/test_v014_s13_p2_collection_receivable_aging.py`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_s13_p2_collection_receivable_aging.py`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s13_p2_collection_receivable_aging.py`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s13_p2_collection_receivable_aging -q` ran 1 test in 457.862s.
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --enforce-sync`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_no_float_money.py`
- PASS: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/no_omission_check.py`
- PASS: changed/untracked JSON, JSONL and CSV structured parse checks.
- PASS: changed/untracked Ruby YAML parse checks.
- PASS: changed/untracked forbidden raw/private suffix scan.
- PASS: changed/untracked high-signal secret scan.
- PASS: scoped S13-P2 public artifact boundary scan.
- PASS: `git diff --check -- KMFA scripts`
- PASS: raw/private inbox read/list/stat/hash/mutation, S13-P3, Stage 13 review, GitHub upload, protected source matching, lineage full check, formal report release, legal collection, payment, invoice, tax, live connector, app reinstall, OpMe integration and business execution were not performed.
