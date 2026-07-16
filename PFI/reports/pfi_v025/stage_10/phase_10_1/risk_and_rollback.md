# Phase 10.1 Risk and Rollback

- 本 Phase 只建立 durable-job lifecycle；未实现 Phase 10.2 dependency diff/cache，也未实现 Phase 10.3 trace/log/kill-offline matrix，不能据此通过 Stage 10。
- SQLite runtime 为 `3.50.4`，低于 Task Pack 指定的 WAL 安全 backport `3.50.7`；因此强制 `journal_mode=DELETE`，没有启用并发 WAL。Stage 11 必须独立完成 runtime gate。
- 所有 worker 写操作必须携带 `expected_revision`、worker identity 与 lease token；token 只返回一次，数据库仅保存 job-bound SHA-256。过期、错误 token 或旧 revision 均 fail closed。
- 进度只接受持久化 `completed_units/total_units/step` 事件；heartbeat 不计进度，重复无变化事件和倒退事件均拒绝。
- 带财务事实的任务即使 `succeeded`，结果仍为 `pending_human_review` 且 `publishable=false`；本 Phase 没有发布方法、网络调用或交易路径。
- Phase 验证只创建并删除隔离临时 SQLite；未打开、迁移或修改 canonical PFI 私有数据库，也未读取财务值。
- 本轮未集成正式 UI，因此没有浏览器验收；Stage 10 最终 UI/DB 一致性仍是后续 Phase 和整阶段门禁。

Rollback：先 revert Phase 10.1 证据/治理提交，再 revert 产品提交 `b97827f0b90f7e72de9fec64f88f702658a823bf`。由于真实 PFI 数据库未迁移，无需执行生产 DB 逆向迁移；若未来已应用迁移，只能按 Stage 11 的备份/补偿流程恢复，不能直接删除已发布事实。
