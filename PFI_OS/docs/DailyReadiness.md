# Daily Readiness

Daily Readiness 是 PFIOS 的日常开机前只读检查入口，用来回答：今天这个研究工作台是否可以进入研究流程，哪些数据源或本地设置还需要处理。

它不刷新行情、不启动 Moomoo OpenD、不打开 Streamlit、不修改持仓、不生成交易指令、不连接实盘交易。

## What It Checks

| 范围 | 检查重点 | 结论用途 |
| --- | --- | --- |
| Data Trust | 是否 `Pass`，是否存在 `NEEDS_REVIEW` 或 `REJECTED` | 判断本地证据链是否干净 |
| Integration Audit | 六层总集成审计是否 `Pass` | 判断母系统验证层是否闭合 |
| No Live Trading | 禁止实盘交易和真实下单边界是否仍为 `Pass` | 防止研究系统越界 |
| Report Evidence | RunMetadata 和报告证据层是否存在 | 防止报告无法追溯 |
| Latest Word Report | 是否存在最近 Word 研究报告 | 方便进入报告中心复核 |
| Provider Summary | 数据源状态、API key、Moomoo OpenD、本地包 | 区分系统可用和真实数据待配置 |
| Health Summary | 本地启动器、脚本、文档、报告目录 | 发现本机使用阻碍 |

## Status Meaning

| 状态 | 含义 | 操作 |
| --- | --- | --- |
| `ReadyForResearch` | 核心研究证据门禁通过，可以进入研究流程 | 仍需检查具体报告的数据质量、交叉校验和风险门禁 |
| `NeedsReview` | 至少一个核心门禁未通过 | 先处理行动项，不要使用结果支持真实决策 |
| `Blocked` | 出现失败或阻断项 | 停止使用相关研究结论，先修复审计失败 |

Provider API key 缺失或 Moomoo OpenD 未启动通常不是平台阻断项，而是真实数据使用前的准备项。只要核心门禁通过，系统仍可用于 Sample、CSV、历史报告复盘和非联网研究。

## Run Command

只读快速检查：

```bash
cd $PFI_OS_HOME
PYTHONPYCACHEPREFIX=/private/tmp/pfi_os-pycache PYTHONPATH=src .venv/bin/python -m pfi_os.examples.daily_check
```

生成正式审计产物：

```bash
PYTHONPYCACHEPREFIX=/private/tmp/pfi_os-pycache PYTHONPATH=src .venv/bin/python -m pfi_os.examples.daily_check --output-dir data/systemAudit
```

也可以使用脚本入口：

```bash
$PFI_OS_HOME/scripts/dailyCheck.sh --output-dir data/systemAudit
```

如果需要联网真实数据 smoke，再追加 `--network`：

```bash
$PFI_OS_HOME/scripts/dailyCheck.sh --output-dir data/systemAudit --network
```

## Outputs

正式输出位于 `data/systemAudit`：

| 文件 | 用途 |
| --- | --- |
| `PFIOSDailyReadiness_DDMMYYYY.json` | 机器可读完整状态 |
| `PFIOSDailyReadiness_DDMMYYYY.md` | 人工阅读摘要 |
| `PFIOSDailyReadiness_DDMMYYYY.pdf` | 轻量正式检查页 |

2026-06-07 当前已生成：

- `data/systemAudit/PFIOSDailyReadiness_07062026.json`
- `data/systemAudit/PFIOSDailyReadiness_07062026.md`
- `data/systemAudit/PFIOSDailyReadiness_07062026.pdf`

## Current Result

2026-06-07 当前实测：

- Daily Readiness：`ReadyForResearch`。
- Core Gates：DataTrust、IntegrationAudit、NoLiveTradingBoundary、ReportEvidence、LatestWordReport 均为 `Pass`。
- Provider Summary：`ready=5`，`needs_config=3`，`needs_package=0`，`needs_opend=0`，`other=0`。
- 主要行动项：只在实际使用相应数据源时配置 API key；使用报告前继续检查数据质量、多源交叉校验和风险门禁。

## Limits

Daily Readiness 只证明平台当天进入研究流程的前置门禁状态，不证明某个策略盈利，不证明某个标的适合交易，也不构成个人金融建议。

真实交易参考仍必须看具体报告中的数据质量、成本、滑点、冲击成本、最大回撤、样本外验证、walk-forward、策略失效条件和 Decision Quality。
