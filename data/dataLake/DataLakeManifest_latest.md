# Reproducible Data Lake 2026-06-13

## Summary
- Status: `Pass`
- Assets: `1`
- Partitions: `1`
- Replay Cursors: `1`
- Latest Aliases: `4`

## Partitions
| partition | dataset | asset_count | row_count | first_event_time | last_event_time |
| --- | --- | --- | --- | --- | --- |
| dataset=market_events/market=US/symbol=SPY/interval=1d | market_events | 1 | 7 | 2026-01-01T00:00:00 | 2026-01-09T00:00:00 |

## Replay Cursors
| cursor_id | dataset | market | symbol | interval | source | asset_count | event_count | first_event_time | last_event_time | next_after |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 06306f6b26f7d3cbddd1ecc4 | market_events | US | SPY | 1d | sample | 1 | 7 | 2026-01-01T00:00:00 | 2026-01-09T00:00:00 | 2026-01-09T00:00:00 |

## Assets
| asset_id | dataset | asset_type | format | relative_path | size_bytes | checksum_sha256 | schema | market | symbol | interval | source | partition | row_count | first_event_time | last_event_time | quality_status | replay_cursor_id |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 7f9c515424d2a839ba055442 | market_events | event_jsonl | jsonl | data/marketEvents/MarketEventLog_SPY_1d_13062026.jsonl | 2969 | dbe3dac854ba1ab4161c87b432b989e5c4010725fb7f2b298104768edd93dfc9 | EVAOSMarketEventV1 | US | SPY | 1d | sample | dataset=market_events/market=US/symbol=SPY/interval=1d | 7 | 2026-01-01T00:00:00 | 2026-01-09T00:00:00 | Pass | 06306f6b26f7d3cbddd1ecc4 |

## Missing Data Log
| dataset | status | message |
| --- | --- | --- |
| bar_cache | Missing | No structured bar cache CSV/Parquet files found. |

## Assumptions
- The manifest indexes local immutable data assets and records mutable latest files only as aliases.
- Checksums are SHA-256 over file bytes; replay cursors are derived from event_time windows.
- This MVP does not copy assets, stream Kafka, write QuestDB/ClickHouse, or connect to live trading.
