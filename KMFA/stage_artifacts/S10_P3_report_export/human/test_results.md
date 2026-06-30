# S10-P3｜导出测试结果

## TDD 红灯

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_report_export_runtime -q
```

初始结果:

```text
ModuleNotFoundError: No module named 'KMFA.tools.report_export_runtime'
FAILED (errors=1)
```

## 专项验证

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_report_export_runtime -q
```

结果:

```text
Ran 5 tests in 0.005s
OK
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/report_export_runtime.py
```

结果:

```text
PASS: KMFA S10-P3 report export artifacts generated (export_records=2, html_exports=2, csv_appendices=2, excel_compatible_downloads=2, pdf_private_runtime_enabled=true, committed_pdf_files=0, committed_excel_files=0, stage10_review=false, github_upload=false)
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s10_p3_report_export.py
```

结果:

```text
PASS: KMFA S10-P3 report export check passed (export_records=2, html_exports=2, csv_appendices=2, excel_compatible_downloads=2, pdf_private_runtime_enabled=true, committed_pdf_files=0, committed_excel_files=0, formal_report_allowed=false, business_decision_basis_allowed=false, stage10_review=false, github_upload=false)
```

## 覆盖

- HTML 报告优先稳定: 2 个 public-safe HTML exports。
- CSV/Excel 附表可下载: 2 个 public-safe CSV appendices；Excel 采用兼容 CSV 下载模式，不提交 workbook。
- PDF 导出在模板稳定后启用: 已记录 private-runtime-only 策略，不提交 PDF 文件。
- D 级报告限制: HTML/CSV 均保留 `report_grade=D` 和 `blocked_decision_use`。
- scope gate: Stage 10 review、GitHub upload、UI、lineage full check、external connector 均为 false。
- public-safe: 禁止 raw values、字段明文、`.xlsx`、`.pdf`、zip、sqlite/db 和私有 CSV。

## 提交前复跑

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_report_templates KMFA.tests.test_report_grade_runtime KMFA.tests.test_report_export_runtime -q
```

结果:

```text
Ran 15 tests in 0.012s
OK
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover KMFA/tests -q
```

结果:

```text
Ran 115 tests in 1.789s
OK
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s10_p1_report_templates.py
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s10_p2_report_grade_runtime.py
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s10_p3_report_export.py
```

结果:

```text
PASS: KMFA S10-P1 report template check passed (templates=2, sections=11, project_cost_sections=4, business_overview_sections=7, formal_report_allowed=false, trusted_grade_assignment_allowed=false, s10_p2_scope=false, s10_p3_scope=false, ui_scope=false, lineage_full_check_scope=false, external_connector_scope=false)
PASS: KMFA S10-P2 report grade runtime check passed (grade_records=2, grade_distribution={'D': 2}, pending_reconciliation_count=12, complete_trusted_report_display_allowed=false, formal_report_allowed=false, business_decision_basis_allowed=false, s10_p3_scope=false, export_artifact_count=0)
PASS: KMFA S10-P3 report export check passed (export_records=2, html_exports=2, csv_appendices=2, excel_compatible_downloads=2, pdf_private_runtime_enabled=true, committed_pdf_files=0, committed_excel_files=0, formal_report_allowed=false, business_decision_basis_allowed=false, stage10_review=false, github_upload=false)
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/no_omission_check.py
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_required_html.py
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_no_float_money.py
```

结果:

```text
PASS: KMFA no omission check passed (requirements=20, P0=9, P1=8, status_records=384, tasks=162, v1.2_html=45+)
PASS: required KMFA v1.2 HTML/UIUX/report samples are present (html=45, core=7).
PASS: no KMFA Python float money usage found
```

```text
python3 scripts/lean_governance.py validate --project KMFA
python3 scripts/validate_project_governance.py --project KMFA
```

结果:

```text
errors: 0
warnings: 0
errors: 0
warnings: 0
```

```text
JSON/JSONL/YAML/CSV parse checks
raw/private file scan
high-signal secret scan
git diff --check -- KMFA
```

结果:

```text
PASS: JSON/JSONL parse checks passed (json=26, jsonl=43)
PASS: YAML parse checks passed
PASS: parameter_registry csv shape passed (rows=117, columns=34)
raw/private file scan: no zip/xlsx/xls/pdf/sqlite/db files under KMFA
high-signal secret scan: no matches
git diff --check: no output
```
