# Company CashFlow Command｜公司经营现金流系统

Company CashFlow Command 是 PFI_OS 的经营现金流子系统。它把公司现金余额、收入、支出、应收和应付记录成可复核证据，并输出现金流状态、近 30 天净现金流、Runway、分类汇总和行动队列。

## 当前范围

- 提供 Streamlit `现金流` 工作台。
- 支持人工录入 `BalanceSnapshot`、`Inflow`、`Outflow`、`Receivable` 和 `Payable`。
- 支持分类：收入、税务、工资、供应商、软件、营销、租金、合规、债务和其他。
- Streamlit 人工台账保存到 private Operational Store `company_cashflow` reviewed-input ledger，不写 public Git `data/**` 台账。
- 支持从本地私有 reviewed input 刷新正式快照；真实输入和派生输出默认留在 `$PFI_OS_DATA_HOME/private/derived/company_cashflow`。
- 输出 JSON、CSV、Markdown、PDF 和 latest 指针文件。
- 输出 `PFIOSCompanyCashFlowRuntimeSummaryV1` compact 运行摘要，供 UI、总控驾驶舱和后续 agent 低 token 读取。

## 证据规则

只有同时满足以下条件的记录才会进入现金流汇总：

- `review_status=Reviewed`。
- `evidence_status=Pass`，即提供了 `evidence_link` 或 `evidence_path`。

`PendingReview`、`Rejected` 或缺少证据的记录只保留在台账中，不会计入余额、收入、支出、应收、应付或 Runway。

## 主要概念

| 字段 | 含义 |
| --- | --- |
| `BalanceSnapshot` | 某日现金余额快照，来自人工录入和可复核证据。 |
| `Inflow` | 已到账收入。 |
| `Outflow` | 已支付支出。 |
| `Receivable` | 应收但未到账，不等同于真实现金。 |
| `Payable` | 应付但未支付，不等同于真实现金流出。 |
| `Runway` | 当前现金余额按近期支出速度可覆盖的天数。 |
| `cashflow_status` | `MissingBalance`、`NeedsEvidence`、`Critical`、`Watch`、`NeedsReview`、`StableWithPendingReview` 或 `Stable`。 |

## 使用命令

生成正式现金流快照：

```bash
$PFI_OS_HOME/scripts/cashFlowCommand.sh --output-dir data/cashflow
```

只查看 JSON：

```bash
$PFI_OS_HOME/scripts/cashFlowCommand.sh --json-only
```

只查看低 token 运行摘要：

```bash
$PFI_OS_HOME/scripts/cashFlowCommand.sh --summary-json
```

从本地 reviewed input 生成正式快照和 runtime summary：

```bash
$PFI_OS_HOME/scripts/cashFlowReviewedInputRefresh.sh \
  --entry-path data/private/cashflow/CompanyCashFlowReviewedInput.json \
  --output-dir data/cashflow
```

如果默认私有输入文件不存在，该命令返回 `PFIOSCompanyCashFlowReviewedInputRefreshV1 status=Blocked`，不会写入现金流输出。

刷新全部 compact runtime summaries 时复用同一 reviewed input：

```bash
$PFI_OS_HOME/scripts/refreshRuntimeSummaries.sh \
  --cashflow-entry-path data/private/cashflow/CompanyCashFlowReviewedInput.json
```

## Reviewed Input Contract

真实输入应保存到被 Git 忽略的本地路径：

```text
data/private/cashflow/CompanyCashFlowReviewedInput.json
```

公共模板和 schema：

```text
data/cashflow/CompanyCashFlowReviewedInput.example.json
shared/schema/company_cashflow_reviewed_input.schema.json
```

每条记录必须至少包含：

- `entry_date`: `YYYY-MM-DD`。
- `direction`: `Inflow`、`Outflow`、`BalanceSnapshot`、`Receivable` 或 `Payable`。
- `category`: 现金流分类。
- `amount`: 大于 0 的金额。
- `review_status`: `PendingReview`、`Reviewed` 或 `Rejected`。

只有 `review_status=Reviewed` 且提供 `evidence_link` 或 `evidence_path` 的记录会计入现金流。真实 evidence 可以是本地私有文件路径或内部链接，但不得提交到 public GitHub。

## 运行摘要与证据闸门

`PFIOSCompanyCashFlowRuntimeSummaryV1` 只保留 compact 状态，不包含完整 `entries`，用于快速判断现金流是否可继续经营复盘。

核心字段：

- `status`: `Pass`、`NeedsReview` 或 `Blocked`。
- `cashflow_status`: 原始现金流状态，例如 `MissingBalance`、`NeedsEvidence`、`Critical`、`Watch` 或 `Stable`。
- `entry_count`、`counted_records`、`pending_review_records`、`reviewed_missing_evidence_records`。
- `latest_balance`、`latest_balance_date`、`net_cashflow`、`runway_days`、`receivable`、`payable`。
- `evidence_gate`: `CommandSchema`、`BalanceSnapshot`、`EvidenceCompleteness`、`ManualReview`、`Runway`、`NetCashflow`、`BalanceFreshness`、`NoExternalExecution`。
- `token_policy`: 明确摘要不包含完整 entries，也不连接任何外部金融系统。

## 输出位置

```text
$PFI_OS_DATA_HOME/private/operational/pfi.sqlite
$PFI_OS_DATA_HOME/private/derived/company_cashflow/CompanyCashFlowCommand_DDMMYYYY.json
$PFI_OS_DATA_HOME/private/derived/company_cashflow/CompanyCashFlowCommand_DDMMYYYY.csv
$PFI_OS_DATA_HOME/private/derived/company_cashflow/CompanyCashFlowCommand_DDMMYYYY.md
$PFI_OS_DATA_HOME/private/derived/company_cashflow/CompanyCashFlowCommand_DDMMYYYY.pdf
$PFI_OS_DATA_HOME/private/derived/company_cashflow/CompanyCashFlowCommand_latest.json
$PFI_OS_DATA_HOME/private/derived/company_cashflow/CompanyCashFlowCommand_latest.csv
$PFI_OS_DATA_HOME/private/derived/company_cashflow/CompanyCashFlowCommand_latest.md
$PFI_OS_DATA_HOME/private/derived/company_cashflow/CompanyCashFlowCommand_latest.pdf
$PFI_OS_DATA_HOME/private/derived/company_cashflow/CompanyCashFlowRuntimeSummary_DDMMYYYY.json
$PFI_OS_DATA_HOME/private/derived/company_cashflow/CompanyCashFlowRuntimeSummary_latest.json
```

## 风险边界

本子系统不连接银行账户、支付账户、税务系统、工资系统或会计系统；不执行付款、转账、下单或任何外部账户动作。所有金额都必须来自人工录入和可复核证据。Runway 只是经营现金安全指标，不是融资、付款、投资或税务建议。
