# 统一研究数据总线

日常用户先读 `QuickStart.md`。本文件用于排查和维护 PFIOS、行研系统、消费行为/持仓数据、独立验证系统、FIFA/TAB 研究系统、政府文件/政策解读系统之间的输入、输出和数据互通。

最常用三件事：

| 目标 | 命令 |
| --- | --- |
| 一次性同步全部系统 | `$PFI_OS_HOME/scripts/syncResearchSystemsOnce.sh` |
| 处理任意聊天框提交的待办 | `$PFI_OS_HOME/scripts/researchBusApi.sh process --system-name ResearchBus --limit 100 --json` |
| 查看共享库健康状态 | `$PFI_OS_HOME/scripts/syncResearchBus.sh --json` |
| 审计跨系统互通是否完整 | `$PFI_OS_HOME/scripts/auditResearchBusInterop.sh --json` |
| 查看或调度子系统 | `$PFI_OS_HOME/scripts/orchestrateSystems.sh status --json` |

总系统开发协调入口：

```text
$PFI_OS_HOME/docs/SystemCoordinationPlan.md
~/Downloads/量化回测分析/2026-06-05/总系统协调计划_05062026.pdf
```

公开研究和外部成熟方案吸收入口：

```text
$PFI_OS_HOME/docs/PublicResearchUpgradePlan.md
$PFI_OS_HOME/data/researchBus/PublicResearchSourceLog_20260605.json
$PFI_OS_HOME/data/researchBus/MarketFeelResearchSourceLog_20260605.json
~/Downloads/量化回测分析/2026-06-05/公开研究驱动总系统升级方案_05062026.pdf
```

该计划用于约束谁主导、谁暂停、哪些功能先合并、哪些功能等待 ACK 或外部输入。后续跨系统开发应先更新该计划或对应状态文件，再动业务功能。

## 目标

统一研究数据总线用于让 PFIOS、行研系统、消费行为/持仓数据、独立验证系统、FIFA/TAB 研究系统和政府文件/政策解读系统共享同一份可审计状态。

它解决这些问题：

- 共享数据库：`data/researchBus/ResearchBus.sqlite`
- JSON 快照：`data/researchBus/ResearchBusSnapshot.json`
- 母系统系统注册表：PFIOS 记录每个子系统的根目录、独立命令、健康检查命令、同步命令和能力
- 子系统产物索引：FIFA、政策系统、独立验证和行研系统的报告/JSON/dashboard 可被统一检索
- 行研报告正文解析成待验证任务
- PFIOS 回测结论回写给行研系统
- 持仓主数据和独立验证运行状态跨系统同步
- 持仓名称到可分析证券代码/ETF/指数代理的映射跨系统同步
- 任意聊天框上传的持仓/交易截图、视频或文字先进入候选复核队列

## 数据表

共享 schema 合约文件：

```text
$PFI_OS_HOME/docs/ResearchBusSchema.json
```

| 表 | 用途 |
| --- | --- |
| `system_state` | 每个系统的路径、状态、最后同步时间和摘要 |
| `system_registry` | 母子系统注册表，保存子系统角色、根目录、独立运行命令、健康检查命令、同步命令、能力和输出规则 |
| `system_artifacts` | 子系统产物索引，保存 FIFA、政策、独立验证、行研和 PFIOS 产出的报告、JSON、dashboard 路径 |
| `orchestration_runs` | PFIOS 母系统调度子系统的 dry-run 或实际执行记录 |
| `research_reports` | 行研 PDF、Word、Markdown、文本报告索引 |
| `validation_tasks` | 从行研报告、政策、新闻或人工研究拆出的待验证任务 |
| `pfi_os_results` | PFIOS 回测结果、风险闸门、决策质量和报告路径 |
| `holdings_master` | 统一持仓主数据表 |
| `holding_symbol_mappings` | 持仓名称到行情代码或 ETF/指数代理的映射，仅用于研究观察和情绪分析 |
| `portfolio_transactions` | 统一交易流水、待确认订单和视频候选交易证据 |
| `holding_update_candidates` | 任意聊天框上传的持仓/交易候选输入，待人工复核后再进入正式持仓 |
| `consumer_behavior_state` | 消费行为系统 SQLite 的只读内部状态摘要 |
| `independent_validation_runs` | 独立验证系统运行记录 |
| `independent_validation_shards` | 大规模验证分片计划 |
| `bus_api_requests` | 跨系统双向 API 请求、状态、响应和错误 |
| `bus_chat_inputs` | 任意对话框输入的原始文本、分类和关联请求 |

2026-06-16 起，`system_registry` 还会注册当前统一 workspace 的 canonical 系统：
`finance_ledger`、`industry_research`、`policy_intelligence`。这些记录来自
`systems/*/SYSTEM_MANIFEST.json` 的 compact adapter，只写入短摘要、样本计数、能力和下一步，
不复制 legacy 绝对路径、SQLite、账户数据、报告正文或运行缓存。
| `bus_system_outbox` | 各系统给其他系统的待读消息 |
| `bus_heartbeats` | PFIOS、行研系统、独立验证系统的心跳和能力声明 |
| `sync_events` | 同步事件和审计日志 |

## Workflow Layer 输入链路

Workflow Layer 的目标是：任何聊天、上传文件、系统请求和跨系统同步意图，先成为 ResearchBus 中可追溯的输入记录，再进入下游处理。

统一只读视图：

```python
from pfi_os.integrations import workflow_inputs_frame

frame = workflow_inputs_frame()
```

输出列：

| 字段 | 含义 |
| --- | --- |
| `workflow_input_id` | 输入记录 ID，聊天输入使用 `input_id`，直接 API 请求使用 `request_id`。 |
| `input_type` | `chat` 或 `api_request`。 |
| `source_system` | 来源系统，例如 `AI-Research-Chat`、`Shortcut`、`ChatDropbox`。 |
| `author` / `channel` | 作者和通道；直接 API 请求通道为 `api`。 |
| `raw_input` | 原始文本或请求类型。 |
| `classification` | 输入分类或请求类型。 |
| `linked_request_id` | 下游处理请求 ID。 |
| `status` | `Pending`、`Processing`、`Completed`、`Failed` 或 `PendingReview`。 |
| `attachments_json` / `payload_json` | 附件引用和机器可读 payload。 |

状态规则：

- 聊天输入创建后为 `Pending`。
- 请求开始处理时，对应聊天输入同步为 `Processing`。
- 请求成功或失败后，对应聊天输入同步为 `Completed` 或 `Failed`。
- 持仓和交易候选进入 `PendingReview` 后不会被自动覆盖为 `Completed`，必须经过确认流程才会写入正式持仓。
- 畸形 API payload 会被拒绝入队。
- dropbox 同名文件重复提交时，旧 processed 文件不会被覆盖。

## Report Evidence Layer 报告证据层

回测 Word 报告和 RunMetadata JSON 现在包含 `PFIOSReportEvidenceV1` 摘要。它把研究结论前置绑定到证据链：

| 字段 | 含义 |
| --- | --- |
| `data_quality_status` | 数据质量检查状态。 |
| `cross_validation_status` | 多源交叉校验状态。 |
| `entity.entity_status` | `TradableSymbol`、`ProxyMapped`、`MissingSymbol` 或 `MissingEntityStatus`。 |
| `workflow.workflow_input_id` | 触发本次研究的聊天/dropbox 输入编号；没有则标记为 `ManualOrLocalOnly`。 |
| `workflow.linked_request_id` | 关联 ResearchBus 请求编号。 |
| `cost_assumptions.complete` | 佣金、最低佣金、滑点、冲击成本和是否允许做空是否齐全。 |
| `risk_gate_status` | 研究风险闸门状态。 |
| `decision_quality_status` | 决策质量状态。 |
| `missing_evidence` | 缺失或需复核的关键证据。 |

当数据质量、多源校验、实体状态或成本假设缺失时，报告证据状态会降级为 `NeedsMoreEvidence`。这不会阻止生成报告，但会阻止把报告表述成高置信交易前参考。

## 最终集成审计

日常使用前可运行：

```bash
bash $PFI_OS_HOME/scripts/auditPFIIntegration.sh --no-write
```

检查范围：

| 层 | 检查内容 |
| --- | --- |
| `DataTrust` | 本地文件、数据、策略、实验和报告是否可进入证据链。 |
| `EntityRegistry` | `EntityRegistry.json/csv/md` 是否存在且 schema 正确。 |
| `WorkflowInputs` | 聊天、dropbox 和 API 请求是否可追溯。 |
| `ReportEvidence` | 新报告 RunMetadata 是否包含 `PFIOSReportEvidenceV1`。 |
| `ResearchBusInterop` | 共享 SQLite、行研桥接、独立验证、持仓和系统心跳是否互通。 |
| `NoLiveTradingBoundary` | 项目是否保持只研究、不实盘、不真实下单。 |

状态解释：

- `Pass`：该层证据链闭合。
- `Review`：存在证据缺口、环境权限限制或旧报告未升级，需要补齐后再作为日常稳定验收。
- `Fail`：存在结构损坏、明确互通失败或疑似实盘代码路径，必须先修复。

`holding_symbol_mappings` 同步时会同时生成 `PFIOSEntityRegistryV1` 摘要并写入 `system_state.summary_json`。实体状态分为：

| 状态 | 含义 |
| --- | --- |
| `TradableSymbol` | 持仓已包含可用于行情查询的代码。 |
| `ProxyMapped` | 持仓名称通过规则映射到 ETF、指数或主题代理，只能作为研究代理证据。 |
| `MissingSymbol` | 缺少可用代码且未匹配代理，不能进入回测、情绪或热点分析。 |

实体注册可导出为独立派生产物：

```text
data/entityRegistry/EntityRegistry.json
data/entityRegistry/EntityRegistry.csv
data/entityRegistry/EntityRegistry.md
```

这些文件只从持仓和代理规则生成，不覆盖 `data/holdings/HoldingsBook.json`。报告、情绪分析、热点分析和跨系统验证应优先读取 `TradableSymbol`；使用 `ProxyMapped` 时必须在报告中说明“代理标的不等于真实持仓”；`MissingSymbol` 必须停在复核队列。

## 互通审计

互通审计是判断 PFIOS、行研系统、消费行为系统和独立验证系统是否真正互通的机器可读检查。它不会下单，不会修改持仓，只读取共享库和行研桥接目录；不加 `--no-write` 时会把审计结果写入固定文件。

```bash
$PFI_OS_HOME/scripts/auditResearchBusInterop.sh --json
```

输出文件：

```text
$PFI_OS_HOME/data/researchBus/ResearchBusInteropAudit.json
```

审计覆盖：

- 共享 JSON schema 合约。
- 共享 SQLite 数据库。
- 本地母子系统注册表。
- 子系统产物索引。
- 双向 API 和消息队列。
- 任意聊天框输入同步。
- 行研报告解析为 PFIOS 待验证任务。
- PFIOS 回测结论回写行研系统。
- 消费行为系统状态同步。
- 统一持仓主数据、持仓映射和交易流水。
- 独立验证系统任意入口运行。
- 独立验证两级架构与本机 worker pool。
- 系统心跳和内部状态。
- 行研系统桥接输出。
- 行研系统 automation 脚本是否保留。

## 母子系统编排

PFIOS 是母系统，ResearchBus 是控制平面。子系统可以被母系统调度，也可以完全绕过 PFIOS 独立运行。

注册所有默认子系统：

```bash
$PFI_OS_HOME/scripts/orchestrateSystems.sh register --json
```

同步子系统产物索引：

```bash
$PFI_OS_HOME/scripts/orchestrateSystems.sh sync-artifacts --json
```

查看系统注册表、产物和最近调度记录：

```bash
$PFI_OS_HOME/scripts/orchestrateSystems.sh status --json
```

dry-run 调度 FIFA 子系统健康检查，只记录母系统将调用的命令，不打开页面：

```bash
$PFI_OS_HOME/scripts/orchestrateSystems.sh run --system FIFA-Research-System --action health --json
```

确实需要由母系统实际运行子系统时，显式加 `--execute`：

```bash
$PFI_OS_HOME/scripts/orchestrateSystems.sh run --system GovernmentPolicySystem --action health --execute --timeout-seconds 120 --json
```

## 通用聊天投递箱

投递箱路径：

```text
$PFI_OS_HOME/data/researchBus/chatInbox
```

支持文件：

- `.txt` / `.md`：全文作为对话输入。
- `.json`：支持 `content_text`、`text` 或 `message` 字段，可附带 `source_system`、`author`、`channel` 和 `attachments`。
- 附件路径建议放在投递箱子目录，例如 `attachments/holding.csv`，避免附件本身被当作一条聊天输入处理。

持仓/交易候选附件自动解析：

| 格式 | 处理方式 |
| --- | --- |
| `.csv` | 按列名自动识别持仓或交易流水 |
| `.xlsx` / `.xls` | 按首个工作表列名自动识别持仓或交易流水 |
| `.json` | 识别 `holdings` / `positions` / `portfolio_transactions` / `transactions` / `trades` |
| `.txt` / `.md` | 如果全文是 JSON，则按 JSON 解析 |
| 图片 | 如果有 `tesseract` + `pytesseract` + `Pillow`，先 OCR；OCR 文本能解析出结构化 JSON 时进入可确认候选，否则保留 OCR 文本摘要供复核 |
| 视频 | 如果有 `ffmpeg` + OCR 运行环境，抽取少量帧后 OCR；缺依赖时进入 `NeedsRuntime`，不写正式持仓 |

处理命令：

```bash
$PFI_OS_HOME/scripts/researchBusApi.sh process-dropbox --json
```

处理结果：

- 成功文件移动到 `data/researchBus/chatInbox/processed`。
- 失败文件移动到 `data/researchBus/chatInbox/failed`，并生成 `.error.json`。
- 文本会自动分类成验证任务、持仓更新、同步请求、独立验证请求、系统优化请求或普通备注。

## 本地 HTTP/Webhook

启动入口：

```bash
$PFI_OS_HOME/scripts/researchBusWebhook.sh --port 8765
```

默认只绑定 `127.0.0.1`，不会对公网开放。

可用接口：

- `GET /health`：返回 ResearchBus 健康摘要。
- `GET /status`：返回 ResearchBus 健康摘要。
- `POST /chat`：提交自然语言文本或 JSON。
- `POST /request`：提交请求型 JSON。
- `POST /webhook`：通用入口，自动识别文本或请求。

示例：

```bash
curl -X POST http://127.0.0.1:8765/chat \
  -H 'Content-Type: application/json' \
  --data '{"text":"请验证 AAPL 的 RSI 策略","source_system":"LocalShortcut"}'
```

独立验证 checksum 示例：

```bash
curl -X POST http://127.0.0.1:8765/chat \
  -H 'Content-Type: application/json' \
  --data '{"text":"请运行十亿行独立验证 checksum 校验，每片1亿行","source_system":"LocalShortcut"}'
```

支持的自然语言规模：

| 表达 | 行数 |
| --- | ---: |
| `百万` / `one million` / `million` | 1,000,000 |
| `千万` / `ten million` | 10,000,000 |
| `一亿` / `1亿` / `hundred million` | 100,000,000 |
| `十亿` / `billion` / `亿万级` | 1,000,000,000 |

分片表达支持 `每片100万行`、`每片1亿行`、`rows_per_shard 10 million`、`per shard 1000000`。

## 常用命令

PFIOS 同步共享库、回写行研系统、批量推送验证任务：

```bash
$PFI_OS_HOME/scripts/syncResearchBus.sh --json
```

行研系统同步共享库、解析报告正文、拉取 PFIOS 和独立验证状态：

```bash
cd $PFI_AI_RESEARCH_ROOT
python3 -m src.cli research-bus-sync --json
```

同步后行研系统会生成这些持仓相关桥接文件：

| 文件 | 用途 |
| --- | --- |
| `data/report_artifacts/research_bus_bridge/HoldingsMasterFromBus.json` | 正式持仓主数据 |
| `data/report_artifacts/research_bus_bridge/HoldingSymbolMappingsFromBus.json` | 持仓名称到行情代理代码映射 |
| `data/report_artifacts/research_bus_bridge/PortfolioTransactionsFromBus.json` | 交易记录和待确认订单 |

`HoldingSymbolMappingsFromBus.json` 只用于研究观察。示例：支付宝基金名称缺少交易所代码时，系统可用黄金、半导体、银行、纳斯达克等主题 ETF 或指数代理生成情绪观察，不代表基金本身，也不生成实盘动作。

只同步消费行为系统内部状态：

```bash
$PFI_OS_HOME/scripts/syncResearchBus.sh --mode consumer --json
```

独立验证百亿行 dry-run 分片登记：

```bash
$PFI_OS_HOME/scripts/runIndependentValidation.sh run --synthetic-rows 10000000000 --rows-per-shard 100000000 --json
```

独立验证 checksum 实际分片校验。每个分片会写入 `expected_rows`、`observed_rows`、`checksum`、`checksum_algorithm` 和执行状态；如果文件缺失、格式不支持或实际行数不足，分片会标记 `Failed`：

```bash
$PFI_OS_HOME/scripts/runIndependentValidation.sh run --synthetic-rows 1000000000 --rows-per-shard 100000000 --mode checksum --json
```

独立验证本机 worker pool。该命令按 10 个分片校验百亿级合成数据，`worker_count=4`，不会把完整数据载入内存：

```bash
$PFI_OS_HOME/scripts/runIndependentValidation.sh run --synthetic-rows 10000000000 --rows-per-shard 1000000000 --mode checksum --worker-count 4 --json
```

通过任意对话框入口提交验证问题：

```bash
$PFI_OS_HOME/scripts/researchBusApi.sh submit-chat --text "请验证 600000 的 RSI 均线策略是否有效" --source-system ExternalChat --json
```

通过任意对话框入口提交持仓或交易截图路径。该命令只生成待复核候选，不会直接覆盖正式持仓：

```bash
$PFI_OS_HOME/scripts/researchBusApi.sh submit-chat \
  --text "这是今天的支付宝持仓截图，含 600000.SH，请同步到量化系统和行研系统" \
  --source-system ExternalChat \
  --attachment-path "/path/to/holding.png" \
  --json
$PFI_OS_HOME/scripts/researchBusApi.sh process --system-name ResearchBus --limit 100 --json
```

也可以使用结构化附件：

```bash
$PFI_OS_HOME/scripts/researchBusApi.sh submit-chat \
  --text "这是今天的持仓视频" \
  --attachment-json '{"path":"/path/to/video.mp4","media_type":"video/mp4","source":"chat_upload"}' \
  --json
```

结构化 CSV 示例：

```csv
symbol,name,market,position_value,quantity,updated_at
600000.SH,浦发银行,CN,12000,1000,2026-06-05
```

结构化 JSON 示例：

```json
{
  "holdings": [
    {"symbol": "600000.SH", "name": "浦发银行", "market": "CN", "position_value": 12000}
  ],
  "portfolio_transactions": [
    {"trade_date": "2026-06-05", "order_time": "14:30:00", "symbol": "600000.SH", "name": "浦发银行", "side": "买入", "order_amount": 12000}
  ]
}
```

确认结构化候选。只有候选 payload 里已经包含 `holdings` 或 `portfolio_transactions` 时才会写入正式持仓/交易；截图、视频等未解析候选会返回 `NeedsStructuredData`：

```bash
$PFI_OS_HOME/scripts/researchBusApi.sh confirm-holding-candidate \
  --candidate-id "holdingCandidate_xxx" \
  --json
```

通过任意对话框入口触发十亿级独立验证 dry-run：

```bash
$PFI_OS_HOME/scripts/researchBusApi.sh submit-chat --text "请运行十亿行独立验证，每片1亿行" --source-system ExternalChat --json
```

通过任意对话框入口触发千万级 checksum：

```bash
$PFI_OS_HOME/scripts/researchBusApi.sh submit-chat --text "请运行千万行独立验证 checksum 校验，每片100万行" --source-system ExternalChat --json
$PFI_OS_HOME/scripts/researchBusApi.sh process --system-name ResearchBus --limit 100 --json
```

行研系统任意聊天入口触发同一共享请求表：

```bash
cd $PFI_AI_RESEARCH_ROOT
python3 -m src.cli research-bus-submit --text "run hundred million rows independent validation, rows_per_shard 10 million" --json
```

行研系统任意聊天入口提交持仓或交易附件：

```bash
cd $PFI_AI_RESEARCH_ROOT
python3 -m src.cli research-bus-submit \
  --text "这是今天的支付宝持仓截图，含 600000.SH" \
  --attachment-path "/path/to/holding.png" \
  --json
```

处理 ResearchBus 待处理请求：

```bash
$PFI_OS_HOME/scripts/researchBusApi.sh process --system-name ResearchBus --limit 100 --json
```

行研系统提交和处理请求：

```bash
cd $PFI_AI_RESEARCH_ROOT
python3 -m src.cli research-bus-submit --text "同步 PFIOS 和行研系统状态" --json
python3 -m src.cli research-bus-process --system-name AI-Research-System --limit 100 --json
```

准实时循环入口：

```bash
RESEARCH_BUS_WATCH_INTERVAL_SECONDS=30 $PFI_OS_HOME/scripts/watchResearchBus.sh
```

```bash
cd $PFI_AI_RESEARCH_ROOT
RESEARCH_BUS_WATCH_INTERVAL_SECONDS=30 scripts/watch_research_bus.sh
```

跨系统一次性总控同步入口。该入口会串行处理投递箱、ResearchBus 请求、PFIOS 同步、行研系统请求和行研系统同步，运行完即退出：

```bash
$PFI_OS_HOME/scripts/syncResearchSystemsOnce.sh
```

macOS LaunchAgent 后台托管配置：

```bash
$PFI_OS_HOME/scripts/installResearchBusLaunchAgent.sh install
$PFI_OS_HOME/scripts/installResearchBusLaunchAgent.sh load
$PFI_OS_HOME/scripts/installResearchBusLaunchAgent.sh status
```

安装器会生成：

```text
~/Library/Application Support/PFIOS/researchBusSyncRunner.sh
~/Library/LaunchAgents/com.pfi_os.researchbus.sync.plist
```

如果当前工程位于 `Documents` 且 macOS 后台任务没有权限，LaunchAgent 可能报 `Operation not permitted`。当前机器已经验证：runner 可以直接手动执行，但 launchd 后台写入 `Documents` 下日志/数据库会被 TCC 拦截。此时先执行：
runner 已加入单步超时保护，后台失败不会无限卡住；但如果没有系统授权，launchd 仍不应长期加载。

```bash
$PFI_OS_HOME/scripts/installResearchBusLaunchAgent.sh unload
```

然后在系统设置里给后台任务访问权限，或继续使用 `syncResearchSystemsOnce.sh` / `watchResearchSystems.sh`。

## 当前验证结果

2026-06-07 当前实测：

- PFIOS 总集成审计：`Pass`，`6 Pass / 0 Review / 0 Fail`。
- ResearchBusInterop：`Pass`，`ResearchBusInteropAuditV1` 当前 `15 Pass / 0 Warn / 0 Fail`。
- ResearchBus SQLite：审计读取入口已支持 sandbox 只读目录；普通 `mode=ro` 探测失败时，会回退到 `mode=ro&immutable=1`，避免 WAL/SHM 写目录权限导致误判。
- 独立验证 worker pool：已记录 `10,000,000,000` 行合成 checksum，10 个分片，`execution_tier=local_worker_pool`，`worker_count=4`，状态 `Completed`。
- DataTrust：`Pass`，旧实验缺失的样本外和 walk-forward 验证已明确记录为 `InsufficientData`，不得解读为验证通过。

2026-06-05 当前实测：

- 跨系统互通审计：`ResearchBusInteropAuditV1` 当前 `status=Pass`，`15 Pass / 0 Warn / 0 Fail`。
- 审计表计数：`system_registry=5`，`system_artifacts=253`，`orchestration_runs=1`，`research_reports=47`，`validation_tasks=10149`，`pfi_os_results=30`，`holdings_master=28`，`holding_symbol_mappings=28`，`portfolio_transactions=1117`，`consumer_behavior_state=2`，`independent_validation_runs=4`，`independent_validation_shards=130`。
- 子系统注册表：已登记 `PFIOS`、`AI-Research-System`、`FIFA-Research-System`、`GovernmentPolicySystem` 和 `IndependentValidation`。
- 子系统产物索引：已索引 253 个产物，其中 FIFA 41 个、政府/政策系统 113 个、IndependentValidation 73 个。
- 母系统编排记录：已 dry-run 调度 FIFA 子系统健康检查，记录命令 `./scripts/verify_fifa_automation_readiness.sh --hermetic`，未实际打开页面。
- PFIOS 同步：行研报告 18 份，PFIOS 结果 30 条，持仓 28 条，交易流水 23 条。
- 行研系统同步：发布报告 18 份，拉取 PFIOS 结果 30 条，拉取验证任务 1000 条，拉取独立验证运行 2 条，拉取消费行为状态 2 条，拉取持仓候选 0 条。
- 消费行为系统只读同步：发现 2 个 `consumption.sqlite` 来源库并写入 `consumer_behavior_state`。
- 通用聊天投递箱：`.txt/.md/.json` 文件可写入 `bus_chat_inputs` 并自动生成 API 请求。
- CLI 附件入口：`submit-chat --attachment-path` 可生成 `holding_update_candidates`，状态为 `PendingReview`，不会写入 `holdings_master`。
- 结构化候选确认：`confirm-holding-candidate` 可把已解析 `holdings` 写入正式 `HoldingsBook`，把已解析 `portfolio_transactions` 写入确认交易 CSV 并同步 ResearchBus；未解析图片/视频候选返回 `NeedsStructuredData`。
- 结构化附件自动解析：PFIOS CLI 和行研 CLI 提交 CSV 附件均已临时库验证，候选 parser 状态为 `Parsed`，确认后状态 `Applied`。
- 图片/视频媒体解析：当前机器缺少 `tesseract/pytesseract/ffmpeg`，媒体候选会标记 `NeedsRuntime`；测试已覆盖缺依赖 fail-closed 和 OCR 文本为结构化 JSON 时的确认链路。
- 本地 HTTP/Webhook：`POST /chat` 已通过本机 curl smoke，成功写入 `bus_chat_inputs` 和待处理请求。
- 研究总线页面：PFIOS 已新增 `研究总线` 功能区，可查看请求、对话输入、心跳、系统状态和投递箱路径。
- 独立验证 dry-run：`1,000,000,000` 行，按每片 `100,000,000` 行生成 10 个分片。
- 独立验证 checksum：合成数据 1,000 行、每片 400 行生成 3 个分片，全部 `Completed`，每片均写入 `observed_rows` 和 `sha256` 校验码。
- 对话触发独立验证 checksum：`请运行十亿行独立验证 checksum 校验，每片1亿行` 自动生成 `1,000,000,000` 行、10 个分片，运行状态 `Completed`。
- 双向 API smoke：PFIOS 侧 `submit-chat` 自动生成验证任务并完成请求；行研侧 `pull_pfi_os_results` 请求完成并回写响应。
- PDF 正文解析：PFIOS venv 已加入 `pypdf`，本机同步实测 `warnings=[]`，验证任务从 PDF 正文生成。
- 对话触发独立验证 smoke：`请运行十亿行独立验证，每片1亿行` 自动生成 `1,000,000,000` 行、10 个分片的 dry-run 计划。
- 准实时 watch smoke：PFIOS 和行研系统 watch 脚本并发各跑 1 轮通过；SQLite 已设置 `busy_timeout=30000` 降低并发写入锁冲突。
- 本轮新增测试：PFIOS 侧 ResearchBus/API/持仓簿相关测试 `41 passed in 83.09s`。
- 本轮新增测试：行研系统 bridge 测试 `6 tests OK`，覆盖附件保存、checksum、千万级、hundred million 规模和共享请求 payload。
- 首页新增 `大数据模拟` 功能区，直接调用 `run_independent_validation` 并写入 `independent_validation_runs` / `independent_validation_shards`。
- 行研系统 `research-bus-submit --text` 现在会把 checksum 和规模参数写入与 PFIOS 相同的 `bus_api_requests.payload_json`。

## 限制

- PDF 如果是扫描图片，仍需要 OCR；当前没有加入 OCR。
- 扫描版 PDF 已加入可选 OCR 探测路径；当前机器没有 `tesseract/pytesseract/fitz`，因此扫描件会明确标记 `OCR 引擎未配置`，不会被误判为已解析正文。
- 独立验证系统当前完成的是两级架构：manifest/dry-run 分片计划 + 本机 worker pool checksum 校验。它支持百亿级计划和本机并行 smoke；还不是跨机器长期分布式 worker 集群。
- watch 脚本是轮询式准实时；LaunchAgent 安装器和 App Support runner 已提供。当前工程位于 macOS `Documents`，如果后台权限不足会触发 TCC `Operation not permitted`，需授权后再加载。
- 所有输出只用于研究验证和复盘，不接实盘交易，不下单。

## 回滚

如需回滚本轮互通状态，保留代码但移除运行数据即可：

```bash
rm -rf $PFI_OS_HOME/data/researchBus
rm -rf $PFI_OS_HOME/data/independentValidation
rm -rf $PFI_AI_RESEARCH_ROOT/data/report_artifacts/research_bus_bridge
rm -rf $PFI_AI_RESEARCH_ROOT/data/report_artifacts/pfi_os_bridge
```

不要删除正式报告、持仓簿或原始行研报告目录。
