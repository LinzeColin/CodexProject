# Market Event Layer

Market Event Layer 是 PFI_OS 事件驱动行情层的第一块本地底座。它把 OHLCV bar 转成稳定、可排序、可去重、可落盘的 `BarClosed` 事件，供后续数据湖、回放、三模式回测/模拟内核和实时研究工作流复用。

它不是实时行情连接器，不启动 Moomoo OpenD，不连接 Kafka、QuestDB、ClickHouse 或券商系统，也不会生成交易指令。

## Why It Exists

| 目标 | 作用 |
| --- | --- |
| Event-driven market layer | 用统一事件契约接住 Sample、CSV、Moomoo、Polygon、Yahoo 等来源。 |
| Reproducible data lake | 每次生成都有 schema、source、quality report、checksum 和 latest 指针。 |
| Replay and simulation | 回测/模拟内核可以按 `event_time` 重放 `BarClosed` 事件，而不是直接耦合 provider。 |
| Real-time adapters later | Kafka、QuestDB、ClickHouse 等后续只需要适配同一个事件契约。 |

## Event Contract

单条事件使用 `PFIOSMarketEventV1`：

| 字段 | 含义 |
| --- | --- |
| `event_id` | 基于 event type、source、market、symbol、interval、event_time 的稳定 ID。 |
| `event_time` | 市场事件时间，不是写入时间。 |
| `event_type` | 当前为 `BarClosed`。 |
| `symbol` / `market` / `interval` | 标的、市场和周期。 |
| `source` | 来源标签，例如 `sample` 或 `csv-import`。 |
| `quality_status` | 复用 `assess_bars` 的 `Pass` / `Review` / `Empty`。 |
| `evidence_layer` | 默认 `OBSERVATION`；真实源经过交叉验证后才能升级。 |
| `payload` | `open`、`high`、`low`、`close`、`volume`。 |

批量事件日志使用 `PFIOSMarketEventLogV1`，包含：

- `event_log_status`
- `source_summary`
- `quality_report`
- `events`
- `outputs`
- `assumptions`

## Command

默认使用 deterministic sample 数据，离线可复跑：

```bash
$PFI_OS_HOME/scripts/marketEventLayer.sh --symbol SPY --market US --interval 1d --start 2026-01-01 --end 2026-01-10 --output-dir data/marketEvents
```

从本地 CSV 转换：

```bash
$PFI_OS_HOME/scripts/marketEventLayer.sh --symbol SPY --market US --interval 1d --source csv-import --input-csv path/to/bars.csv --output-dir data/marketEvents
```

CSV 至少需要：

```text
datetime,open,high,low,close,volume
```

## Outputs

```text
data/marketEvents/MarketEventLog_SYMBOL_INTERVAL_DDMMYYYY.json
data/marketEvents/MarketEventLog_SYMBOL_INTERVAL_DDMMYYYY.jsonl
data/marketEvents/MarketEventLog_SYMBOL_INTERVAL_DDMMYYYY.csv
data/marketEvents/MarketEventLog_SYMBOL_INTERVAL_DDMMYYYY.md
data/marketEvents/MarketEventLog_latest.json
data/marketEvents/MarketEventLog_latest.jsonl
data/marketEvents/MarketEventLog_latest.csv
data/marketEvents/MarketEventLog_latest.md
```

## Current Boundary

- 当前只支持本地 sample 或 CSV 输入。
- 当前不做实时订阅、不写外部时序数据库、不推 Kafka。
- 当前事件只包括 `BarClosed`，不包括 order book、tick、news、policy、fundamental 或 portfolio events。
- 后续数据湖可以直接读取 JSONL/CSV/latest 指针；后续事件流适配器必须保持同一个 schema。
