# Token ROI Ledger｜Token经济转化台账

Token ROI Ledger 是 EVA_OS 的 Value Layer 最小闭环。它把本地审计、就绪检查、报告、RunMetadata、数据质量和交叉校验产物登记成可追溯资产，先证明“产出存在、可复核、可复用”，再等待人工补充真实收入、节省成本、避免损失或资产复用价值。

## 当前范围

当前产品化范围：

- 扫描 `data/systemAudit` 中的 Data Trust、Integration Audit、Daily Readiness 等正式产物。
- 扫描报告目录 `~/Downloads/量化回测分析` 中的 Word 报告、RunMetadata、数据质量、交叉校验和实验产物。
- 提供 Streamlit `Token ROI` 工作台，人工录入真实可复核的收入、节省成本、避免损失、资产复用价值、AI 成本和人工时间成本。
- 人工条目保存到本地 `data/value/TokenROIManualEntries.json`，供台账生成、总控驾驶舱和后续复盘读取；该文件默认 gitignored，避免真实金额误传。
- 支持 reviewed value evidence 刷新入口，把真实金额证据默认放在 `data/private/value/TokenROIReviewedValueEvidence.json`，避免把私人财务假设提交到 GitHub。
- 输出 JSON、CSV、Markdown、PDF。
- 输出 `EVATokenROIRuntimeSummaryV1` compact 运行摘要，供 UI、总控驾驶舱和后续 agent 低 token 读取。
- 同时写入 dated 文件和 `latest` 文件，便于后续总控驾驶舱读取。

## 输出位置

默认输出到：

```text
data/value
```

主要文件：

```text
EVATokenROILedger_DDMMYYYY.json
EVATokenROILedger_DDMMYYYY.csv
EVATokenROILedger_DDMMYYYY.md
EVATokenROILedger_DDMMYYYY.pdf
EVATokenROILedger_latest.json
EVATokenROILedger_latest.csv
EVATokenROILedger_latest.md
EVATokenROILedger_latest.pdf
EVATokenROIRuntimeSummary_DDMMYYYY.json
EVATokenROIRuntimeSummary_latest.json
TokenROIReviewedValueEvidence.example.json
```

## 使用命令

生成正式台账：

```bash
$EVA_OS_HOME/scripts/tokenRoiLedger.sh --output-dir data/value
```

只查看 JSON：

```bash
$EVA_OS_HOME/scripts/tokenRoiLedger.sh --json
```

只查看低 token 运行摘要：

```bash
$EVA_OS_HOME/scripts/tokenRoiLedger.sh --summary-json
```

从本地 reviewed value evidence 刷新：

```bash
$EVA_OS_HOME/scripts/tokenRoiReviewedValueRefresh.sh --entry-path data/private/value/TokenROIReviewedValueEvidence.json --output-dir data/value
```

用原台账入口读取 reviewed/manual entry：

```bash
$EVA_OS_HOME/scripts/tokenRoiLedger.sh --manual-entry-path data/private/value/TokenROIReviewedValueEvidence.json --summary-json
```

把 reviewed value evidence 纳入统一 runtime summary 刷新：

```bash
$EVA_OS_HOME/scripts/refreshRuntimeSummaries.sh --token-roi-entry-path data/private/value/TokenROIReviewedValueEvidence.json
```

## Reviewed Value Evidence Contract

默认私有输入：

```text
data/private/value/TokenROIReviewedValueEvidence.json
```

公开样本与 schema：

```text
data/value/TokenROIReviewedValueEvidence.example.json
shared/schema/token_roi_reviewed_value_evidence.schema.json
```

每条 reviewed value evidence 用于解释一个系统产出为什么产生价值。核心字段：

- `run_date`: 任务或交付日期。
- `task_goal`: 任务目标。
- `title`: 价值证据标题。
- `subsystem`: 归属系统。
- `value_contribution`: 价值类型，例如 System Reliability、Decision Support、Validation Efficiency。
- `evidence_link` / `source_path`: 可复核证据。公开样本使用 `sample://token-roi/...`。
- `ai_cost`、`human_time_cost`: AI 和人工成本。
- `revenue_generated`、`cost_saved`、`loss_avoided`、`asset_reuse_value`: 已复核价值字段。
- `time_saved_hours`、`reuse_count`: 效率和复用指标。
- `review_status`: `PendingReview`、`Reviewed` 或 `Rejected`。

计入规则：

- 只有 `review_status=Reviewed` 且至少一个真实财务字段大于 0 的条目会进入 `Quantified`。
- 最好同时提供 `evidence_link` 或 `source_path`，否则证据闸门会提示复核。
- `PendingReview` 可以保存假设，但不会进入已量化财务汇总。
- 默认真实输入位于 `data/private/**`，不应提交。
- 生成的 full ledger 可能包含 reviewed 金额和证据线索；提交或分享前必须人工检查。

## 运行摘要与证据闸门

`EVATokenROIRuntimeSummaryV1` 只保留 compact 状态，不包含完整 `records`，用于快速判断当前台账是否值得继续人工复核。

核心字段：

- `status`: `Pass`、`NeedsReview` 或 `Blocked`。
- `record_count`: 完整台账记录数。
- `quantified_records`: 已复核且有真实金额字段的记录数。
- `pending_financial_hypothesis_count`: 已填写金额但仍处于 `PendingReview` 的人工假设数量。
- `financial_totals`: 已量化记录的收益、成本、净价值和聚合 ROI。
- `evidence_gate`: `LedgerSchema`、`RecordsPresent`、`QuantifiedValuePresent`、`PendingValueReview`、`QuantifiedEvidenceLinks`、`FormulaReady`、`ResearchOnlyBoundary`。
- `token_policy`: 明确摘要不包含完整 records，也不在台账构建之外重复扫描报告目录。

## 公式

```text
Token ROI = (新增收入 + 节省成本 + 避免损失 + 资产复用价值 - AI成本 - 人工时间成本) / (AI成本 + 人工时间成本)
```

系统不自动填写金额。原因是没有真实收入、成本、人工时间或资产复用价值输入时，任何金额都是伪造确定性。

因此：

- `revenue_generated` 默认为 `0.00`。
- `cost_saved` 默认为 `0.00`。
- `loss_avoided` 默认为 `0.00`。
- `asset_reuse_value` 默认为 `0.00`。
- `ai_cost` 默认为 `0.00`。
- `human_time_cost` 默认为 `0.00`。
- `roi_score` 默认为 `null`。
- `value_status` 默认为 `Unquantified`。

人工条目必须同时满足以下条件才会升级为 `Quantified`：

- `review_status=Reviewed`。
- 至少一个真实财务字段大于 0，例如 `cost_saved`、`revenue_generated`、`loss_avoided`、`asset_reuse_value`、`ai_cost` 或 `human_time_cost`。
- 最好提供 `evidence_link` 或 `source_path`，便于回到报告、账单、截图、JSON、CSV、PDF 或源码变更复核。

`PendingReview` 条目可以先保存估算和证据线索，但不会进入已量化财务汇总。

## 字段说明

| 字段 | 含义 |
| --- | --- |
| `roi_id` | 按文件路径、修改时间和大小生成的稳定编号。 |
| `record_type` | `ArtifactEvidence` 或 `ManualValueEvidence`。 |
| `subsystem` | 产物来源系统，例如 QuantLab 或 EVA_OS Foundation。 |
| `artifact_type` | 产物类型，例如 Daily Readiness、Data Trust Audit、Backtest Word Report。 |
| `source_path` | 证据文件路径。 |
| `value_contribution` | 推断的价值贡献，例如 Data Credibility、System Reliability、Decision Support。 |
| `evidence_level` | 当前记录的证据层级；文件存在性为 FACT。 |
| `decision_level` | 当前默认 Observe，表示只登记不产生操作建议。 |
| `value_status` | 当前是否已有真实金额量化。 |
| `run_date` | 任务或产物对应日期。 |
| `task_goal` | 本次 run 要解决的真实目标。 |
| `time_saved_hours` | 人工登记的节省小时数。 |
| `reuse_count` | 该资产或方法被复用的次数。 |
| `evidence_link` | 可复核证据链接或说明。 |
| `notes` | 人工复核备注、假设或证据缺口。 |
| `next_action` | 下一步人工复核或利用方式。 |

## 风险边界

Token ROI Ledger 不证明任何策略盈利，不产生实盘买卖建议，不自动交易，不自动付款，不自动下注。它只把产物登记为可审计资产，并明确哪些价值已经量化、哪些仍未量化。
