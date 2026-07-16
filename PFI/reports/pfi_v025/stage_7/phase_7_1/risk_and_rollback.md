# Phase 7.1 风险与回滚

## 风险

- 真实上传请求包含私有字节，因此禁止保存 raw Playwright trace、HAR、response body 或数据库副本；只保存 sanitized trace metadata 和脱敏截图。
- confirm/review 若退化为前端 state、toast 或 localStorage，会产生假闭环；静态合同与浏览器/SQLite 双层验证阻止该退化。
- 非原子确认可能形成 ledger/review 半写；SQLite `BEGIN IMMEDIATE` 与强制失败 trigger 测试证明整批 rollback。
- 重复上传可能重复入账；batch fingerprint、唯一约束与 browser duplicate replay 共同验证 ledger count 不增长。
- 旧 MetaDatabase 写路径仍是历史兼容 helper，但正式 `/api/imports/alipay` endpoint 已切换为新 preview service；不得恢复正式端点对旧 writer 的调用。
- 早期测试路径曾短暂误触仓库内 MetaDatabase 工作副本；两份 tracked 文件已恢复、新增 raw 已删除，最终 `MetaDatabase` 与 `PFI/MetaDatabase` 均为零 diff。该已整改事件保留在证据中，不得改写成“全过程未发生”。

## 回滚

1. revert 本 Phase 单一提交，包括 additive migration、use case、runtime endpoint、正式 Shell 与 evidence。
2. 不删除或改写 canonical 财务源；本 Phase 没有 canonical migration。
3. 若 isolated runtime 已产生批次，调用 batch rollback 或删除整个 `/tmp` data home；不得清理用户 canonical data。
4. 保留 Stage 6 accepted baseline；不得以回滚为由进入 Phase 7.2/7.3、push 或重装 App。

## 当前边界

- Phase 7.1=`candidate_pass`；Stage 7=`in_progress`；Phase 7.2/7.3 与 whole-stage review=`not_started`。
- `finder_used=false`、`external_network_performed=false`、`push_performed=false`、`app_install_performed=false`。
- `real_financial_data_read=true` 仅表示读取 canonical 源并复制到 `/tmp`；`real_financial_data_mutated=false` 且前后 hash 相同。
