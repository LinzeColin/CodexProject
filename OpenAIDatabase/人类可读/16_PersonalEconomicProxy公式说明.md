# 16 Personal Economic Proxy 公式说明

## 结论

S07 P1 已完成。任务 ID 为 `MA-V12-S07P1`，验收 ID 为
`ACC-MA-V12-S07P1`，状态为
`phase_s07_p1_economic_proxy_completed_pending_s07_p2`。

本阶段用内部派生数据生成 Personal Economic Proxy。它把 S06 的主题簇、低价值循环和机会线索转换成六个可解释分数：时间节省、复用价值、返工成本、机会分、技能复利和自动化/增强比例。

公式来源是 `机器治理/参数与公式/personal_economic_proxy.v1_2_s07_p1.json`。
输出是 `data/derived/economic_proxy/personal_economic_proxy.json`。
下一步只允许进入 S07 P2。

## 六个分数

| 分数 | score_key | 含义 | 公式来源 |
|---|---|---|---|
| 时间节省 | `time_saved_proxy` | 估算自动化、模板化、产品化和减少返工可能节省的重复工作时间。 | `FORM-MA-V12-S07P1-001` |
| 复用价值 | `reuse_value_proxy` | 判断哪些主题簇和机会适合沉淀为模板、脚本、validator 或产品入口。 | `FORM-MA-V12-S07P1-002` |
| 返工成本 | `rework_cost_proxy` | 衡量低价值循环和行动半衰期带来的返工成本信号。 | `FORM-MA-V12-S07P1-003` |
| 机会分 | `opportunity_score_proxy` | 使用 S06 候选机会分数和证据密度评估可行动程度。 | `FORM-MA-V12-S07P1-004` |
| 技能复利 | `skill_compounding_proxy` | 衡量跨时间重复出现的能力或工作流是否值得固化为长期复利资产。 | `FORM-MA-V12-S07P1-005` |
| 自动化/增强比例 | `automation_enhancement_ratio_proxy` | 区分更适合自动化的候选和更适合增强、模板化或产品化的候选。 | `FORM-MA-V12-S07P1-006` |

## 限制

- 这是内部 proxy，不是精确收入预测。
- 这不是财务建议，不用于收入、薪资、投资或商业价值承诺。
- 本阶段不接入外部经济数据库；外部经济数据库只保留 v2 接口占位。
- 本阶段不实现 S07 P2 的信息 ROI gate。
- 本阶段不实现 S07 P3 的 Formula What-if Simulator UI。
- 本阶段不修改 raw。

Machine-readable boundary summary: Memory Atlas v1.2 S07 P1 Personal Economic Proxy; MA-V12-S07P1; ACC-MA-V12-S07P1; phase_s07_p1_economic_proxy_completed_pending_s07_p2; validate:v1.2-s07-p1; personal_economic_proxy.v1_2_s07_p1.json; personal_economic_proxy.json; time_saved_proxy; reuse_value_proxy; rework_cost_proxy; opportunity_score_proxy; skill_compounding_proxy; automation_enhancement_ratio_proxy; pending S07 P2; No GitHub main upload in this phase; No remote push in this phase; No raw mutation in this phase; No external economic database; No precise income prediction; No S07 P2 information ROI gate; No S07 P3 what-if UI.
