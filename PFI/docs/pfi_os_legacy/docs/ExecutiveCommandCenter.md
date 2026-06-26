# Executive Command Center

总控驾驶舱是 PFI_OS 的第一入口，用来回答一个问题：当前系统是否可以继续研究，还是必须先补证据、修风险或生成报告。

它不刷新行情、不启动 Moomoo OpenD、不修改持仓、不连接实盘、不生成下单指令。

## What It Reads

| 输入 | 作用 |
| --- | --- |
| Daily Readiness | 判断日常就绪状态、核心门禁和行动项。 |
| Integration Audit | 判断 Data Trust、Entity、Workflow、Report Evidence、ResearchBus 和禁止实盘边界是否闭合。 |
| Data Trust Audit | 判断本地证据链是否有待复核或拒绝项。 |
| Company CashFlow Runtime Summary | 优先读取 compact 现金流运行摘要，汇总余额、净现金流、runway、证据缺口和行动项。 |
| Policy Intelligence Runtime Summary | 优先读取 compact 政策运行摘要，汇总政策机会、来源权威、证据缺口和行动项。 |
| Consumption Guard Runtime Summary | 优先读取 compact 消费运行摘要，汇总支出、冲动风险、固定成本、可投资现金流压力和止血行动项。 |
| Report Center | 查找最新正式 Word 研究报告和报告证据。 |

## Status Rules

| 状态 | 含义 | 处理方式 |
| --- | --- | --- |
| `ReadyForResearch` | 核心证据闭合，可以继续研究。 | 继续回测、报告、复盘或跨系统同步。 |
| `NeedsReview` | 有证据缺口或报告缺失。 | 先处理行动队列，再使用研究结论。 |
| `Blocked` | 有失败或阻断项。 | 停止使用下游结论，修复 P0 后复跑。 |


需要刷新这些低 token 状态面时，先运行：

```bash
$PFI_OS_HOME/scripts/refreshRuntimeSummaries.sh --as-of 2026-06-16
```

该命令只写四个 compact runtime summary latest 和对应日期文件，不重写完整 records、entries、opportunities、events、CSV、Markdown 或 PDF。

现金流、政策、消费三个业务子系统使用 fail-closed 汇总：`Critical`、`StopBleeding` 和 runtime `Blocked` 会阻断总控；缺余额、缺政策证据、缺消费证据、待复核和 Watch 状态会降级为 `NeedsReview`；`Actionable` 政策机会会进入行动队列，但本身不是系统故障。

## How To Use

1. 双击 `PFI_OS.app`。
2. 默认进入 `总控驾驶舱`。
3. 先看 `总控状态`。
4. 看 `业务子系统`，确认现金流、政策和消费没有缺证据或高压状态。
5. 再看 `行动队列`，优先处理 P0 和 P1。
6. 如 `Runtime Summary Sources` 仍显示 `full_snapshot`，先运行 `scripts/refreshRuntimeSummaries.sh`。
7. 打开 `证据来源`，确认每个来源都有实际文件路径。
8. 打开 `Runtime Summary Sources`，确认四个业务/value 子系统优先使用 `runtime_summary`，而不是 full snapshot。
9. 打开 `风控闸门`，确认核心门禁不是 `Fail` 或 `Blocked`。
10. 需要留档时点击页面按钮 `生成总控报告`。

命令行生成：

```bash
$PFI_OS_HOME/scripts/commandCenter.sh --output-dir data/commandCenter
```

## Outputs

```text
data/commandCenter/PFICommandCenter_DDMMYYYY.json
data/commandCenter/PFICommandCenter_DDMMYYYY.md
data/commandCenter/PFICommandCenter_DDMMYYYY.pdf
data/commandCenter/PFICommandCenter_latest.json
data/commandCenter/PFICommandCenter_latest.md
data/commandCenter/PFICommandCenter_latest.pdf
```

## Risk Boundary

总控驾驶舱只证明本地证据链和系统门禁状态，不证明策略盈利能力。

如果底层数据、报告或审计过期，页面状态只代表最近一次本地证据，不代表实时市场。

任何 `NeedsReview` 或 `Blocked` 都应降级为观察或待复核，不应作为交易前参考。

现金流、政策和消费快照只来自本地 latest 文件或本地 fail-closed fallback，不连接银行、支付、工资、税务、政府平台、支付宝、券商或实盘交易系统。

总控读取 compact runtime summary 只减少上下文和 token 压力，不绕过原始子系统的 evidence gate；需要审计明细时仍应回到 full latest 快照和原始台账。
