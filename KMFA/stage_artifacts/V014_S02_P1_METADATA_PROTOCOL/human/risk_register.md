# KMFA v0.1.4 S02-P1 Risk Register

| Risk | Status | Control |
|---|---|---|
| raw/private inbox 被误读或误列目录 | controlled | 本 phase validator 要求 `raw_inbox_read_by_this_phase=false` 和 `raw_inbox_listed_by_this_phase=false`；本轮不调用 raw readiness 工具。 |
| metadata 目录协议与 v1.4 raw boundary 脱节 | controlled | 新增 `raw_data_roots_v1_4.json` 并由 phase validator 校验。 |
| 公开仓库误提交业务明文或私有文件 | controlled | `.gitignore`、phase manifest、metadata protocol check、changed-file raw/secret scan 共同约束。 |
| 误把 S02-P1 当作 raw inventory 或正式数据导入 | controlled | completion record 和 manifest 明确 `raw_inventory_performed=false`、`business_records_committed=false`、`formal_report_performed=false`。 |
| 误触发 GitHub upload | controlled | manifest 和 validator 均要求 `github_upload_performed=false`；v1.4 upload 延期到 Stage 1-18 全部完成整体复审后一次性执行。 |
