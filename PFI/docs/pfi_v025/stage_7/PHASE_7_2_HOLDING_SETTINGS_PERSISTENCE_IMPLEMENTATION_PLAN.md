# v0.2.5 Stage 7 Phase 7.2：持仓与设置正式持久化

## 执行合同

- 唯一范围：`S7-P2-T1..T4`。
- 唯一 Acceptance：`ACC-PFI-V025-S7-P72-HOLDINGS-SETTINGS`（项目治理分配；源 Roadmap/Task Pack 未提供 Phase 级 ACC-*）。
- 目标：持仓新增、编辑、软删除以单一 SQLite transaction 持久化，并让首页、投资和报告使用同一投影 hash；设置偏好只在设置页通过正式 API 持久化。
- 非范围：Phase 7.3 参数中心、Interconnection Map 与指标下钻，Stage 7 整阶段审查，GitHub push，PFI.app install，production/final acceptance。

## 实现

正式 Shell 的持仓草稿可暂存在浏览器，但“保存修改”只调用 `/api/holdings/commit`。后端在 `BEGIN IMMEDIATE` 中一次执行 create/update/delete change-set，以 request id、projection hash 和行 revision 防重复与并发覆盖；输入在进入数据库前完成类型、枚举、日期、数量和长度校验。SQLite additive migration 保存持仓记录、change-set、审计事件、设置偏好和设置事件；已有数据库首次迁移前使用 SQLite Online Backup 创建权限收紧的备份。

持仓投影只同步 `holding_count`、`valuation_status` 和 `projection_hash`。由于当前 Phase 没有真实持仓、价格和 FX source，所有金额字段保持 `null`，`financial_values_emitted=0`；浏览器验证使用明确标记的非财务 contract sentinel，只证明 CRUD/事务/重启机制，不计入真实财务验收。

设置页通过 `/api/settings/preferences` 读取、保存和恢复默认值，并使用 revision 防止覆盖；正式偏好不写 localStorage/sessionStorage/IndexedDB。反馈控制仍只在设置页显示。

## 验证结果

- 聚焦合同：`6 passed`；current-HEAD release/Stage 6/Phase 7.1/7.2 Python regression：`66 passed`；Node identity/cache：`28 passed`。
- 正式 Shell cached Playwright/local Chrome：首次保存/刷新 `13/13`，关闭浏览器 context、重启 Runtime API 并重新打开后 `12/12`。
- SQLite：重启前持仓 revision=2、设置 revision=1；重启后均保留；随后软删除持仓 revision=3、恢复默认设置 revision=2。
- 数据库最终 create/update/delete 各 1 次，change-set=3，settings event=2，migration=1；`foreign_key_check=pass`、`integrity_check=ok`。
- 首页、投资和报告只显示同一持仓数量、估值依赖缺失状态与同一 projection hash；没有生成假金额。
- console/page/HTTP/external-network errors=0；截图写入前脱敏并已纯工具目视检查；Finder 未使用。

## 风险、回滚与停止条件

风险集中在非原子 CRUD、刷新/重启丢失、revision 冲突、localStorage/toast 假保存、重复迁移备份和无来源时伪造金额。回滚方式是 revert 本 Phase 单一提交；schema 为 additive，不删除已有表；测试数据库位于 `/tmp`，可删除隔离 data home。任何正式保存只改变前端状态、数据库 integrity/FK 失败、金额从 sentinel 推导、设置控制泄漏到业务页、外网/Finder 使用或进入 Phase 7.3 都必须停止。

## 当前结论

`ACC-PFI-V025-S7-P72-HOLDINGS-SETTINGS` 为 `candidate_pass`。v0.2.5 进度 `92/156 = 58.97%`；Stage 7 为 `8/12 = 66.67% in_progress`，Phase 7.3 和 whole-stage review 均 `not_started`。
