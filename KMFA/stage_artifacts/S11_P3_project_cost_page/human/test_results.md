# S11-P3｜项目成本页面测试结果

更新时间: 2026-07-01

## TDD Red

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_project_cost_page_runtime -q
```

结果:

```text
ModuleNotFoundError: No module named 'KMFA.tools.project_cost_page_runtime'
```

## TDD Green

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_project_cost_page_runtime -q
```

结果:

```text
Ran 5 tests in 0.009s

OK
```

```bash
python3 -m py_compile KMFA/tools/project_cost_page_runtime.py KMFA/tools/check_s11_p3_project_cost_page.py
```

结果:

```text
PASS
```

```bash
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/project_cost_page_runtime.py
```

结果:

```text
PASS: KMFA S11-P3 project cost page artifacts generated (projects=4, margin_records=4, cost_categories=9, pending_reconciliations=12, report_preview=true, report_grade=D, quality_bypass=false, formal_report_allowed=false, stage11_review=false, github_upload=false)
```

```bash
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s11_p3_project_cost_page.py
```

结果:

```text
PASS: KMFA S11-P3 project cost page passed (projects=4, margin_records=4, cost_categories=9, pending_reconciliations=12, report_preview=true, report_grade=D, quality_bypass=false, formal_report_allowed=false, stage11_review=false, github_upload=false)
```

## 覆盖

- 验证 4 条 public-safe 项目页面记录。
- 验证 9 类成本结构、4 条 margin records 和 12 条 pending reconciliation 状态。
- 验证报告预览可直接查看，同时 D 级质量门禁不可绕过。
- 验证新增 HTML 和 machine artifacts 不包含 raw/private refs、真实金额、真实账号、字段明文、Excel workbook、PDF、zip、sqlite/db 或 private CSV。

## Final Acceptance

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_home_navigation_runtime KMFA.tests.test_source_check_board_runtime KMFA.tests.test_project_cost_page_runtime -q
```

结果:

```text
Ran 15 tests in 0.026s

OK
```

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s KMFA/tests -q
```

结果:

```text
Ran 131 tests in 1.845s

OK
```

```bash
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s11_p1_home_navigation.py
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s11_p2_source_check_board.py
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s11_p3_project_cost_page.py
```

结果:

```text
PASS: KMFA S11-P1 home navigation check passed
PASS: KMFA S11-P2 source check board passed
PASS: KMFA S11-P3 project cost page passed
```

```bash
python3 KMFA/tools/check_required_html.py
python3 KMFA/tools/no_omission_check.py
python3 scripts/lean_governance.py validate --project KMFA
python3 scripts/validate_project_governance.py --project KMFA
```

结果:

```text
PASS: required KMFA v1.2 HTML/UIUX/report samples are present (html=45, core=7).
PASS: KMFA no omission check passed (requirements=20, P0=9, P1=8, status_records=404, tasks=162, v1.2_html=45+)
CodexProject governance validation: errors 0 / warnings 0
```

```bash
raw/private extension scan
high-signal secret scan
JSON/JSONL parse checks
YAML parse checks
git diff --check -- KMFA
```

结果:

```text
PASS: no forbidden raw/private file extensions committed outside taskpack baseline
PASS: high-signal secret scan passed
PASS: JSON/JSONL parse checks passed
PASS: YAML parse checks passed
PASS: git diff --check
```
