# 参数与公式

用于放置 Memory Atlas v1.2 的信息 ROI、Personal Economic Proxy、证据强度、
新鲜度、复用价值、维护成本等公式和参数。

当前 S08 Review 已完成。S08 Review 只复审协作质量、授权边界和 stage flight recorder，
不新增或修改
Personal Economic Proxy、Information ROI、Visual ROI Gate 或 Formula What-if 的 active
公式配置。S07 Review 已复审以下公式配置：
`机器治理/参数与公式/personal_economic_proxy.v1_2_s07_p1.json`、
`机器治理/参数与公式/information_roi.v1_2_s07_p2.json` 和
`机器治理/参数与公式/formula_what_if_defaults.v1_2_s07_p3.json`。

任务 ID：`MA-V12-S08-REVIEW`。

验收 ID：`ACC-MA-V12-S08-REVIEW`。

Validator：`validate:v1.2-s08-review`。

## S07 Review 结论

Personal Economic Proxy、Information ROI、Visual ROI Gate 和 Formula What-if 均保留
中文解释、公式来源、参数引用和 no external economic database 边界。外部经济数据库只保留
v2 占位；本阶段不声称精确收入预测，也不提供财务建议。

## S07 P3 公式

| score_key | 公式 ID | 含义 |
|---|---|---|
| `formula_what_if_proxy_score` | `FORM-MA-V12-S07P3-001` | 在不修改 active config 的前提下，用可调权重预览时间节省、复用价值、机会价值、长期复利、自动化增强、返工成本和低价值循环惩罚对 proxy 分的影响。 |
| `what_if_parameter_proposal` | `FORM-MA-V12-S07P3-002` | 为每个 scenario 生成 proposal-only 参数变更摘要；`proposal_required_before_apply=true`，`active_config_write=false`。 |

S07 P3 是配置预览，不是运行时 UI，不会直接写回
`personal_economic_proxy.v1_2_s07_p1.json`。

## S07 P2 保留公式

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
- 不修改 active formula config。
- Formula What-if 仅为 config preview。
- 不修改运行时 UI。
- 不修改 raw。
- No GitHub main upload in this phase。

S08 Review 只确认 S08 P1/P2/P3 的协作质量、授权边界和运行证据满足 stage gate，不改本目录 active formula config。
下一步是 S09 P1。
