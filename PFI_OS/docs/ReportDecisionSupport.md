# Report Decision Support Index

报告决策支持索引用来判断每份研究报告是否足够支撑后续研究决策。

它只读取 Word 报告和 RunMetadata，不改原报告、不刷新行情、不连接实盘。

## What It Checks

| 检查项 | 作用 |
| --- | --- |
| Word 报告文件 | 确认 RunMetadata 能对应到正式报告。 |
| `PFIOSReportEvidenceV1` | 确认报告有标准证据摘要。 |
| 数据质量状态 | 确认报告引用的数据质量是否通过或可观察。 |
| 多源交叉校验 | 确认关键行情是否经过多源验证。 |
| 风险闸门 | 确认回撤、成本、稳定性、样本外和 walk-forward 证据。 |
| Decision Quality | 确认 Thesis、证据、风险、退出条件和反方观点是否完整。 |

## Status Rules

| 状态 | 含义 |
| --- | --- |
| `ContinueResearch` | 证据链较完整，可以继续研究，但仍不等于交易建议。 |
| `WatchOnly` | 只适合观察，不能升级为交易前参考。 |
| `NeedsMoreEvidence` | 缺少关键证据，必须补齐后再使用。 |
| `DoNotUse` | 存在明确拒绝项，暂停使用该报告作为研究依据。 |

## Command

```bash
$PFI_OS_HOME/scripts/reportDecisionSupport.sh --output-dir data/reportDecision
```

只读预览：

```bash
$PFI_OS_HOME/scripts/reportDecisionSupport.sh --json-only
```

## Outputs

```text
data/reportDecision/ReportDecisionSupportIndex_DDMMYYYY.json
data/reportDecision/ReportDecisionSupportIndex_DDMMYYYY.csv
data/reportDecision/ReportDecisionSupportIndex_DDMMYYYY.md
data/reportDecision/ReportDecisionSupportIndex_DDMMYYYY.pdf
data/reportDecision/ReportDecisionSupportIndex_latest.json
data/reportDecision/ReportDecisionSupportIndex_latest.csv
data/reportDecision/ReportDecisionSupportIndex_latest.md
data/reportDecision/ReportDecisionSupportIndex_latest.pdf
```

## How To Use

1. 打开 `报告中心`。
2. 进入 `证据索引` 页签。
3. 先看 `继续研究`、`需要证据`、`仅观察`、`不要使用` 数量。
4. 查看高频缺失证据。
5. 对 `NeedsMoreEvidence` 报告，优先补数据质量、多源交叉校验、参数稳定性、样本外验证和 walk-forward。
6. 需要正式留档时点击 `生成报告证据索引`，或运行命令行脚本。

## Risk Boundary

该索引判断的是“报告证据是否足够”，不判断未来收益，也不输出买入、卖出、仓位或下单指令。

如果报告本身使用的是样例数据、旧数据或缺失多源校验，索引会把它降级为 `NeedsMoreEvidence`。

`ContinueResearch` 仍然只是研究状态，不是个人金融建议。
