# 参数与公式

用于放置 Memory Atlas v1.2 的信息 ROI、Personal Economic Proxy、证据强度、
新鲜度、复用价值、维护成本等公式和参数。

当前 S07 P2 已完成。Information ROI 公式配置已写入
`机器治理/参数与公式/information_roi.v1_2_s07_p2.json`，输出写入
`data/derived/information_roi/information_roi_gate.json`。

任务 ID：`MA-V12-S07P2`。

验收 ID：`ACC-MA-V12-S07P2`。

Validator：`validate:v1.2-s07-p2`。

## S07 P2 公式

| score_key | 公式 ID | 含义 |
|---|---|---|
| `information_roi_score` | `FORM-MA-V12-S07P2-001` | 用决策价值、可行动性、证据强度、新鲜度、复用价值除以阅读、导航、误导和维护成本，得到 insight/card/chart 的信息 ROI。 |
| `visual_roi_gate` | `FORM-MA-V12-S07P2-002` | 判断 P0 visual 是否有足够信息 ROI、human question、action 和可验证 evidence。 |

S07 P2 同时引用 Visual ROI Gate 配置：
`机器治理/可视化配置/visual_roi_gate.v1_2_s07_p2.json`。没有决策价值的图表不进 P0。

## S07 P1 保留公式

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
- 不实现 S07 P3 Formula What-if Simulator UI。
- 不修改运行时 UI。
- 不修改 raw。
- No GitHub main upload in this phase。

下一步是 S07 P3。
