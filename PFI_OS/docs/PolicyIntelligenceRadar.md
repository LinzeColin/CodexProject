# Policy Intelligence Radar｜政策机会情报系统

Policy Intelligence Radar 是 PFI_OS 的政策机会台账。它把政策来源、影响行业、机会类型、权威证据、影响评分和下一步行动整理成可复核记录，用于把政府/监管/交易所/政策系统产物转成可管理机会队列。

## 当前范围

- 提供 Streamlit `政策雷达` 工作台。
- 支持人工录入政策标题、来源、来源类型、URL、本地证据、地区、政策层级、机会类型、影响行业、影响对象、影响摘要和下一步行动。
- 支持权威分、相关分、紧急分和可执行分，生成 `impact_score`。
- Streamlit 人工台账保存到 private Operational Store `policy_radar` reviewed-input ledger，不写 public Git `data/**` 台账。
- 输出 JSON、CSV、Markdown、PDF 和 latest 指针文件。
- 输出 `PFIOSPolicyIntelligenceRuntimeSummaryV1` compact 运行摘要，供 UI、总控和后续 agent 低 token 判断来源证据状态。
- 支持从 reviewed input 刷新正式快照，默认真实输入和派生输出留在 `$PFI_OS_DATA_HOME/private/derived/policy_radar`，公共仓库只保留示例和 schema。

## Fail-Closed 规则

政策机会进入 `Actionable` 必须同时满足：

- `review_status=Reviewed`。
- `source_type` 是 `Official`、`Regulator`、`Government` 或 `Exchange`。
- 提供 `source_url` 或 `evidence_path`。
- `impact_score >= 70`。

`Research`、`News` 或 `Manual` 来源即使有链接和高分，也只能作为 `NeedsAuthorityReview` 或观察线索，必须回溯到官方、监管、政府或交易所来源后才能升级。

## 评分公式

```text
impact_score = authority_score * 0.30
             + relevance_score * 0.30
             + urgency_score * 0.20
             + feasibility_score * 0.20
```

评分只用于排序，不代表政策确定落地、补贴可得、项目可批、合规意见或投资收益。

## 使用命令

生成正式政策雷达快照：

```bash
$PFI_OS_HOME/scripts/policyRadar.sh --output-dir data/policy
```

只查看 JSON：

```bash
$PFI_OS_HOME/scripts/policyRadar.sh --json-only
```

低 token 检查只输出运行摘要：

```bash
$PFI_OS_HOME/scripts/policyRadar.sh --summary-json
```

`PFIOSPolicyIntelligenceRuntimeSummaryV1` 只保留 compact 状态，不包含完整 `opportunities`，用于快速判断政策来源、证据、人工复核和只读安全边界是否可继续。

从本地 reviewed input 生成正式政策雷达和运行摘要：

```bash
$PFI_OS_HOME/scripts/policyReviewedInputRefresh.sh --entry-path data/private/policy/PolicyReviewedInput.json --output-dir data/policy
```

缺少真实输入时，该命令返回 `PFIOSPolicyReviewedInputRefreshV1 status=Blocked`，不会写入 full snapshot 或 runtime summary。

统一刷新四个低 token runtime summary 时复用同一政策输入：

```bash
$PFI_OS_HOME/scripts/refreshRuntimeSummaries.sh --policy-entry-path data/private/policy/PolicyReviewedInput.json
```

## Reviewed Input Contract

真实政策输入保存在 Git 忽略路径：

```text
data/private/policy/PolicyReviewedInput.json
```

公共模板和 schema：

```text
data/policy/PolicyReviewedInput.example.json
shared/schema/policy_reviewed_input.schema.json
```

每条记录至少需要 `published_date`、`title`、`source_name`、`source_type` 和 `review_status`。建议同时提供 `source_url` 或 `evidence_path`、`jurisdiction`、`policy_level`、`opportunity_type`、`sectors`、`affected_entities`、`impact_summary`、`required_action`、`authority_score`、`relevance_score`、`urgency_score` 和 `feasibility_score`。

进入 `Actionable` 必须是 `Reviewed`，来源必须是 `Official`、`Regulator`、`Government` 或 `Exchange`，必须存在 `source_url` 或 `evidence_path`，并且影响评分达到阈值。真实政策证据、内部备注、门户导出和复核材料只放在 `data/private/policy`，不得提交到公共 GitHub。

## 输出位置

```text
$PFI_OS_DATA_HOME/private/operational/pfi.sqlite
data/policy/PolicyReviewedInput.example.json
$PFI_OS_DATA_HOME/private/derived/policy_radar/PolicyIntelligenceRadar_DDMMYYYY.json
$PFI_OS_DATA_HOME/private/derived/policy_radar/PolicyIntelligenceRadar_DDMMYYYY.csv
$PFI_OS_DATA_HOME/private/derived/policy_radar/PolicyIntelligenceRadar_DDMMYYYY.md
$PFI_OS_DATA_HOME/private/derived/policy_radar/PolicyIntelligenceRadar_DDMMYYYY.pdf
$PFI_OS_DATA_HOME/private/derived/policy_radar/PolicyIntelligenceRadar_latest.json
$PFI_OS_DATA_HOME/private/derived/policy_radar/PolicyIntelligenceRadar_latest.csv
$PFI_OS_DATA_HOME/private/derived/policy_radar/PolicyIntelligenceRadar_latest.md
$PFI_OS_DATA_HOME/private/derived/policy_radar/PolicyIntelligenceRadar_latest.pdf
$PFI_OS_DATA_HOME/private/derived/policy_radar/PolicyIntelligenceRuntimeSummary_DDMMYYYY.json
$PFI_OS_DATA_HOME/private/derived/policy_radar/PolicyIntelligenceRuntimeSummary_latest.json
shared/schema/policy_reviewed_input.schema.json
```

## 风险边界

本子系统不自动抓取实时政策，不登录政府平台，不提交申请，不付款，不下单，不生成法律、税务、合规或投资结论。所有政策机会都必须经过人工来源复核；缺少权威来源时只能作为观察或待复核线索。
