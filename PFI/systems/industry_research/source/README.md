# AI Research Terminal

自动化权益行研、仓位操作建议与投资决策质量检查系统。

系统主线：数据采集 -> 事实整理 -> 行研判断 -> 仓位操作建议 -> 风险提示 -> PFIOS 验证队列 -> 报告生成 -> 纸面跟踪 -> 复盘迭代。

量化因子、风险规则和简化回测在本系统中是“证据与校验层”，不是产品主功能。系统的主要输出是 PDF 仓位操作报告、投资决策质量检查、风险控制说明、待验证问题和复盘材料。

## 设计原则

- 所有结论必须可追溯到 `source_name` / `source_url`。
- 自动生成内容必须区分 `fact`、`inference`、`opinion`。
- 所有 LLM 调用统一经过 `src/llm_router.py`。
- 报告 Markdown 优先，再导出 Word/PDF。
- 财务、估值、风控和研究依据必须可复现。
- 回测仅用于验证研究线索或复盘，不作为核心使用入口。
- 不在业务模块硬编码 LLM provider。

## 快速开始

```bash
cd outputs/AI-Research-System
python3 -m src.cli pfi_os-refresh --date 2026-06-03
python3 -m src.cli generate-daily --date 2026-06-03
python3 -m src.cli generate-report --date 2026-06-03
python3 -m src.cli generate-industry --industry 半导体 --date 2026-06-03
python3 -m src.cli validate-advice --strategy demo_momentum --date 2026-06-03
python3 -m src.cli report-quality-check --date 2026-06-03 --report-kind pre_open
python3 -m src.cli report-week-status --date 2026-06-03
python3 -m src.cli generate-due-reports --date 2026-06-03
python3 -m src.cli data-trust-audit --date 2026-06-06
python3 -m src.cli reconciliation-audit --date 2026-06-06
python3 -m src.cli manual-review-audit --date 2026-06-06
python3 -m src.cli entity-registry-audit --date 2026-06-06
python3 -m src.cli evidence-decision-audit --date 2026-06-06
python3 doctor.py --date 2026-06-06 --json
make doctor DATE=2026-06-06
```

生成结果在：

- `~/Downloads/行研报告/X月第Y周 DDMM-DDMM/`
- PDF 直接保存在周文件夹顶层；周文件夹只保留报告 PDF。
- Markdown、source log、图表和验证附件保存在项目内部 `data/report_artifacts/对应周文件夹/`，不写入 Downloads 周文件夹。
- PFIOS 验证附件保存在 `data/report_artifacts/对应周文件夹/_pfi_os/`，包括 `thesis_queue_YYYY-MM-DD.csv`、`validation_results_YYYY-MM-DD.csv` 和 `validation_summary_YYYY-MM-DD.json`。
- 每周标准产出 22 份 PDF：5 个交易日 * 4 份日报/K线报告 + 周一报告 + 周五报告。

## Data Trust Layer

`data-trust-audit` 是只读审计入口，用来检查行研系统现有 source log、报告伴随文件、支付宝持仓/交易文件、ResearchBus bridge、PFIOS bridge、policy bridge 和 automation health 的证据状态。

```bash
python3 -m src.cli data-trust-audit --date 2026-06-06
python3 -m src.cli data-trust-audit --date 2026-06-06 --json
```

输出位置：

- `data/report_artifacts/system_audit/data_trust_audit_YYYY-MM-DD.json`
- `data/report_artifacts/system_audit/data_trust_audit_YYYY-MM-DD.csv`
- `data/report_artifacts/system_audit/data_trust_audit_YYYY-MM-DD.md`
- `data/report_artifacts/system_audit/data_trust_audit_YYYY-MM-DD.pdf`

状态口径：

- `RAW_IMPORTED`：原始导入证据，只能保留追溯。
- `PARSED_CANDIDATE`：已解析候选证据，可以辅助研究。
- `NEEDS_REVIEW`：需要人工复核或更强来源确认。
- `USER_CONFIRMED`：用户确认或官方导出来源。
- `RECONCILED`：已具备本审计要求的伴随证据。
- `ARCHIVED`：已归档历史证据。
- `REJECTED`：失败、冲突或不可用证据。

该命令不会刷新 moomoo、OpenD、支付宝、政策系统或 ResearchBus，不生成买入/卖出指令，不改变现有日报、周报、K 线报告生产口径。

## Reconciliation Layer

`reconciliation-audit` 是只读自动对账入口，用来检查 Data Trust、source log、Markdown、PDF、ResearchBus bridge、PFIOS bridge、policy bridge、automation health 和 `HANDOFF.md` 之间是否互相支持。

```bash
python3 -m src.cli reconciliation-audit --date 2026-06-06
python3 -m src.cli reconciliation-audit --date 2026-06-06 --json
```

输出位置：

- `data/report_artifacts/system_audit/reconciliation_audit_YYYY-MM-DD.json`
- `data/report_artifacts/system_audit/reconciliation_audit_YYYY-MM-DD.csv`
- `data/report_artifacts/system_audit/reconciliation_audit_YYYY-MM-DD.md`
- `data/report_artifacts/system_audit/reconciliation_audit_YYYY-MM-DD.pdf`

对账结果使用 `pass / warn / fail`：

- `pass`：当前文件链条一致，可进入下一层审计。
- `warn`：可以观察，但需要人工复核或更强证据。
- `fail`：对应证据链不能支撑可执行交易动作，必须先修复或降级。

该命令不会生成报告、不会刷新行情、不会读取交易账户、不会修改 ResearchBus；它只比较本地现有文件和审计产物。

## Manual Review Queue

`manual-review-audit` 把 Data Trust 和 Reconciliation 中的 `NEEDS_REVIEW`、`REJECTED`、`warn`、`fail` 转成可处理的人工复核队列。

```bash
python3 -m src.cli manual-review-audit --date 2026-06-06
python3 -m src.cli manual-review-audit --date 2026-06-06 --json
```

输出位置：

- `data/report_artifacts/system_audit/manual_review_queue_YYYY-MM-DD.json`
- `data/report_artifacts/system_audit/manual_review_queue_YYYY-MM-DD.csv`
- `data/report_artifacts/system_audit/manual_review_queue_YYYY-MM-DD.md`
- `data/report_artifacts/system_audit/manual_review_queue_YYYY-MM-DD.pdf`

优先级：

- `P0`：阻断可执行交易支持，必须先处理或有证据地降级。
- `P1`：进入人工复核后才能用于正式决策支持。
- `P2`：工作流、文档或低风险质量问题。

涉及支付宝、视频候选、持仓、待确认订单和账户证据的项目会自动标记 `user_confirmation_required=true`。这类项目必须等用户确认后才能进入持仓事实或交易依据。

## Entity Registry / Alias Map

`entity-registry-audit` 从现有本地证据中生成统一实体注册表和别名映射表。

```bash
python3 -m src.cli entity-registry-audit --date 2026-06-06
python3 -m src.cli entity-registry-audit --date 2026-06-06 --json
```

输出位置：

- `data/report_artifacts/system_audit/entity_registry_YYYY-MM-DD.json`
- `data/report_artifacts/system_audit/entity_registry_YYYY-MM-DD.csv`
- `data/report_artifacts/system_audit/alias_map_YYYY-MM-DD.csv`
- `data/report_artifacts/system_audit/entity_registry_YYYY-MM-DD.md`
- `data/report_artifacts/system_audit/entity_registry_YYYY-MM-DD.pdf`

当前 v1 覆盖：

- 金融标的 / 基金
- 行研报告
- 数据源
- 政策文件
- 账户
- 系统
- 策略
- 验证任务
- 验证运行
- 复核队列项目
- 系统审计产物

Alias Map 会把中文名、英文名、代码、quote code、source URL、holding id、run id、task id、报告文件名等统一映射到稳定实体。当前使用 `alias_scope + normalized_alias` 判定冲突：不同实体类型的同名 alias 不互相误报；金融标的按市场作用域判定，ResearchBus 的 `CN` 代码会优先使用 watchlist 中已有的 `SSE/SZSE` 口径。若同一作用域内同一 alias 指向多个实体，会标记为 `Conflict` 并进入后续复核。

## Evidence Decision Matrix

`evidence-decision-audit` 把 Data Trust、Reconciliation、Manual Review、Entity Registry 和 Alias Map 冲突统一成证据等级和决策等级矩阵。

```bash
python3 -m src.cli evidence-decision-audit --date 2026-06-06
python3 -m src.cli evidence-decision-audit --date 2026-06-06 --json
```

输出位置：

- `data/report_artifacts/system_audit/evidence_decision_matrix_YYYY-MM-DD.json`
- `data/report_artifacts/system_audit/evidence_decision_matrix_YYYY-MM-DD.csv`
- `data/report_artifacts/system_audit/evidence_decision_matrix_YYYY-MM-DD.md`
- `data/report_artifacts/system_audit/evidence_decision_matrix_YYYY-MM-DD.pdf`

证据等级：

- `FACT`：可追溯到本地来源文件、审计结果或明确事实。
- `INFERENCE`：基于多个事实或规则推导，需要保留假设。
- `OPINION`：主观判断，不能作为可执行决策证据。
- `OBSERVATION`：候选、弱证据、缓存、视频可见或待确认信息，只能作为研究观察。

决策等级：

- `Actionable`：可进入研究证据链，但不等于交易批准。
- `Watch`：需要更强证据或人工复核。
- `Observe`：低风险背景或归档信息。
- `Reject`：失败、缺失、冲突或不可用证据，阻断可执行交易支持。

该命令不会修复上游阻断，也不会提高任何证据等级；它只把所有关键结论集中到一张可审计矩阵，供后续 Report Layer、质量门禁和总系统整合使用。

## Report Layer

`report-layer-audit` 把 Evidence Decision Matrix 转换成正式报告质量门禁和结论上限。

```bash
python3 -m src.cli report-layer-audit --date 2026-06-06
python3 -m src.cli report-layer-audit --date 2026-06-06 --json
```

输出位置：

- `data/report_artifacts/system_audit/report_layer_audit_YYYY-MM-DD.json`
- `data/report_artifacts/system_audit/report_layer_audit_YYYY-MM-DD.csv`
- `data/report_artifacts/system_audit/report_layer_audit_YYYY-MM-DD.md`
- `data/report_artifacts/system_audit/report_layer_audit_YYYY-MM-DD.pdf`

结论上限：

- `EvidenceChainReady`：审计链未发现系统级阻断。
- `ObservationOnly`：存在弱证据，只能作为观察或证据缺口。
- `ResearchOnlyBlocked`：存在 `P0`、`Reject` 或 blocker，正式报告只能用于研究复盘和缺口清单。
- `NoFormalResearchUse`：Evidence Decision Matrix 缺失或不可读。

该层已经接入 `src.reporting.quality_gate.run_report_quality_gate()`。生成正式报告时，Report Layer issue 会进入质量门禁；旧日期如果没有 Report Layer 或 Evidence Matrix，不会凭空生成阻断。

详见：`docs/ReportLayer.md`。

## Codex Workflow Layer

Codex Workflow Layer 提供跨 Run、跨 agent、跨 automation 的固定工作流入口，降低上下文压力并减少手工命令错误。

核心文件：

- `AGENTS.md`
- `docs/RunContract.md`
- `docs/CodexWorkflowLayer.md`
- `doctor.py`
- `setup.sh`
- `Makefile`

常用命令：

```bash
./setup.sh 2026-06-06
python3 doctor.py --date 2026-06-06 --json
python3 doctor.py --date 2026-06-06 --write-report --json
make doctor DATE=2026-06-06
make test-monitoring
make audit-stack DATE=2026-06-06
make test
make clean-cache
```

正式产物：

- `data/report_artifacts/system_audit/codex_workflow_doctor_YYYY-MM-DD.json`
- `data/report_artifacts/system_audit/codex_workflow_doctor_YYYY-MM-DD.md`
- `data/report_artifacts/system_audit/codex_workflow_doctor_YYYY-MM-DD.pdf`
- `data/report_artifacts/system_audit/codex_workflow_layer_YYYY-MM-DD.pdf`

该层不刷新外部数据、不打开应用、不生成交易动作，只检查项目文件、运行时、CLI 命令、审计产物和脚本可执行性。

## 目录

```text
00_prompts/       LLM 提示词
01_templates/     Markdown/Excel 模板
src/reporting/paths.py  下载目录与周文件夹输出规则
config/           数据源、风控、策略配置
data/sample/      可复现样例数据
src/              系统源码
tests/            单元测试
```

## 核心模块

| 模块 | 作用 |
| --- | --- |
| collectors | 行情、财务、公告、新闻、宏观、行业数据采集 |
| factors | 价格、成交量、估值、成长、质量、盈利、风险、情绪、政策、行业因子 |
| advice | 买入/卖出/等待确认/观望建议、Volume、触发条件、失效条件、风险提示 |
| strategies | 研究信号和规则解释 |
| risk | 回撤、权重、行业、杠杆、黑名单等纪律约束 |
| portfolio | 研究权重汇总与主题暴露 |
| backtesting | 可选验证层，用于纸面交易、复盘和研究可信度校验 |
| monitoring | 数据缺失、策略异常、风控触发监控 |
| reporting | PDF 报告、核心观察清单和可审计证据表 |

## 主要报告

- 每日仓位操作报告：仓位操作建议、盘前/盘中/盘后对比复盘、关键事实事件、市场结构、研究可信度、PFIOS 验证、操作纪律、反方校验和末尾账户附图。
- 行业跟踪报告：核心观点、行业表现、产业链/供需变化、估值与财务、风险变化、研究复盘。
- 可选验证附件：建议标的的历史表现、收益曲线和风险指标，用于复盘，不替代行研判断。

## 报告结构

日报、周报和 K 线报告统一采用简明商务结构：

- 仓位操作建议：显性列出 `Name`、`Position`、`Volume`、`Volume依据`、复合质量分、说服力、操作结论、建议金额、持仓金额、持有收益率、待确认金额、执行窗口、依据和风险点；买入行标红，卖出行标绿。中证银行和科创50属于用户可交易观察对象，不按纯指数背景移出核心操作表。
- 对比复盘：盘中对比盘前，盘后对比盘前和盘中，周五对比本周已生成报告，并输出逻辑总结和规则优化结论。
- 关键事实、事件与市场结构：事实/推论/观点分层，事件时间必须包含年月日；日报/周报必须包含 A 股板块热力图与气泡图，热力图必须使用浅色背景和深色文字，每格显示对象名称，气泡图必须说明上下横轴、左右纵轴、气泡大小、颜色和对象标签。
- 研究可信度与 PFIOS 验证：全自选池进入基础验证队列；估值缺失必须使用 ETF/指数代理估值或个股 PE/PB/行业估值分位补齐口径；信号质量矩阵放在本板块，和研究可信度合并阅读，不再占用仓位操作建议空间。
- 操作纪律与反方校验：检查待确认订单、现金缓冲、情绪化追涨补跌、反方观点和推翻条件。
- 复合判断质量：周报不得把收盘价、涨跌幅、成交额作为独立结论表；这些字段只能进入量价证据，并必须同时展示复合质量分、策略胜率代理、概率等级、高概率盈利条件、事件原文核验、PFIOS 风险闸门、操作策略和失败动作。
- 事件催化核验：政府/政策/新闻/公告事件必须有原文核验、原文抓取状态、独立爬虫请求/报告链路、误读风险、来源链路和操作影响；未完成政府文件解读系统原文抓取或仅有缓存/标题的事件，只能作为风险背景，不能提高买入分、买入金额或 Volume。
- 持仓与支付宝历史交易附图：三张持仓/账户图统一放在报告末尾，历史交易流显示上一周买入、卖出、退款/其他和现金流净流入。

## 报告深度标准

行业跟踪报告必须达到产业生态图谱级深度，至少覆盖：产业生态分层、公司映射、政策映射、研究映射和证据链检查。

每日、周度和 K 线报告必须引用行研结论、政策催化、账户/行情证据或 PFIOS 验证需求。买入/卖出建议必须同时显示 Volume、持仓依据、风险点和反方校验；证据不足的对象降为等待确认或观望。

K 线研究观察报告是技术面训练和证据检查附件，不作为独立交易依据。正式 K 线 PDF 必须不少于 50 页，至少覆盖 7 个观察标的槽位：3 个承接观察或观望替代、3 个降暴露风险观察或观望替代、1 个中性观望；每个重点标的必须覆盖 MA、EMA、BOLL、MACD、VOL、RSI、KDJ 和混合指标分析。

PFIOS 在本系统中只作为验证层：需要输出回测对象、样本区间、成本假设、参数稳定性、样本外验证、walk-forward 结果和研究风险闸门状态。验证不足时，研究结论必须降级为观察或待验证。

PFIOS 刷新命令：

```bash
python3 -m src.cli pfi_os-refresh --date 2026-06-03
```

统一研究数据总线同步命令：

```bash
python3 -m src.cli research-bus-sync --json
```

共享 SQLite：`<PFI_HOME>/data/researchBus/ResearchBus.sqlite`

行研系统 outbox：`data/report_artifacts/research_bus_bridge/`

PFIOS 回写 outbox：`data/report_artifacts/pfi_os_bridge/PFIOSResults.json`

该同步会发布行研报告索引，解析 PDF、Markdown 和 TXT 正文生成待验证任务，拉取 PFIOS 回测结果，并拉取独立验证系统运行状态。

PFI schema 合约：`<PFI_HOME>/docs/ResearchBusSchema.json`

该 schema 是统一研究数据总线的字段和请求类型来源。后续新聊天、其他 agent 或 automation 修改字段时，应同时更新 PFIOS 与本系统 bridge。

行研系统也支持研究总线双向 API：

```bash
python3 -m src.cli research-bus-submit --text "同步 PFIOS 和行研系统状态" --json
python3 -m src.cli research-bus-process --system-name AI-Research-System --limit 100 --json
python3 -m src.cli research-bus-heartbeat --system-name AI-Research-System --status Ready
```

行研聊天入口也可以触发独立验证系统。支持 `百万`、`千万`、`一亿`、`十亿`、`亿万级`、`million`、`hundred million`、`billion`，并会把 `synthetic_rows`、`rows_per_shard` 和 `checksum` 请求类型写入共享 SQLite。

```bash
python3 -m src.cli research-bus-submit --text "请运行千万行独立验证 checksum 校验，每片100万行" --json
python3 -m src.cli research-bus-submit --text "run hundred million rows independent validation, rows_per_shard 10 million" --json
```

真正执行独立验证请求由 PFIOS / ResearchBus 处理：

```bash
<PFI_HOME>/scripts/researchBusApi.sh process --system-name ResearchBus --limit 100 --json
```

准实时同步循环：

```bash
RESEARCH_BUS_WATCH_INTERVAL_SECONDS=30 scripts/watch_research_bus.sh
```

这些命令只写共享研究数据总线和本地 outbox，不触发实盘交易、不下单、不读取交易账户密码。

规则：

- 报告生成前应先运行 `pfi_os-refresh`，让可信度评分和验证队列表引用同一天的验证结果。
- 涉及模拟时，Monte Carlo 不少于 100,000 次；全流程从数据读取到验证结果写入不少于 2 次。
- 输出状态为 `NeedsMoreEvidence`、`DataQualityReview`、`DoNotUse` 或风险闸门 `Blocked` 时，买入/卖出候选不得直接执行；买入类 Volume 必须归零或转为等待确认/观望，并在风险点中说明原因。

报告质量闸门：

```bash
python3 -m src.cli report-quality-check --date 2026-06-03 --report-kind pre_open
```

质量闸门会检查：

- 对应 PDF 和 Markdown 辅助产物是否存在。
- 对应 source log JSON 是否存在，且每条来源包含 `source_name`、`source_url`、`fetch_time` 和 `data_version`；正式报告正文不得出现“来源清单”板块。
- 正式报告是否包含仓位操作建议、对比复盘、事实/推论/观点、研究可信度与 PFIOS 验证、反方观点、持仓纪律检查和末尾持仓附图。
- 事实/推论/观点三层是否都有实质内容，反方观点是否不是空表或占位，持仓纪律检查是否覆盖待确认订单、现金缓冲和情绪化交易风险。
- 支付宝执行金额闸门是否生效：当日账户更新缺失/未确认时，所有买入/卖出候选必须标记为账户待更新候选，且 `Volume` 和建议金额必须为 0。
- PFIOS 动作闸门是否生效：同一标的若为 `NeedsMoreEvidence`、`DataQualityReview`、`DoNotUse` 或风险闸门 `Blocked`，买入类建议不得出现非零 `Volume`，最终规则必须是取消、观望、等待或暂停，而不是继续保留可执行买入。
- 日报/周报是否真实包含 A 股板块热力图与气泡图，且图表说明覆盖板块对象名称、底部横轴、顶部横轴、左侧纵轴、右侧纵轴、气泡大小、颜色和对象标签。
- 核心仓位操作表是否包含复合质量分、说服力和操作结论；信号质量矩阵是否放在研究可信度板块；热力图是否明确采用浅色背景，避免影响阅读。
- 事件催化表每条非占位事件是否包含完整年月日和来源当地时区；缺日期或缺时区的事件行会被质量门禁拒绝。
- 周报是否拒绝裸行情结论表和低价值简化事件表，是否包含概率等级、高概率盈利条件、事件原文核验、复合质量分、策略胜率代理、操作策略和失败动作。
- K 线报告是否避免重复日报/周报市场结构图、来源清单和泛化事件板块。
- 政府文件解读系统 policy bridge 是否完成刷新；若政策状态缺失、刷新失败/超时、命中政策事件但无原文 URL 核验、原文抓取状态、独立爬虫请求路径、政策系统报告路径或操作影响分析，质量门禁失败。
- K 线报告是否不少于 50 页，是否包含 7 个观察槽位、MA/EMA/BOLL/MACD/VOL/RSI/KDJ 和混合指标分析；每个指标段必须给出当前读数、参考标准、判断结论和建议操作。
- 是否出现旧的 `sell_or_avoid` 等过时动作措辞。
- Research Confidence Score 是否被 PFIOS 状态正确压低。
- `_pfi_os` 队列、结果和 summary 是否存在。
- Downloads 周文件夹是否只包含标准 22 份报告 PDF 的允许命名。
- `generate-daily`、`generate-weekly`、`generate-kline` 和对应 suite 命令默认会先检查 Australia/Sydney 报告时间；同日未到点或未来日期不得生成，suite 命令只跳过未到点报告。
- suite 命令只处理 `--date` 当天已到点的报告：`generate-daily-suite` 不处理历史日期，`generate-weekly-suite` 只在周一生成周一报告、周五生成周五报告，不在周中/周五后回填本周周一报告。
- `generate-daily`、`generate-weekly`、`generate-kline` 和对应 suite 命令默认会在生成后自动运行质量闸门；仅本地调试可加 `--skip-quality-check`。

周级报告状态：

```bash
python3 -m src.cli report-week-status --date 2026-06-03
python3 -m src.cli report-week-status --date 2026-06-03 --json
```

该命令只读，不生成、不删除报告。它会列出本周标准 22 份 PDF 的 `quality_pass`、`quality_fail`、`missing`、`future`、`present`、`historical_present` 或 `historical_missing` 状态，显示周文件夹污染问题，并只为当前已到生成时间且缺失或质量失败的报告给出下一步修复命令。

只补当天已到点缺口：

```bash
python3 -m src.cli generate-due-reports --date 2026-06-04
```

该命令会先读取 `report-week-status`，只生成报告日期等于 `--date` 且状态为 `missing` 或 `quality_fail` 的报告。它不会补跑 `historical_present` / `historical_missing`，也不会提前生成 `future` 报告。

自动化健康检查：

```bash
python3 -m src.cli automation-health --date 2026-06-04
python3 -m src.cli automation-health --date 2026-06-04 --json
python3 -m src.cli automation-health --date 2026-06-04 --strict-opend
```

该命令会检查 Python 依赖、moomoo app、OpenD 端口、自选池数据库、行情快照新鲜度、OpenD/fallback 覆盖率、支付宝当日更新状态、周目录状态和当天已到期报告质量。默认允许 OpenD 无权限后的备用行情，但会标记为 `warn` 并记录 source 分布；`--strict-opend` 会要求支持标的全部来自 OpenD，否则返回失败。结构化健康日志保存在 `data/report_artifacts/automation_logs/automation_health_YYYY-MM-DD.json`。

系统更新后的报告重生成策略：

- 只更新当天已经生成且需要按新质量闸门复核的报告。
- 同一天尚未到生成时间的盘后、K 线或周报，标记为 `future`，等待对应 automation 到点生成。
- 历史日期报告标记为 `historical_present` 或 `historical_missing`，只做记录，不按最新框架自动补跑或重生成。
- 正式补齐仍必须使用报告日期的可操作行情；行情无法补齐时应失败。

## moomoo 桌面端自选池

系统可以在报告生成前自动打开 moomoo 桌面端并同步本地自选池：

```bash
python3 -m src.cli sync-moomoo --date 2026-06-03 --quotes
python3 -m src.cli pfi_os-refresh --date 2026-06-03
python3 -m src.cli generate-daily-suite --date 2026-06-03
python3 -m src.cli generate-kline --date 2026-06-03
```

周报必须使用对应交易日日期：

```bash
python3 -m src.cli generate-weekly --date 2026-06-01 --session monday_pre_open
python3 -m src.cli generate-weekly --date 2026-06-05 --session friday_post_close
```

自动化任务固定入口：

```bash
scripts/run_report_automation.sh pre_open
scripts/run_report_automation.sh midday
scripts/run_report_automation.sh post_close
scripts/run_report_automation.sh kline
scripts/run_report_automation.sh monday_pre_open
scripts/run_report_automation.sh friday_post_close
```

该脚本会固定 Australia/Sydney 日期、选择包含 `certifi` / `matplotlib` / `reportlab` 的 Python 运行时、记录 automation log、运行自动化健康检查、检查 OpenD 监听状态、刷新支付宝更新状态和 PFIOS，再生成对应报告并只补当天已到期的缺失或质量失败报告。即使 automation 被误提前触发，CLI 到点闸门也会阻断同日未到点报告和未来日期报告。

自动化任务内部顺序：

1. 打开/同步 moomoo 自选池。
2. 运行 `python3 -m src.cli pfi_os-refresh --date 当日日期`。
3. 每日生成三份 PDF：开盘前、盘中停盘、盘后分析。
4. 每周生成两份 PDF：周一开盘前、周五关盘后。
5. 额外生成 K 线分析 PDF，用于训练技术面、基本面、价值面分析。
6. 运行 `python3 -m src.cli generate-due-reports --date 当日日期`，只补当天已到期缺口。
7. 运行 `python3 -m src.cli report-week-status --date 当日日期`，输出周目录状态。
8. 将通过质量闸门的 PDF 发送到通知渠道。

当前自动同步读取的是 moomoo 本地自选分组数据库，不会操作账户、不会修改账户、不会发送任何账户操作指令。

OpenD 行情刷新：

- 报告、周报、K线报告和验证命令默认会先同步 moomoo 自选池，再尝试通过 moomoo OpenD 刷新价格、涨跌幅、成交量、成交额。
- 研究观察报告禁止使用离线、过期或合成行情；当日行情刷新失败必须阻断报告生成并输出失败原因。
- OpenD 配置复用 `<MOOMOO_WORKBENCH_ROOT>/config.json`。
- 如果某个市场没有 OpenD 行情权限，系统会按 Yahoo Finance（美国）-> Tencent Finance Quote（港股上市平台/港区可用源）-> Sina Finance（最后兜底）的顺序补充；仍无法补齐的标的只进入观察层。
- automation 默认刷新 moomoo/OpenD；OpenD 或备用行情源无法补齐当日可操作价格时，报告视为不可用。

## 支付宝实盘账户账本

支付宝账户数据不通过登录密码、支付密码或验证码自动抓取。系统使用本地私有账本接入：

```text
data/private/alipay/current_positions.csv      当前确认持仓
data/private/alipay/trade_ledger.csv           已确认交易流水
data/private/alipay/pending_orders.csv         待确认订单
data/private/alipay/daily_update_log.csv       每日更新记录
```

执行初始化：

```bash
python3 -m src.cli alipay-init
```

今天先导入完整持仓快照；后续每天优先上传支付宝基金交易明细截图、持仓截图或官方交易明细 CSV。基金订单在支付宝中存在确认延迟，因此系统分为：

- 预估持仓：根据当天提交的买入/卖出金额先记录到 `pending_orders.csv`。
- 确认持仓：确认份额、确认净值、手续费出来后写入 `trade_ledger.csv` 并修正 `current_positions.csv`。

记录一次当天已更新：

```bash
python3 -m src.cli alipay-record-update \
  --date 2026-06-03 \
  --source-type video \
  --source-path "<PRIVATE_SCREEN_RECORDING_OR_ALIPAY_MEDIA>" \
  --status needs_confirmation \
  --notes "今日支付宝持仓/交易视频已收到，待截图或导出文件确认。"
```

统计哪些交易日更新、哪些交易日缺失：

```bash
python3 -m src.cli alipay-update-status --start-date 2026-06-03 --end-date 2026-06-05
```

导入支付宝官方交易明细 CSV：

```bash
python3 -m src.cli alipay-import-transactions \
  --path "<PRIVATE_ALIPAY_TRANSACTION_CSV>"
```

导入后系统会把全量原始交易明细保存到 `data/private/alipay/raw_transactions_*.csv`，把基金买入、卖出、退款、转换写入 `trade_ledger.csv`，把仍在确认中的基金订单写入 `pending_orders.csv`。

上传支付宝基金交易明细截图、持仓截图、视频或 CSV 后，必须先更新 `data/private/alipay/` 私有账本，然后立即向用户展示当前记录的持仓情况，并明确区分确认持仓、截图/视频候选持仓、待确认订单。

报告生成时优先读取 `data/private/alipay/current_positions.csv`；如果私有账本为空，才回退到截图/视频候选持仓，再回退到 `data/sample/holdings.csv`。自动化报告必须把账户数据新鲜度作为研究依据：当日截图/交易明细未更新时，不得把研究观察状态当作完整实盘结论。

所有日报、周报和 K 线报告必须在末尾包含三张持仓图：账户关键指标、持仓金额/持有收益/待确认订单、建议动作与上一周支付宝历史交易流。核心仓位操作建议表必须包含单个标的的持仓金额、持仓收益率、待确认金额、Position 和 Volume。

报告命名：

- `1. DDMMYYYY_盘前报告.pdf`
- `2. DDMMYYYY_盘中报告.pdf`
- `3. DDMMYYYY_盘后报告.pdf`
- `4. DDMMYYYY_K线分析报告.pdf`
- `DDMMYYYY_周一报告.pdf`
- `DDMMYYYY_周五报告.pdf`

旧命名历史报告只作为状态记录兼容，不会被新框架自动重命名、补跑或重生成；当天已生成报告和未来报告统一使用新命名。

周文件夹命名示例：

- `~/Downloads/行研报告/6月第1周 0106-0706/`

## 真实数据接入

新增数据源时继承或复用 `src/collectors/base.py`，每条记录至少包含：

```json
{
  "source_name": "source",
  "source_url": "https://...",
  "fetch_time": "2026-06-03T10:00:00+10:00",
  "data_version": "v1",
  "raw_response": {},
  "parsed_data": {},
  "status": "ok",
  "error_message": ""
}
```

## LLM 接入

默认使用 deterministic stub，便于离线测试。生产环境可在 `config/llm.yaml` 配置 provider，但业务代码仍只调用：

```python
from src.llm_router import LLMRouter
router = LLMRouter.from_config("config/llm.yaml")
router.generate(prompt, context)
```
