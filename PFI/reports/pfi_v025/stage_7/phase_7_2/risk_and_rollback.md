# Phase 7.2 风险与回滚

## 风险

- 持仓保存若逐行提交，部分失败会形成半写；正式 API 必须使用一个 `BEGIN IMMEDIATE` change-set。
- 前端 toast、内存或 localStorage 可能制造假保存；正式保存结果必须来自 API、SQLite、刷新、浏览器重开和服务重启证据。
- revision/projection hash 缺失会让旧页面覆盖新状态；冲突必须 fail closed 并要求刷新。
- 当前没有可验收的真实持仓、价格和 FX source；contract sentinel 只能验证机制，任何由它生成的金额都属于假财务结果。
- 已有数据库升级若无一致备份或迁移并发执行，可能破坏本地状态；首次 additive migration 前必须 SQLite Online Backup，初始化由进程锁串行化。
- 设置偏好若写浏览器存储或在业务页显示反馈控制，会违反正式持久化与页面隔离合同。

## 回滚

1. revert 本 Phase 单一提交，包括 additive migration、use case、runtime endpoint、正式 Shell、测试与 evidence。
2. 不删除已有 SQLite 表或 canonical 财务源；本 Phase migration 只增加新表和索引。
3. 验证数据库只位于 `/tmp/pfi-stage7-phase72-*`，失败时删除整个隔离 data home；不得清理用户 canonical data。
4. 保留 Phase 7.1 candidate baseline；不得以回滚为由进入 Phase 7.3、整阶段审查、push 或重装 App。

## 当前边界

- Phase 7.2=`candidate_pass`；Stage 7=`8/12 in_progress`；Phase 7.3 与 whole-stage review=`not_started`。
- `finder_used=false`、`external_network_performed=false`、`push_performed=false`、`app_install_performed=false`。
- `real_financial_data_read=false`、`financial_sentinel_counts_as_real_acceptance=false`、`financial_values_emitted=0`。
