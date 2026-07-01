# KMFA S14-P3 政策证据测试结果

更新时间: 2026-07-01

## TDD

- RED: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_policy_evidence_plan -q` 预期失败，原因是 `ModuleNotFoundError: No module named 'KMFA.tools.policy_evidence_plan'`。
- GREEN: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_policy_evidence_plan -q` 通过，`Ran 6 tests ... OK`。

## Phase 验收

- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/policy_evidence_plan.py` 通过，生成 S14-P3 policy evidence artifacts。
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s14_p3_policy_evidence_plan.py` 通过，确认 5 类政策目录、5 条缺口、5 条风险提示、D 级展示、正式结论/申报/upload 均阻断。

## 边界扫描

- S14-P3 输出不提交 raw business data、zip、Excel、PDF、sqlite/db、private CSV、字段明文、真实金额、真实账号、税号、发票号、政策评分或正式政策资格结论。
- Stage 14 整体复审和 GitHub upload 未执行。

## 本轮验收

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s KMFA/tests -q` 通过，`Ran 190 tests ... OK`。
- `python3 scripts/lean_governance.py validate --project KMFA` 通过，errors 0 / warnings 0。
- `python3 scripts/validate_project_governance.py --project KMFA` 通过，errors 0 / warnings 0。
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/no_omission_check.py` 通过，status_records=460，tasks=162。
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_required_html.py` 通过，html=45，core=7。
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_no_float_money.py` 通过。
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/metadata_protocol_check.py` 通过，files=19。
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/immutability_policy_check.py` 通过。
- `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_report_grade_gate.py` 通过。
- YAML/JSON/JSONL/CSV parse checks 通过；`parameter_registry.csv` 为 34 列、170 rows。
- 禁止文件类型扫描未发现可提交 `.zip/.xlsx/.xls/.pdf/.sqlite/.db`。
- S14-P3 输出高信号 forbidden scan 无匹配。
- 本次改动文件高信号 raw/secret scan 通过，changed_files=33。
- `git diff --check -- KMFA scripts` 通过。
