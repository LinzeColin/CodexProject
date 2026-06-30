# S10-P2｜报告可信等级测试结果

## 已执行

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_report_grade_runtime -q
```

结果:

```text
Ran 5 tests in 0.003s
OK
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/report_grade_runtime.py
```

结果:

```text
PASS: KMFA S10-P2 report grade runtime artifacts generated (grade_records=2, grade_distribution={'D': 2}, pending_reconciliation_count=12, complete_trusted_report_display_allowed=false, formal_report_allowed=false, s10_p3_scope=false, export_artifact_count=0)
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s10_p2_report_grade_runtime.py
```

结果:

```text
PASS: KMFA S10-P2 report grade runtime check passed (grade_records=2, grade_distribution={'D': 2}, pending_reconciliation_count=12, complete_trusted_report_display_allowed=false, formal_report_allowed=false, business_decision_basis_allowed=false, s10_p3_scope=false, export_artifact_count=0)
```

## 验收覆盖

- S10-P2 required reports 覆盖: `project_cost_special_report`, `business_overview_report`
- A/B/C/D 等级运行时判定: 当前两份报告均为 `D`
- 缺关键数据或未关闭差异阻断完整可信报告显示: 已覆盖
- 每个报告记录版本、公式版本、字段映射版本: 已覆盖
- public-safe payload: 已覆盖

## 提交前复跑结果

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover KMFA/tests -q
```

结果:

```text
Ran 109 tests in 1.832s
OK
```

```text
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/no_omission_check.py
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_no_float_money.py
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/metadata_protocol_check.py
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/immutability_policy_check.py
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_report_grade_gate.py
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_required_html.py
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s09_p1_project_cost_fact_layer.py
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s09_p2_margin_cash_margin.py
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s09_p3_scope_reconciliation.py
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s10_p1_report_templates.py
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s10_p2_report_grade_runtime.py
```

结果: 全部 `PASS`。

```text
PYTHONDONTWRITEBYTECODE=1 python3 scripts/lean_governance.py validate --project KMFA
PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_project_governance.py --project KMFA
```

结果:

```text
errors: 0
warnings: 0
```

结构和安全检查:

- JSON/JSONL parse: `report_grade_runtime_manifest.json`, `report_grade_runtime_records.jsonl`, S10-P2 machine manifest, stage status 和 governance events 均通过。
- YAML parse: touched governance/project/model registry files 均通过。
- CSV parse: `KMFA/docs/governance/parameter_registry.csv` 为 109 rows / 34 columns，无列数错位。
- raw/private file scan: 未发现 `.zip`, `.xlsx`, `.xls`, `.pdf`, `.sqlite`, `.db`。
- high-signal secret scan: 无命中。
- `git diff --check`: 通过。
