# S15-P3 Test Results - Salary Boundary

更新时间: 2026-07-01

## Phase 验证

| 命令 | 结果 |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_performance_salary_boundary.py` | PASS: 5 tests |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/performance_salary_boundary.py --generated-at 2026-07-01T23:55:00+10:00` | PASS: artifacts generated |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s15_p3_salary_boundary.py` | PASS: interface_contracts=1, readiness_rows=4, future_read_draft=true, live_integration=false, salary_calculation=false, bonus_approval=false, payroll_export=false, final_approval_human=true, payment_release_human=true, stage15_review=false, github_upload=false |

## Regression 验证

| 命令 | 结果 |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_performance_fact_fields.py` | PASS: 5 tests |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s15_p1_performance_fact_fields.py` | PASS: fields=6, bindings=6, manual_reviews=4, performance_fact_table=false, salary_calculation=false, bonus_approval=false, payroll_export=false |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_performance_review_list.py` | PASS: 5 tests |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s15_p2_performance_review_list.py` | PASS: fact_rows=4, review_items=16, performance_fact_table=true, abnormal_review_list=true, salary_calculation=false, bonus_approval=false, payroll_export=false, final_compensation=false |

## Governance And Safety

| 命令 | 结果 |
|---|---|
| `ruby -ryaml -e 'ARGV.each { |p| YAML.load_file(p); puts "yaml_ok #{p}" }' ...` | PASS: governance/project/model YAML parse checks |
| JSONL parse check for governance events, development events, stage status, salary readiness draft | PASS: rows=81/81/479/4 |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/no_omission_check.py` | PASS: requirements=20, status_records=479, tasks=162 |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_required_html.py` | PASS: html=45, core=7 |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_no_float_money.py` | PASS |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/metadata_protocol_check.py` | PASS |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/immutability_policy_check.py` | PASS |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_report_grade_gate.py` | PASS |
| `python3 scripts/lean_governance.py validate --project KMFA` | PASS: errors=0, warnings=0 |
| `python3 scripts/validate_project_governance.py --project KMFA` | PASS: errors=0, warnings=0 |
| S15-P3 artifact payload scan | PASS: no high-signal secret, private reference, raw value, compensation amount, person marker, or account marker in generated S15-P3 artifacts |
| KMFA sensitive file extension scan | PASS: no source package, workbook, document, database, or binary data file found under KMFA |
| `git diff --check -- KMFA scripts` | PASS |
