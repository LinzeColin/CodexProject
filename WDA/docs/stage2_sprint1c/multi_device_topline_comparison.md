# WDA Stage 2 Sprint 1C Multi-device Topline Comparison

## Scope

本报告只使用用户提供的两个输出包：

- `新电脑.zip`: `/Users/linzezhang/Downloads/新电脑.zip`
- `旧电脑.zip`: `/Users/linzezhang/Downloads/旧电脑.zip`

未扫描任何 WeChat 源目录；未解密；未提取 key；未绕过 protected stores；未打开 DB schema；未解析消息内容；未运行第三方 WeChat export/decrypt 工具；未上传 raw data。

## Decision Summary

- 旧电脑 = 高价值数据源：`旧电脑.zip` 显示 128,088 classified paths、43.91 GB stat size，约为新电脑 path count 的 24.3 倍、stat size 的 12.0 倍。
- 新电脑 = WDA Control Plane / compute / RAG / Web / WDA_HOME host：新电脑存储和算力更适合承载后续索引、RAG、数据库和 Web，不应让旧电脑承担重分析。
- Raw Gate decision: **Conditional Investigation**。当前只证明路径/统计/候选类型差异，不证明消息可读，不声明 WDA Raw Gate 为 Go。
- Sprint 2 应优先做安全 readability classification：尽可能只转移旧电脑的 copied candidate DB bundle，而不是复制整份约 47GB 旧 WeChat cache。

## Topline Table

| Device package | Classified paths | Total stat size | Live DB candidate rows / size | Candidate DB inventory rows / size | BackupFiles | Account buckets |
|---|---:|---:|---:|---:|---:|---:|
| 新电脑 | 5,265 | 3.65 GB | 295 / 78.85 MB | 270 / 78.84 MB | 4 rows; 2 files | 24 |
| 旧电脑 | 128,088 | 43.91 GB | 362 / 1010.50 MB | 239 / 1004.42 MB | 4 rows; 0 files | 7 |

## Why the Old Computer Is Much Larger

旧电脑显著更大，主要不是因为 BackupFiles，而是因为历史消息文件和媒体/附件缓存更完整：

| Path family | 新电脑 rows / size | 旧电脑 rows / size |
|---|---:|---:|
| `msg/file` | 195 / 3.13 GB | 6,295 / 33.15 GB |
| `msg/attach` | 2,527 / 123.51 MB | 113,823 / 7.01 GB |
| `msg/video` | 23 / 625.04 KB | 2,427 / 1.96 GB |
| `db_storage/message` | 81 / 28.85 MB | 140 / 858.76 MB |

Key observations:

- `msg/file`: 旧电脑 6,295 rows / 33.15 GB，新电脑 195 rows / 3.13 GB，旧电脑约 10.6 倍 size。
- `msg/attach`: 旧电脑 113,823 rows / 7.01 GB，旧电脑约 58.2 倍 size。
- `msg/video`: 旧电脑 2,427 rows / 1.96 GB，旧电脑约 3283.3 倍 size。
- `db_storage/message`: 旧电脑 140 rows / 858.76 MB，新电脑 81 rows / 28.85 MB，旧电脑约 29.8 倍 size。
- BackupFiles 两边都是 4 rows；旧电脑 BackupFiles file rows 为 0，新电脑有 2 个 zero-byte `.wxbak` file rows。因此旧电脑更大的主要来源不是 BackupFiles。

## Acceptance Separation

- 旧电脑：推荐作为最高价值 WeChat 数据源，因为它包含更多历史路径、媒体/附件、视频和 message DB 候选体量。
- 新电脑：推荐作为 WDA Control Plane、WDA_HOME、数据库、Web、RAG 与重分析主机。
- 不声明消息已经可读。
- 不声明 Raw Gate 为 Go。
- 不建议复制整个 47GB 旧 WeChat cache；建议 Sprint 2 只处理 copied candidate DB bundle。
