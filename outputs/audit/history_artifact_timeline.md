# 历史报告与快照时间线

- 历史文件总数：142
- 分析报告文件：52
- MooMoo 快照/原始数据文件：11
- SQLite 快照表：21

## 口径

- `file_created_at` 来自文件系统创建时间；不支持创建时间的平台回退为 metadata change time。
- `file_modified_at` 是文件最后内容修改时间，可用于识别旧报告是否被后续编辑。
- `run_created_at` 和 `run_time_bj` 来自 SQLite `run_log`，用于区分“运行事实发生时间”和“文件被写入/编辑时间”。
- 该时间线是审计索引；不会改写任何旧报告、旧快照或历史 SQLite 行。

## 最近 20 个历史文件

- `data/notifications/sda_20260613T094539Z_r7_31fb1cc3_alert_local_notification.applescript` | 创建 `2026-06-13T17:45:39+08:00` | 修改 `2026-06-13T18:10:39+08:00` | run `sda_20260613T094539Z_r7_31fb1cc3`
- `data/notifications/sda_20260613T094539Z_r7_31fb1cc3_alert_mail.html` | 创建 `2026-06-13T18:10:39+08:00` | 修改 `2026-06-13T18:10:39+08:00` | run `sda_20260613T094539Z_r7_31fb1cc3`
- `data/notifications/sda_20260613T094539Z_r7_31fb1cc3_alert_mail.md` | 创建 `2026-06-13T17:45:39+08:00` | 修改 `2026-06-13T18:10:39+08:00` | run `sda_20260613T094539Z_r7_31fb1cc3`
- `data/notifications/sda_20260613T094539Z_r7_31fb1cc3_alert.md` | 创建 `2026-06-13T17:45:39+08:00` | 修改 `2026-06-13T17:45:39+08:00` | run `sda_20260613T094539Z_r7_31fb1cc3`
- `data/reports/sda_20260613T094539Z_r7_31fb1cc3_report.html` | 创建 `2026-06-13T17:45:39+08:00` | 修改 `2026-06-13T17:45:39+08:00` | run `sda_20260613T094539Z_r7_31fb1cc3`
- `data/reports/sda_20260613T094539Z_r7_31fb1cc3_report.md` | 创建 `2026-06-13T17:45:39+08:00` | 修改 `2026-06-13T17:45:39+08:00` | run `sda_20260613T094539Z_r7_31fb1cc3`
- `data/notifications/sda_20260613T093809Z_r7_e7c5fc7d_alert.md` | 创建 `2026-06-13T17:38:09+08:00` | 修改 `2026-06-13T17:38:09+08:00` | run `sda_20260613T093809Z_r7_e7c5fc7d`
- `data/notifications/sda_20260613T093809Z_r7_e7c5fc7d_alert_local_notification.applescript` | 创建 `2026-06-13T17:38:09+08:00` | 修改 `2026-06-13T17:38:09+08:00` | run `sda_20260613T093809Z_r7_e7c5fc7d`
- `data/notifications/sda_20260613T093809Z_r7_e7c5fc7d_alert_mail.md` | 创建 `2026-06-13T17:38:09+08:00` | 修改 `2026-06-13T17:38:09+08:00` | run `sda_20260613T093809Z_r7_e7c5fc7d`
- `data/reports/sda_20260613T093809Z_r7_e7c5fc7d_report.html` | 创建 `2026-06-13T17:38:09+08:00` | 修改 `2026-06-13T17:38:09+08:00` | run `sda_20260613T093809Z_r7_e7c5fc7d`
- `data/reports/sda_20260613T093809Z_r7_e7c5fc7d_report.md` | 创建 `2026-06-13T17:38:09+08:00` | 修改 `2026-06-13T17:38:09+08:00` | run `sda_20260613T093809Z_r7_e7c5fc7d`
- `data/reports/sda_20260612T121124Z_r7_5dacbac6_report.html` | 创建 `2026-06-12T20:11:24+08:00` | 修改 `2026-06-13T16:02:49+08:00` | run `sda_20260612T121124Z_r7_5dacbac6`
- `data/reports/sda_20260612T121124Z_r7_5dacbac6_report.md` | 创建 `2026-06-12T20:11:24+08:00` | 修改 `2026-06-13T16:02:49+08:00` | run `sda_20260612T121124Z_r7_5dacbac6`
- `data/reports/sda_20260612T121246Z_r7_5492880d_report.html` | 创建 `2026-06-12T20:12:47+08:00` | 修改 `2026-06-13T16:02:49+08:00` | run `sda_20260612T121246Z_r7_5492880d`
- `data/reports/sda_20260612T121246Z_r7_5492880d_report.md` | 创建 `2026-06-12T20:12:47+08:00` | 修改 `2026-06-13T16:02:49+08:00` | run `sda_20260612T121246Z_r7_5492880d`
- `data/reports/sda_20260612T122902Z_r11_ca0de309_report.html` | 创建 `2026-06-12T20:29:02+08:00` | 修改 `2026-06-13T16:02:49+08:00` | run `sda_20260612T122902Z_r11_ca0de309`
- `data/reports/sda_20260612T122902Z_r11_ca0de309_report.md` | 创建 `2026-06-12T20:29:02+08:00` | 修改 `2026-06-13T16:02:49+08:00` | run `sda_20260612T122902Z_r11_ca0de309`
- `data/reports/sda_20260612T122902Z_r6_4cdf476d_report.html` | 创建 `2026-06-12T20:29:02+08:00` | 修改 `2026-06-13T16:02:49+08:00` | run `sda_20260612T122902Z_r6_4cdf476d`
- `data/reports/sda_20260612T122902Z_r6_4cdf476d_report.md` | 创建 `2026-06-12T20:29:02+08:00` | 修改 `2026-06-13T16:02:49+08:00` | run `sda_20260612T122902Z_r6_4cdf476d`
- `data/reports/sda_20260612T122902Z_r7_e791c6e9_report.html` | 创建 `2026-06-12T20:29:02+08:00` | 修改 `2026-06-13T16:02:49+08:00` | run `sda_20260612T122902Z_r7_e791c6e9`

## SQLite 快照表

- `asset_master`：rows=23，runs=-，first_created=-，last_created=-
- `audit_log`：rows=39，runs=27，first_created=2026-06-12T12:11:24+00:00，last_created=2026-06-13T09:45:39+00:00
- `automation_tick_log`：rows=689，runs=16，first_created=2026-06-12T12:29:19+00:00，last_created=2026-06-13T09:45:39+00:00
- `baseline_snapshot`：rows=45，runs=9，first_created=2026-06-12T22:34:10+00:00，last_created=2026-06-13T09:45:39+00:00
- `comparison_snapshot`：rows=480，runs=24，first_created=2026-06-12T12:29:02+00:00，last_created=2026-06-13T09:45:39+00:00
- `conflict_log`：rows=0，runs=-，first_created=-，last_created=-
- `decision_record`：rows=130，runs=26，first_created=2026-06-12T12:11:24+00:00，last_created=2026-06-13T09:45:39+00:00
- `fund_nav_snapshot`：rows=199，runs=26，first_created=2026-06-12T12:11:24+00:00，last_created=2026-06-13T09:45:39+00:00
- `fund_rule_snapshot`：rows=208，runs=26，first_created=2026-06-12T12:11:24+00:00，last_created=2026-06-13T09:45:39+00:00
- `manual_review_decision`：rows=0，runs=-，first_created=-，last_created=-
- `manual_review_queue`：rows=69，runs=26，first_created=2026-06-12T12:11:24+00:00，last_created=2026-06-13T09:45:39+00:00
- `market_kline_snapshot`：rows=11982，runs=31，first_created=2026-06-12T12:11:24+00:00，last_created=2026-06-13T09:45:39+00:00
- `missing_data_log`：rows=94，runs=26，first_created=2026-06-12T12:11:24+00:00，last_created=2026-06-13T09:45:39+00:00
- `notification_log`：rows=51，runs=27，first_created=2026-06-12T12:11:24+00:00，last_created=2026-06-13T09:45:39+00:00
- `position_snapshot`：rows=8，runs=2，first_created=2026-06-12T12:11:19+00:00，last_created=2026-06-12T12:28:52+00:00
- `rebalance_event_log`：rows=106，runs=20，first_created=2026-06-12T12:29:02+00:00，last_created=2026-06-13T09:45:39+00:00
- `recommendation_snapshot`：rows=130，runs=26，first_created=2026-06-12T12:11:24+00:00，last_created=2026-06-13T09:45:39+00:00
- `run_log`：rows=33，runs=33，first_created=2026-06-12T12:11:19+00:00，last_created=2026-06-13T09:45:39+00:00
- `score_snapshot`：rows=208，runs=26，first_created=2026-06-12T12:11:24+00:00，last_created=2026-06-13T09:45:39+00:00
- `source_evidence_audit_snapshot`：rows=316，runs=-，first_created=-，last_created=-
- `source_log`：rows=429，runs=33，first_created=2026-06-12T12:11:19+00:00，last_created=2026-06-13T09:45:39+00:00
