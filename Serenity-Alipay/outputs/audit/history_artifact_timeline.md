# 历史报告与快照时间线

- 历史文件总数：216
- 分析报告文件：68
- MooMoo 快照/原始数据文件：11
- SQLite 快照表：23

## 口径

- `file_created_at` 来自文件系统创建时间；不支持创建时间的平台回退为 metadata change time。
- `file_modified_at` 是文件最后内容修改时间，可用于识别旧报告是否被后续编辑。
- `run_created_at` 和 `run_time_bj` 来自 SQLite `run_log`，用于区分“运行事实发生时间”和“文件被写入/编辑时间”。
- 该时间线是审计索引；不会改写任何旧报告、旧快照或历史 SQLite 行。

## 最近 20 个历史文件

- `data/notifications/mail_smoke_20260630T055915.html` | 创建 `2026-06-30T05:59:15+08:00` | 修改 `2026-06-30T05:59:15+08:00` | run `-`
- `data/notifications/mail_smoke_20260630T055915.md` | 创建 `2026-06-30T05:59:15+08:00` | 修改 `2026-06-30T05:59:15+08:00` | run `-`
- `data/notifications/mail_smoke_20260630T054401.html` | 创建 `2026-06-30T05:44:01+08:00` | 修改 `2026-06-30T05:44:01+08:00` | run `-`
- `data/notifications/mail_smoke_20260630T054401.md` | 创建 `2026-06-30T05:44:01+08:00` | 修改 `2026-06-30T05:44:01+08:00` | run `-`
- `data/notifications/mail_smoke_20260630T053033.html` | 创建 `2026-06-30T05:30:33+08:00` | 修改 `2026-06-30T05:30:33+08:00` | run `-`
- `data/notifications/mail_smoke_20260630T053033.md` | 创建 `2026-06-30T05:30:33+08:00` | 修改 `2026-06-30T05:30:33+08:00` | run `-`
- `data/notifications/mail_smoke_20260629T203241.html` | 创建 `2026-06-29T20:32:41+08:00` | 修改 `2026-06-29T20:32:41+08:00` | run `-`
- `data/notifications/mail_smoke_20260629T203241.md` | 创建 `2026-06-29T20:32:41+08:00` | 修改 `2026-06-29T20:32:41+08:00` | run `-`
- `data/notifications/mail_smoke_20260629T202123.html` | 创建 `2026-06-29T20:21:23+08:00` | 修改 `2026-06-29T20:21:23+08:00` | run `-`
- `data/notifications/mail_smoke_20260629T202123.md` | 创建 `2026-06-29T20:21:23+08:00` | 修改 `2026-06-29T20:21:23+08:00` | run `-`
- `data/notifications/mail_smoke_20260629T202011.html` | 创建 `2026-06-29T20:20:11+08:00` | 修改 `2026-06-29T20:20:11+08:00` | run `-`
- `data/notifications/mail_smoke_20260629T202011.md` | 创建 `2026-06-29T20:20:11+08:00` | 修改 `2026-06-29T20:20:11+08:00` | run `-`
- `data/notifications/mail_smoke_20260629T200635.html` | 创建 `2026-06-29T20:06:35+08:00` | 修改 `2026-06-29T20:06:35+08:00` | run `-`
- `data/notifications/mail_smoke_20260629T200635.md` | 创建 `2026-06-29T20:06:35+08:00` | 修改 `2026-06-29T20:06:35+08:00` | run `-`
- `data/notifications/mail_smoke_20260629T195712.html` | 创建 `2026-06-29T19:57:12+08:00` | 修改 `2026-06-29T19:57:12+08:00` | run `-`
- `data/notifications/mail_smoke_20260629T195712.md` | 创建 `2026-06-29T19:57:12+08:00` | 修改 `2026-06-29T19:57:12+08:00` | run `-`
- `data/notifications/mail_smoke_20260629T195702.html` | 创建 `2026-06-29T19:57:02+08:00` | 修改 `2026-06-29T19:57:02+08:00` | run `-`
- `data/notifications/mail_smoke_20260629T195702.md` | 创建 `2026-06-29T19:57:02+08:00` | 修改 `2026-06-29T19:57:02+08:00` | run `-`
- `data/moomoo/moomoo_collect_20260612T130021Z_3e03c0c0/US_AAPL_K_DAY_2026-06-01_2026-06-12.csv` | 创建 `2026-06-29T19:22:50+08:00` | 修改 `2026-06-29T19:22:50+08:00` | run `moomoo_collect_20260612T130021Z_3e03c0c0`
- `data/moomoo/moomoo_collect_20260612T130021Z_3e03c0c0/snapshot.json` | 创建 `2026-06-29T19:22:50+08:00` | 修改 `2026-06-29T19:22:50+08:00` | run `moomoo_collect_20260612T130021Z_3e03c0c0`

## SQLite 快照表

- `asset_master`：rows=48，runs=-，first_created=-，last_created=-
- `asset_pool_entry`：rows=38，runs=-，first_created=-，last_created=-
- `audit_log`：rows=79，runs=35，first_created=2026-06-12T12:11:24+00:00，last_created=2026-06-29T09:27:38+00:00
- `automation_tick_log`：rows=1019，runs=24，first_created=2026-06-12T12:29:19+00:00，last_created=2026-06-29T09:27:38+00:00
- `baseline_snapshot`：rows=123，runs=17，first_created=2026-06-12T22:34:10+00:00，last_created=2026-06-29T09:27:38+00:00
- `comparison_snapshot`：rows=640，runs=32，first_created=2026-06-12T12:29:02+00:00，last_created=2026-06-29T09:27:38+00:00
- `conflict_log`：rows=0，runs=-，first_created=-，last_created=-
- `decision_record`：rows=208，runs=34，first_created=2026-06-12T12:11:24+00:00，last_created=2026-06-29T09:27:38+00:00
- `fund_nav_snapshot`：rows=307，runs=34，first_created=2026-06-12T12:11:24+00:00，last_created=2026-06-29T09:27:38+00:00
- `fund_rule_snapshot`：rows=335，runs=34，first_created=2026-06-12T12:11:24+00:00，last_created=2026-06-29T09:27:38+00:00
- `manual_review_decision`：rows=0，runs=-，first_created=-，last_created=-
- `manual_review_queue`：rows=277，runs=34，first_created=2026-06-12T12:11:24+00:00，last_created=2026-06-29T09:27:38+00:00
- `market_kline_snapshot`：rows=67486，runs=39，first_created=2026-06-12T12:11:24+00:00，last_created=2026-06-29T09:27:38+00:00
- `missing_data_log`：rows=973，runs=34，first_created=2026-06-12T12:11:24+00:00，last_created=2026-06-29T09:27:38+00:00
- `notification_log`：rows=67，runs=35，first_created=2026-06-12T12:11:24+00:00，last_created=2026-06-29T09:27:38+00:00
- `platform_trade_check_snapshot`：rows=0，runs=-，first_created=-，last_created=-
- `position_snapshot`：rows=8，runs=2，first_created=2026-06-12T12:11:19+00:00，last_created=2026-06-12T12:28:52+00:00
- `rebalance_event_log`：rows=162，runs=28，first_created=2026-06-12T12:29:02+00:00，last_created=2026-06-29T09:27:38+00:00
- `recommendation_snapshot`：rows=208，runs=34，first_created=2026-06-12T12:11:24+00:00，last_created=2026-06-29T09:27:38+00:00
- `run_log`：rows=41，runs=41，first_created=2026-06-12T12:11:19+00:00，last_created=2026-06-29T09:27:38+00:00
- `score_snapshot`：rows=472，runs=34，first_created=2026-06-12T12:11:24+00:00，last_created=2026-06-29T09:27:38+00:00
- `source_evidence_audit_snapshot`：rows=316，runs=-，first_created=-，last_created=-
- `source_log`：rows=820，runs=41，first_created=2026-06-12T12:11:19+00:00，last_created=2026-06-29T09:27:38+00:00
