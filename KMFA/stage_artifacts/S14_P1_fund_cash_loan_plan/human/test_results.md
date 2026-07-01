# S14-P1 测试结果

## 初始结果

| 命令 | 结果 |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_fund_cash_loan_plan -q` | PASS: 6 tests |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/fund_cash_loan_plan.py --generated-at 2026-07-01T22:00:00+10:00` | PASS: generated S14-P1 public-safe artifacts |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s14_p1_fund_cash_loan_plan.py` | PASS: source_lanes=4, cash_pressure=4, loan_due_alerts=3, account_summaries=3, report_grade_visible=D, formal_report_allowed=false, payment_approval=false, bank_operation=false, loan_management=false, s14_p2_scope=false, s14_p3_scope=false, github_upload=false |

## Final Verification

| 命令 | 结果 |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_fund_cash_loan_plan -q` | PASS: 6 tests |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s14_p1_fund_cash_loan_plan.py` | PASS: source_lanes=4, cash_pressure=4, loan_due_alerts=3, account_summaries=3, report_grade_visible=D, formal_report_allowed=false, payment_approval=false, bank_operation=false, loan_management=false, s14_p2_scope=false, s14_p3_scope=false, github_upload=false |
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s KMFA/tests -q` | PASS: 178 tests |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/no_omission_check.py` | PASS: requirements=20, P0=9, P1=8, status_records=450, tasks=162, v1.2_html=45+ |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_required_html.py` | PASS: html=45, core=7 |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_no_float_money.py` | PASS: no KMFA Python float money usage found |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/metadata_protocol_check.py` | PASS: dirs=8, files=19, identifiers=5 |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/immutability_policy_check.py` | PASS: raw_manifest=append_only, derived_versions=append_only, control_events=no_raw_writes |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_report_grade_gate.py` | PASS: quality_grades=Q0-Q5, report_grades=A-D, release_gate=blocked_by_missing_evidence |
| `python3 scripts/lean_governance.py validate --project KMFA` | PASS: errors=0, warnings=0 |
| `python3 scripts/validate_project_governance.py --project KMFA` | PASS: errors=0, warnings=0 |
| YAML parse via Ruby | PASS: `formula_registry.yaml`, `roadmap.yaml`, `project.yaml`, `ASSURANCE_STATUS.yaml`, `VERSION_MATRIX.yaml`, `metadata/model_registry.yaml` |
| JSONL/CSV parse via Python stdlib | PASS: `events.jsonl`, `development_events.jsonl`, `stage_status.jsonl`, `parameter_registry.csv` |
| changed forbidden file type scan | PASS: no changed `.zip`, `.xlsx`, `.xls`, `.pdf`, `.sqlite` or `.db` files |
| S14-P1 public output forbidden text scan | PASS: no raw/private text markers in S14-P1 public outputs |
| high-signal secret scan on changed KMFA files | PASS: no credential patterns found |
| `git diff --check -- KMFA scripts` | PASS |

## Scope Confirmation

- Stage 14 review was not performed.
- GitHub upload was not performed.
- S14-P2 and S14-P3 were not performed.
- No raw business data, zip, Excel workbook, PDF, private CSV, sqlite/db, bank statement, contract, payroll, tax filing, real amount, real account identifier, field plaintext or credentials were committed.
