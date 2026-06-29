# S04-P3 测试结果

更新时间: 2026-06-29

## 已运行

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_basic_tool_boundaries -q
```

结果:

```text
Ran 4 tests
OK
```

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_field_standardization -q
```

结果:

```text
Ran 5 tests
OK
```

```bash
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/generate_tool_test_report.py --format markdown
```

结果:

```text
Status: PASS
Case summary: 22 total / 22 passed / 0 failed
Raw business data used: false
```

```bash
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_no_float_money.py
```

结果:

```text
PASS: no KMFA Python float money usage found
```

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_amount_tools -q
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_source_priority -q
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_source_check_matrix -q
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_file_import_register -q
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/metadata_protocol_check.py
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/no_omission_check.py
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_required_html.py
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/immutability_policy_check.py
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_report_grade_gate.py
PYTHONDONTWRITEBYTECODE=1 python3 scripts/lean_governance.py validate --project KMFA
PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_project_governance.py --project KMFA
git diff --check -- README.md governance/projects.yaml KMFA
find KMFA -type f \( -name '*.zip' -o -name '*.xls' -o -name '*.xlsx' -o -name '*.pdf' -o -name '*.sqlite' -o -name '*.db' -o -name '*.sqlite-shm' -o -name '*.sqlite-wal' \) -print
```

结果:

```text
PASS: amount_tools, source_priority, source_check_matrix and file_import_register tests passed
PASS: KMFA metadata protocol check passed
PASS: KMFA no omission check passed
PASS: required KMFA v1.2 HTML/UIUX/report samples are present
PASS: KMFA immutability policy check passed
PASS: KMFA report grade gate check passed
PASS: CodexProject governance validation errors 0 / warnings 0
PASS: git diff --check no output
PASS: sensitive file suffix scan no output
```

## 覆盖结论

- `S4PCT01`: PASS，覆盖金额小数、负数、Unicode 负号、括号负数、万元、异常字符和非整分拒绝。
- `S4PCT02`: PASS，覆盖中文日期、紧凑日期、斜杠日期、中文年月、紧凑期间、中文完整日期转期间、空值和无效日期。
- `S4PCT03`: PASS，报告生成器可输出 JSON/Markdown 工具函数测试报告。

## 待最终复跑

Stage 4 全部 Phase 已本地完成；下一轮 Stage 4 整体复审仍必须复跑完整 validator 组合，修复复审问题后才允许整体上传 GitHub。
