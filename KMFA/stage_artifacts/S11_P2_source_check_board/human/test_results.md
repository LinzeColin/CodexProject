# S11-P2｜数据源检查板测试结果

## TDD 红灯

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_source_check_board_runtime -q
```

初始结果:

```text
ModuleNotFoundError: No module named 'KMFA.tools.source_check_board_runtime'
FAILED (errors=1)
```

## 专项验证

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_source_check_board_runtime -q
```

结果:

```text
Ran 5 tests in 0.012s
OK
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/source_check_board_runtime.py
```

结果:

```text
PASS: KMFA S11-P2 source check board artifacts generated (matrix_rows=13, html_exports=1, columns=11, statuses=5, status_click_detail=true, blue_gray_surface=true, large_yellow_surface_count=0, formal_report_allowed=false, s11_p3_scope=false, stage11_review=false, github_upload=false)
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s11_p2_source_check_board.py
```

结果:

```text
PASS: KMFA S11-P2 source check board passed (matrix_rows=13, html_exports=1, columns=11, statuses=5, status_click_detail=true, blue_gray_surface=true, large_yellow_surface_count=0, formal_report_allowed=false, s11_p3_scope=false, stage11_review=false, github_upload=false)
```

## 覆盖

- 11 个固定列头全部存在。
- 5 种状态全部覆盖：已就绪、部分/阻塞、失败/不适用、已过期、人工复核。
- HTML 数据源检查板包含 KMFA 数据源检查板、KM 标识、蓝灰商务风、低干扰状态徽标和状态详情面板。
- 禁止 raw values、字段明文、zip、Excel workbook、PDF、sqlite/db、private CSV、真实账号和 credentials。
- scope gate: S11-P3、Stage 11 review、GitHub upload、formal report、business decision basis 均为 false。

## 提交前复跑

```text
python3 -m py_compile KMFA/tools/source_check_board_runtime.py KMFA/tools/check_s11_p2_source_check_board.py
```

结果: PASS

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover KMFA/tests -q
```

结果:

```text
Ran 126 tests in 1.838s
OK
```

```text
python3 scripts/lean_governance.py validate --project KMFA
python3 scripts/validate_project_governance.py --project KMFA
```

初始 finding:

```text
[ERROR] KMFA: KMFA/docs/governance/ASSURANCE_STATUS.yaml active formula count drift
```

修复: 补登记 `FORM-KMFA-HOME-NAVIGATION-001` 和 `FORM-KMFA-SOURCE-CHECK-BOARD-001` 到 `KMFA/docs/governance/formula_registry.yaml`；active formula count 由 27 修复为 29。

复跑结果:

```text
CodexProject governance validation
root: checked
projects checked: KMFA
errors: 0
warnings: 0
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/no_omission_check.py
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_required_html.py
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_no_float_money.py
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s11_p1_home_navigation.py
```

结果:

```text
PASS: KMFA no omission check passed (requirements=20, P0=9, P1=8, status_records=399, tasks=162, v1.2_html=45+)
PASS: required KMFA v1.2 HTML/UIUX/report samples are present (html=45, core=7).
PASS: no KMFA Python float money usage found
PASS: KMFA S11-P1 home navigation check passed (navigation_modules=8, html_exports=1, km_brand=true, blue_business_style=true, all_chinese=true, formal_report_allowed=false, business_decision_basis_allowed=false, s11_p2_scope=false, s11_p3_scope=false, stage11_review=false, github_upload=false)
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s10_p1_report_templates.py
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s10_p2_report_grade_runtime.py
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s10_p3_report_export.py
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s10_stage_review.py
```

结果:

```text
PASS: KMFA S10-P1 report template check passed
PASS: KMFA S10-P2 report grade runtime check passed
PASS: KMFA S10-P3 report export check passed
PASS: KMFA S10 stage review check passed
```

结构和安全扫描:

```text
PASS: parse check passed (json=3, jsonl=4, yaml=7)
PASS: no forbidden raw/private file suffixes under KMFA
PASS: no high-confidence secret patterns under KMFA
git diff --check -- KMFA
```

结果: PASS
