# Consumption Guard｜个人消费止血系统

Consumption Guard 是 PFI_OS 的消费行为复盘与止血子系统。它把消费事件、账单证据、冲动风险、固定成本和可投资现金流压力整理成可复核台账，用来减少非必要支出对投资纪律和现金流的侵蚀。

## 当前范围

- 提供 Streamlit `消费守卫` 工作台。
- 支持人工录入消费日期、事件类型、分类、金额、商户、支付方式、是否计划内、是否周期性、必要性、冲动分、后悔分、证据和复核状态。
- 支持月可投资现金流预算，用于计算非必要/冲动消费压力。
- Streamlit 人工台账保存到 private Operational Store `consumption_guard` reviewed-input ledger，不写 public Git `data/**` 台账。
- 输出 JSON、CSV、Markdown、PDF 和 latest 指针文件。
- 输出 `PFIOSConsumptionGuardRuntimeSummaryV1` compact 运行摘要，供 UI、总控和后续 agent 低 token 判断证据、风险和现金流压力。
- 支持从 reviewed input 刷新正式快照，默认真实输入和派生输出留在 `$PFI_OS_DATA_HOME/private/derived/consumption_guard`，公共仓库只保留示例和 schema。

## Fail-Closed 规则

只有同时满足以下条件的消费事件才会进入支出、冲动风险、固定成本和现金流压力汇总：

- `review_status=Reviewed`。
- 提供 `evidence_link` 或 `evidence_path`。

`PendingReview`、`Rejected` 或缺少证据的记录只保留在台账中，不会污染守卫指标。

## 风险评分

```text
risk_score = impulse_score * 0.45
           + regret_score * 0.25
           + (100 - necessity_score) * 0.20
           + planning_penalty
```

其中计划内消费 `planning_penalty=0`，非计划消费 `planning_penalty=10`。

风险等级：

| 等级 | 规则 |
| --- | --- |
| `HighImpulse` | `event_type=Impulse` 或 `risk_score >= 70` |
| `Watch` | `risk_score >= 40` |
| `Controlled` | 其他 |

## 使用命令

生成正式消费守卫快照：

```bash
$PFI_OS_HOME/scripts/consumptionGuard.sh --output-dir data/consumption
```

只查看 JSON：

```bash
$PFI_OS_HOME/scripts/consumptionGuard.sh --json-only
```

低 token 检查只输出运行摘要：

```bash
$PFI_OS_HOME/scripts/consumptionGuard.sh --summary-json
```

`PFIOSConsumptionGuardRuntimeSummaryV1` 只保留 compact 状态，不包含完整 `events`，用于快速判断消费证据、冲动风险、固定成本、预算压力和只读安全边界是否可继续。

从本地 reviewed input 生成正式消费守卫和运行摘要：

```bash
$PFI_OS_HOME/scripts/consumptionReviewedInputRefresh.sh --event-path data/private/consumption/ConsumptionGuardReviewedInput.json --output-dir data/consumption --monthly-investable-budget 1000
```

缺少真实输入时，该命令返回 `PFIOSConsumptionGuardReviewedInputRefreshV1 status=Blocked`，不会写入 full snapshot 或 runtime summary。

统一刷新四个低 token runtime summary 时复用同一消费输入：

```bash
$PFI_OS_HOME/scripts/refreshRuntimeSummaries.sh --consumption-event-path data/private/consumption/ConsumptionGuardReviewedInput.json --monthly-investable-budget 1000
```

## Reviewed Input Contract

真实消费输入保存在 Git 忽略路径：

```text
data/private/consumption/ConsumptionGuardReviewedInput.json
```

公共模板和 schema：

```text
data/consumption/ConsumptionGuardReviewedInput.example.json
shared/schema/consumption_guard_reviewed_input.schema.json
```

每条记录至少需要 `event_date`、`event_type`、`category`、`amount` 和 `review_status`。建议同时提供 `currency`、`merchant`、`payment_method`、`planned`、`recurring`、`necessity_score`、`impulse_score`、`regret_score`、`evidence_link` 或 `evidence_path`、`notes`。

进入支出、冲动风险、固定成本和现金流压力汇总必须是 `Reviewed` 且有 `evidence_link` 或 `evidence_path`。真实账单、截图、支付宝/银行导出、商户明细和复核备注只放在 `data/private/consumption`，不得提交到公共 GitHub。

## 输出位置

```text
$PFI_OS_DATA_HOME/private/operational/pfi.sqlite
data/consumption/ConsumptionGuardReviewedInput.example.json
$PFI_OS_DATA_HOME/private/derived/consumption_guard/ConsumptionGuard_DDMMYYYY.json
$PFI_OS_DATA_HOME/private/derived/consumption_guard/ConsumptionGuard_DDMMYYYY.csv
$PFI_OS_DATA_HOME/private/derived/consumption_guard/ConsumptionGuard_DDMMYYYY.md
$PFI_OS_DATA_HOME/private/derived/consumption_guard/ConsumptionGuard_DDMMYYYY.pdf
$PFI_OS_DATA_HOME/private/derived/consumption_guard/ConsumptionGuard_latest.json
$PFI_OS_DATA_HOME/private/derived/consumption_guard/ConsumptionGuard_latest.csv
$PFI_OS_DATA_HOME/private/derived/consumption_guard/ConsumptionGuard_latest.md
$PFI_OS_DATA_HOME/private/derived/consumption_guard/ConsumptionGuard_latest.pdf
$PFI_OS_DATA_HOME/private/derived/consumption_guard/ConsumptionGuardRuntimeSummary_DDMMYYYY.json
$PFI_OS_DATA_HOME/private/derived/consumption_guard/ConsumptionGuardRuntimeSummary_latest.json
shared/schema/consumption_guard_reviewed_input.schema.json
```

## 风险边界

本子系统不连接支付宝、银行、工资、税务、券商或支付系统，不自动分类真实账单，不执行付款、转账、退款、冻结账户或投资操作。冲动风险评分是行为复盘工具，不是医学、心理、投资或财务诊断。
