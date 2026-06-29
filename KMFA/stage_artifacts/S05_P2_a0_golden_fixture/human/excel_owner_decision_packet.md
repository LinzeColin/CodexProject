# S05-P2 Excel 候选 Owner 决策包

## 范围

- Stage/Phase: `S05-P2`
- Task: `S5PBT01-S5PBT03`
- 目标: 为剩余 Excel A0 候选的 5 条 pending 字段提供 owner/授权决策入口。
- 本文件不是 Q4 人工确认记录，不是 Q5 计算基准，不完成 S05-P2，不启动 S05-P3。

## 当前已证实状态

- A0 字段候选总数: `45`
- PDF 字段已 hash-only 回填: `40`
- Excel 字段仍 pending: `5`
- Pending 字段: `contract_amount`, `total_expense`, `gross_profit`, `gross_margin`, `cost_category`
- 机器复核结论: Excel workbook 是交叉来源汇总/支持材料，不能机器合成为单一 A0 项目基准。
- 公开仓库边界: 不提交 Excel、PDF、zip、私有 CSV、业务字段明文或私有运行路径。

## 允许的 owner/授权决策

### A. 补齐私有字段映射

适用条件: owner 或授权人员确认 Excel candidate 是独立 A0 项目基准的一部分，并提供可验证私有映射。

必须提供:

- candidate id 和 file id
- 5 个字段的 source anchor
- 5 个字段的私有 hash/ref 输入
- Q3 机器候选状态是否保留
- 是否仍需要后续 Q4 人工确认

结果: 可继续 S05-P2 hash-only 回填验证；仍不得直接进入 Q5。

### B. 降级为交叉来源支持材料

适用条件: owner 或授权人员确认 Excel candidate 不是独立 A0 项目基准，只作为 PDF 与系统复算的交叉校验来源。

必须确认:

- Excel candidate 不进入 standalone A0 golden fixture
- 5 个 pending 字段不伪造 hash，不生成占位值
- 后续在 S06 或差异队列中作为 cross-source support 使用
- S05-P3 不得使用该 Excel candidate 做 Q5 计算基准

结果: 可形成明确 resolution，后续再判断 S05-P2 是否可在 PDF baseline 范围内完成。

### C. 保持 pending

适用条件: 暂无授权映射或 owner 尚未决策。

结果: S05-P2 继续阻塞；S05-P3、Stage 5 review 和 GitHub upload 不允许。

## 停止条件

- 需要提交原始 Excel/PDF/zip 或解包文件。
- 需要提交真实合同额、支出合计、毛利、毛利率、成本分类明文。
- 需要把缺失字段静默置 0。
- 需要生成占位 hash 或把 workbook 行机器聚合成单一项目。
- 需要绕过 Q4/Q5 门禁进入正式报告。

## 下一步

等待 owner 或授权私有映射选择 A/B/C 之一。选择前，本轮状态保持 `machine_reviewed_human_resolution_required`。
