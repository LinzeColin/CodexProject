# Information ROI 与 Visual ROI Gate 说明

S07 P2 已完成。任务 ID 为 `MA-V12-S07P2`，验收 ID 为
`ACC-MA-V12-S07P2`，状态为
`phase_s07_p2_information_roi_completed_pending_s07_p3`。

本阶段定义每个 insight、card、chart 的 Information ROI，并实现轻量
Visual ROI Gate。核心规则是：没有决策价值的图表不进 P0。

## 产物

- 公式配置：`机器治理/参数与公式/information_roi.v1_2_s07_p2.json`
- Visual ROI Gate 配置：`机器治理/可视化配置/visual_roi_gate.v1_2_s07_p2.json`
- 派生输出：`data/derived/information_roi/information_roi_gate.json`
- 生成脚本：`scripts/build_memory_atlas_information_roi.py`
- 运行入口：`python scripts/atlasctl.py analyze --stage information-roi`
- 审计入口：`python scripts/atlasctl.py audit --check visual-roi`
- Validator：`validate:v1.2-s07-p2`

## 如何读

Information ROI 使用内部 derived 数据评估内容是否值得占据决策视图。每个 ROI item
都保留 `formula_id`、`formula_source`、`parameter_refs` 和 `evidence_refs`。

输出当前覆盖：

| 类型 | 数量 | 用途 |
|---|---:|---|
| insight | 15 | 判断哪些洞察有行动价值、复用价值和证据强度。 |
| card | 6 | 判断 Personal Economic Proxy score card 是否值得继续作为 P0 解释卡。 |
| chart | 10 | 判断 P0 图表是否有清晰 human question 和 action。 |

Visual ROI Gate 要求每个 P0 chart 同时具备：

- `human_question`：用户打开图表时要回答的真实问题。
- `action`：图表支持的下一步动作。
- `information_roi_score`：达到 P0 阈值。
- `visual_roi_gate_pass=true`。

当前 10 个 P0 visual 均通过 gate，`failed_p0_count=0`。被排除示例包括
`decorative_word_cloud` 和 `raw_schema_table`，原因是它们没有足够直接的决策价值。

## 边界

- 不接入外部经济数据库。
- 不是精确收入预测。
- 不构成财务建议。
- 不修改 raw。
- 不修改运行时 UI。
- 不实现 S07 P3 Formula What-if Simulator UI。
- No GitHub main upload in this phase。

下一步只允许进入 S07 P3。

Machine-readable boundary summary: Memory Atlas v1.2 S07 P2 Information ROI and Visual ROI Gate; MA-V12-S07P2; ACC-MA-V12-S07P2; phase_s07_p2_information_roi_completed_pending_s07_p3; validate:v1.2-s07-p2; information_roi.v1_2_s07_p2.json; visual_roi_gate.v1_2_s07_p2.json; information_roi_gate.json; insight; card; chart; 没有决策价值的图表不进 P0; pending S07 P3; No GitHub main upload in this phase; No remote push in this phase; No raw mutation in this phase; No external economic database; No precise income prediction; No S07 P3 what-if UI.
