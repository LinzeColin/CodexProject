# S11-P1｜首页与导航测试结果

## TDD 红灯

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_home_navigation_runtime -q
```

初始结果:

```text
ModuleNotFoundError: No module named 'KMFA.tools.home_navigation_runtime'
FAILED (errors=1)
```

## 专项验证

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_home_navigation_runtime -q
```

结果:

```text
Ran 5 tests in 0.006s
OK
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/home_navigation_runtime.py
```

结果:

```text
PASS: KMFA S11-P1 home navigation artifacts generated (navigation_modules=8, html_exports=1, km_brand=true, blue_business_style=true, all_chinese=true, formal_report_allowed=false, business_decision_basis_allowed=false, s11_p2_scope=false, s11_p3_scope=false, stage11_review=false, github_upload=false)
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s11_p1_home_navigation.py
```

结果:

```text
PASS: KMFA S11-P1 home navigation check passed (navigation_modules=8, html_exports=1, km_brand=true, blue_business_style=true, all_chinese=true, formal_report_allowed=false, business_decision_basis_allowed=false, s11_p2_scope=false, s11_p3_scope=false, stage11_review=false, github_upload=false)
```

## 覆盖

- 8 个 S11-P1 必需首页模块全部存在。
- HTML 首页样张包含 KMFA 经营分析系统、KM 标识、蓝色商务风、全中文业务入口和报告等级 D 阻断。
- 禁止 raw values、字段明文、zip、Excel workbook、PDF、sqlite/db、private CSV 和 credentials。
- scope gate: S11-P2、S11-P3、Stage 11 review、GitHub upload、formal report、business decision basis 均为 false。

## 提交前复跑

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover KMFA/tests -q
```

结果:

```text
Ran 121 tests in 1.817s
OK
```

```text
python3 scripts/lean_governance.py validate --project KMFA
python3 scripts/validate_project_governance.py --project KMFA
```

结果:

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
```

结果:

```text
PASS: KMFA no omission check passed (requirements=20, P0=9, P1=8, status_records=394, tasks=162, v1.2_html=45+)
PASS: required KMFA v1.2 HTML/UIUX/report samples are present (html=45, core=7).
PASS: no KMFA Python float money usage found
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s10_p1_report_templates.py
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s10_p2_report_grade_runtime.py
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s10_p3_report_export.py
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s10_stage_review.py
```

结果:

```text
PASS: S10-P1/S10-P2/S10-P3/Stage 10 validators passed without regression.
```

```text
git diff --check -- KMFA
```

结果:

```text
PASS: no whitespace errors
```

```text
Ruby JSON/JSONL/YAML parse check
```

结果:

```text
PASS: parse check passed (json=2, jsonl=4, yaml=6)
```

```text
raw/private file scan
high-confidence secret scan
```

结果:

```text
PASS: raw/private file scan passed (zip/xlsx/xls/xlsm/pdf/sqlite/db/parquet=0)
PASS: high-confidence secret scan passed
```
