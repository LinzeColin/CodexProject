# S05-P2 Excel 候选机器复核与待人工决策记录

## 范围

- Stage/Phase: `S05-P2`
- Task: `S5PBT01-S5PBT03`
- 本记录只处理 S05-P2 剩余 1 个 Excel A0 候选的 5 条 pending 字段：`contract_amount`、`total_expense`、`gross_profit`、`gross_margin`、`cost_category`。
- 本记录不进入 S05-P3，不执行 Q4 人工确认，不创建 Q5 计算基准，不生成 zero-delta、事实层、报告、UI 或 GitHub upload。

## 机器复核结论

- Excel 候选仍保持 `Q3` 机器候选，`q4_human_confirmed=false`，`q5_calculation_baseline_allowed=false`。
- 现有 Ring4 Excel 提取证据显示该 workbook 更像交叉来源汇总/支持材料，而不是可直接绑定为单一 A0 项目基准的独立项目文件。
- Excel summary rows 中存在合同/发票/毛利等部分支持字段，但没有可机器安全映射为单一项目 `total_expense` 的直接字段，也没有项目级 `cost_category` 绑定。
- PDF 与 Excel cross-source 检查只有部分项目匹配：8 条 PDF 项目检查中 4 条有 Excel 匹配，其余仍需人工解释或私有映射。
- 因此本轮不能为 Excel 候选生成占位 hash、不能把 workbook 行聚合成单一项目、不能把 5 条 pending 字段标记为完成。

## 公开仓库边界

- 未提交 Excel、PDF、zip、私有 CSV 或解包文件。
- 未提交合同额、支出合计、毛利、毛利率、成本分类的业务明文值。
- 公开仓库只记录字段 key、候选/file id、计数、状态、证据路径和人工决策要求。

## 决策状态

- decision_status: `machine_reviewed_human_resolution_required`
- reason_code: `excel_workbook_is_cross_source_summary_not_standalone_project_fixture`
- S05-P2 仍未完成；S05-P3 仍不得启动。
- Owner 决策包已生成: `KMFA/stage_artifacts/S05_P2_a0_golden_fixture/human/excel_owner_decision_packet.md`
- 下一步必须由 owner 或授权私有映射明确 Excel 候选角色：
  - 补齐 Excel candidate 的 5 条字段 private hash/source anchor；或
  - 确认 Excel candidate 不是独立 A0 项目基准，并以人工决策形式保留/豁免/降级。

## 关联证据

- `KMFA/stage_artifacts/S05_P2_a0_golden_fixture/machine/excel_resolution_manifest.json`
- `KMFA/stage_artifacts/S05_P2_a0_golden_fixture/human/excel_owner_decision_packet.md`
- `KMFA/stage_artifacts/S05_P2_a0_golden_fixture/machine/excel_owner_decision_packet.json`
- `KMFA/metadata/approvals/resolution_events.jsonl`
- `KMFA/metadata/approvals/control_events.jsonl`
- `KMFA/stage_artifacts/S05_P2_a0_golden_fixture/human/private_backfill_record.md`
