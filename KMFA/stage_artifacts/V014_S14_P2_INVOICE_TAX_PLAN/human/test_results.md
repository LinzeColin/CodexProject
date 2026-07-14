# KMFA v0.1.4 S14-P2 Test Results

- task_id: `KMFA-V014-S14-P2-INVOICE-TAX-PLAN-20260705`
- status: `passed_local_validation`

## Commands

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_s14_p2_invoice_tax_plan.py KMFA/tools/check_v014_s14_p2_invoice_tax_plan.py KMFA/tests/test_v014_s14_p2_invoice_tax_plan.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/v014_s14_p2_invoice_tax_plan.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s14_p2_invoice_tax_plan.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_s14_p2_invoice_tax_plan.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_s14_p2_invoice_tax_plan -q`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_project_governance.py --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/lean_governance.py validate --project KMFA`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 scripts/validate_governance_sync.py --changed-only --enforce-sync`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_no_float_money.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/no_omission_check.py`
- `git diff --check -- KMFA scripts`
- structured JSON/JSONL/CSV parse for changed-or-untracked paths
- YAML parse for changed YAML governance files
- changed-path raw/private suffix scan
- high-signal secret scan
- S14-P2 public artifact boundary scan

## Result

- py_compile: `PASS`
- generator: `PASS`
- legacy S14-P2 validator: `PASS`
- v0.1.4 S14-P2 validator: `PASS`
- focused unit test: `PASS`
- governance validators: `PASS`
- no-float money scan: `PASS`
- no-omission check: `PASS`
- parse checks: `PASS`
- diff check: `PASS`
- raw/private and secret scans: `PASS`
- public artifact boundary scan: `PASS`
