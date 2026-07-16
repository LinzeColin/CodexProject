# A0 14-Day Shadow Value-Cost Spec · ADP-S3-P03-T039

对比**现有媒体流**与 **A0 官方流**（T034-T036 适配器 → T037 门 → T038 resolver）的 **权威率、污染、及时、覆盖、成本**。
工具：`tools/a0_shadow.py`。**release_mode = SHADOW**：**不切换任何东西**（切换是 T040 canary，且须过 Owner S3 Exit 门）。

## 对比指标（每周期 + 累计）

| 指标 | A0 官方流 | 媒体流（board3 today） |
|---|---|---|
| **权威率** authoritativeness | official-backed / items | ≈0（全媒体） |
| **污染** pollution | 非官方混入 / items | ≈100%（全新闻噪声，见 T037） |
| **及时** latency_hours | 发布→可用 | （媒体更快但不权威） |
| **覆盖** coverage | coverage_misses（漏抓官方数） | — |
| **误报** false_positives | 媒体噪声被误纳数 | — |
| **成本** cost_per_accepted | A0 流请求数 / 已接受项 | — |

`daily`：每周期 metrics。`accumulate`：跨周期累计 + 建议。

## Shadow 纪律（强制，acceptance）

- **至少 14 个完整周期**：`MIN_CYCLES=14`；`< 14` 周期 → 建议 **CONTINUE_SHADOW**（**不以单日样本决策**）。
- **未达门槛继续 Shadow**：门槛 = 权威率 ≥ 99% **且** 污染 ≤ 1%；未达 → CONTINUE_SHADOW。
- 达标（≥14 周期 + 门槛）→ **READY_FOR_OWNER_S3_EXIT_GATE**——**仍需 Owner S3 Exit 门批准**才进 T040 canary 切换。
- **SHADOW 不切换**：`release_mode=SHADOW`，note 明示切换 gated by Owner S3 Exit。

## 验收（`test-results/shadow_tests.txt`，PASS）

代表性 14 周期（真实 board3 媒体 85 条/~6 每周期 vs A0 官方流 ~8/周期）：
- **价值对比**：A0 流 **权威率 100% / 污染 0% / cost_per_accepted 0.375**；媒体流 **权威率 0% / 污染 100%**。
- **≥14 周期 + 不单日决策**：14 周期达标 → READY_FOR_OWNER_S3_EXIT_GATE；**单日 → CONTINUE_SHADOW**；13 周期 → CONTINUE_SHADOW。
- **未达门槛继续**：注入污染使门槛不达 → CONTINUE_SHADOW。
- **不切换**：release_mode=SHADOW，决策 defer 到 Owner S3 Exit。

## 边界

14 周期报告为**代表性**（把可得真实样本分桶为日周期）；**字面 14 天跨真实日历时间**由试点 cron 累计（同 T023 的 7 日 shadow 打法）。真实 latency/coverage/cost 随真实运行填充；决策不在本任务、defer 到 Owner。miss/false-positive 与 cost-per-accepted 已建模，真实值随 shadow 累积。
