# Event Replay MVP

Event Replay 是 PFI_OS 的事件回放最小实现。它读取可复现数据湖的 manifest、replay cursor 和本地 `MarketEventLog_*.jsonl`，生成一个按 `event_time`、`event_id` 稳定排序的 replay batch。

它不是回测引擎，也不模拟订单。它只解决一个问题：把同一组不可变行情事件，以同样的顺序、同样的过滤条件、同样的分页游标交给后续三模式回测/模拟内核。

## 目的

- 降低 token 压力：后续回测、诊断和报告只引用 replay batch 摘要或文件路径，不需要反复解释原始行情文件。
- 保证复现：每个 batch 记录 manifest、cursor、asset、event window、过滤条件和输出文件。
- 支持渐进升级：先服务本地 `BarClosed` 事件，再扩展到 tick、order book、news、policy 和 portfolio event。

## 输入

默认读取：

```text
data/dataLake/DataLakeManifest_latest.json
data/dataLake/DataLakeManifest_latest_replay_cursors.json
data/marketEvents/MarketEventLog_*.jsonl
```

可用过滤条件：

| 参数 | 含义 |
| --- | --- |
| `--cursor-id` | 指定一个 replay cursor。 |
| `--dataset` | 过滤数据集，当前主要为 `market_events`。 |
| `--market` | 过滤市场，例如 `US`。 |
| `--symbol` | 过滤标的，例如 `SPY`。 |
| `--interval` | 过滤周期，例如 `1d`。 |
| `--source` | 过滤来源，例如 `sample`。 |
| `--start-after` | 只回放严格晚于该 `event_time` 的事件。 |
| `--end-at` | 只回放不晚于该 `event_time` 的事件。 |
| `--limit` | 限制本次输出事件数，用于分页和小批量调试。 |

## 运行

```bash
scripts/eventReplay.sh --output-dir data/replay
```

只生成状态、不写文件：

```bash
scripts/eventReplay.sh --json-only --limit 5
```

指定标的和窗口：

```bash
scripts/eventReplay.sh --market US --symbol SPY --interval 1d --start-after 2026-01-02T00:00:00 --output-dir data/replay
```

## 输出

```text
data/replay/EventReplay_<cursor>_DDMMYYYY.json
data/replay/EventReplay_<cursor>_DDMMYYYY.csv
data/replay/EventReplay_<cursor>_DDMMYYYY.md
data/replay/EventReplay_latest.json
data/replay/EventReplay_latest.csv
data/replay/EventReplay_latest.md
```

JSON 主要字段：

| 字段 | 含义 |
| --- | --- |
| `schema` | `PFIOSEventReplayBatchV1`。 |
| `replay_status` | `Pass`、`Review` 或 `Empty`。 |
| `selected_cursors` | 本次选中的 replay cursor。 |
| `selected_assets` | 本次读取的不可变 asset。 |
| `records` | 按顺序输出的事件记录。 |
| `next_after` | 下一批可使用的 `start_after` 值。 |
| `missing_data_log` | 缺失 manifest、cursor、asset 或无法回放时的证据。 |

CSV 记录列：

```text
replay_index, cursor_id, asset_id, event_id, event_time, event_type,
symbol, market, interval, source, quality_status, evidence_layer, payload_json
```

## 当前边界

- 当前只回放 `market_events` JSONL，不直接读取 bar cache。
- 当前不连接 Moomoo、Kafka、QuestDB、ClickHouse 或任何券商。
- 当前不生成交易信号、不提交订单、不做资金动作。
- 若找不到 cursor、asset 或事件，状态为 `Empty`，不会伪装成通过。

## 后续接口

后续三模式回测/模拟内核应把 `EventReplay_latest.json` 作为统一输入：

| 模式 | 使用方式 |
| --- | --- |
| Vectorized Research Mode | 将 replay records 转成 DataFrame，做快速参数扫描和样本内/样本外验证。 |
| Discrete Event Simulation Mode | 按 replay order 推进事件，模拟撮合、成本、滑点和风控状态机。 |
| Agent Market Simulation Mode | 把 replay records 作为市场观察输入，驱动 agent 决策和审计日志。 |

Vectorized Research Mode MVP 已落地在 `docs/VectorizedResearchMode.md`、`src/pfi_os/research/vectorized.py` 和 `scripts/vectorizedResearch.sh`。它只读取本地 replay 输出，不联网、不刷新行情、不连接券商、不创建订单。
