# Reproducible Data Lake

Reproducible Data Lake 是 PFI_OS 的可复现数据湖最小实现。它不复制数据、不联网、不接实时库，而是先把本地不可变数据资产登记成 manifest：路径、schema、partition、row count、checksum 和 replay cursor 都可复核。

它服务于后续三件事：

- 事件回放：从 `MarketEventLog_*.jsonl` 生成按 `event_time` 推进的 replay cursor。
- 可复现实验：每次回测/模拟能引用同一个 asset checksum，而不是只引用可变 latest 文件。
- 外部存储适配：后续 Arrow/Parquet、QuestDB、ClickHouse、Kafka sink 只需要保持 manifest 契约。

## What It Indexes

| 来源 | 当前行为 |
| --- | --- |
| `data/marketEvents/MarketEventLog_*.jsonl` | 作为不可变 market event asset 进入 manifest。 |
| `data/marketEvents/*latest*` | 只登记为 mutable alias，不计入不可变资产数量。 |
| `data/cache/<MARKET>/<interval>/<symbol>.csv/parquet` | 若存在且包含 OHLCV 必要列，则登记为 bar cache asset。 |

## Manifest Contract

主 manifest 使用 `PFIOSReproducibleDataLakeManifestV1`：

| 字段 | 含义 |
| --- | --- |
| `lake_status` | `Pass` / `Review` / `Empty`。 |
| `assets` | 不可变数据资产清单。 |
| `partitions` | 按 dataset、market、symbol、interval 聚合的分区摘要。 |
| `replay_cursors` | 每个可回放数据流的事件窗口和 `next_after`。 |
| `latest_aliases` | 可变 latest 文件，仅作定位，不作为可复现实验依据。 |
| `missing_data_log` | 未发现的可选数据族，例如尚无结构化 bar cache。 |

每个 asset 至少包含：

```text
asset_id, dataset, asset_type, format, relative_path, size_bytes,
checksum_sha256, schema, market, symbol, interval, source,
partition, row_count, first_event_time, last_event_time,
quality_status, replay_cursor_id
```

## Command

```bash
$PFI_OS_HOME/scripts/dataLakeManifest.sh --output-dir data/dataLake
```

只预览不写文件：

```bash
$PFI_OS_HOME/scripts/dataLakeManifest.sh --json-only
```

只索引事件层，跳过 bar cache：

```bash
$PFI_OS_HOME/scripts/dataLakeManifest.sh --no-cache --output-dir data/dataLake
```

## Outputs

```text
data/dataLake/DataLakeManifest_DDMMYYYY.json
data/dataLake/DataLakeManifest_DDMMYYYY_assets.csv
data/dataLake/DataLakeManifest_DDMMYYYY_replay_cursors.json
data/dataLake/DataLakeManifest_DDMMYYYY_replay_cursors.csv
data/dataLake/DataLakeManifest_DDMMYYYY.md
data/dataLake/DataLakeManifest_latest.json
data/dataLake/DataLakeManifest_latest_assets.csv
data/dataLake/DataLakeManifest_latest_replay_cursors.json
data/dataLake/DataLakeManifest_latest_replay_cursors.csv
data/dataLake/DataLakeManifest_latest.md
```

## Boundary

- 不连接 Moomoo OpenD、券商、Kafka、QuestDB、ClickHouse 或云对象存储。
- 不复制或移动原始资产，避免制造重复数据和路径混乱。
- 不把 latest 当成可复现实验依据；回测/模拟应引用 date-stamped asset 和 checksum。
- 当前 replay cursor 只覆盖 `BarClosed` 事件和结构化 bar cache；tick、order book、news、policy、portfolio event 后续分轮接入。
