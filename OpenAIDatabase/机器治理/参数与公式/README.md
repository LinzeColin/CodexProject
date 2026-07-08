# 参数与公式

用于放置 Memory Atlas v1.2 的信息 ROI、Personal Economic Proxy、证据强度、
新鲜度、复用价值、维护成本等公式和参数。

当前 S07 P1 已完成。Personal Economic Proxy 公式配置已写入
`机器治理/参数与公式/personal_economic_proxy.v1_2_s07_p1.json`，输出写入
`data/derived/economic_proxy/personal_economic_proxy.json`。

任务 ID：`MA-V12-S07P1`。

验收 ID：`ACC-MA-V12-S07P1`。

Validator：`validate:v1.2-s07-p1`。

## S07 P1 公式

| score_key | 公式 ID | 含义 |
|---|---|---|
| `time_saved_proxy` | `FORM-MA-V12-S07P1-001` | 时间节省 proxy |
| `reuse_value_proxy` | `FORM-MA-V12-S07P1-002` | 复用价值 proxy |
| `rework_cost_proxy` | `FORM-MA-V12-S07P1-003` | 返工成本 proxy |
| `opportunity_score_proxy` | `FORM-MA-V12-S07P1-004` | 机会分 proxy |
| `skill_compounding_proxy` | `FORM-MA-V12-S07P1-005` | 技能复利 proxy |
| `automation_enhancement_ratio_proxy` | `FORM-MA-V12-S07P1-006` | 自动化/增强比例 proxy |

## 边界

- 本阶段只使用内部 derived 数据。
- 不接入外部经济数据库；外部经济数据库只保留 v2 接口占位。
- 不是精确收入预测。
- 不是财务建议。
- 不实现 S07 P2 信息 ROI gate。
- 不实现 S07 P3 Formula What-if Simulator UI。
- 不修改 raw。
- No GitHub main upload in this phase。

下一步是 S07 P2。
