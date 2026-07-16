# PFI v0.2.5 Stage 10 Phase 10.1 持久任务生命周期

## Run Contract

- Phase：`V025-S10-P10.1`
- Tasks：`S10-P1-T1..T4`
- Acceptance：`ACC-PFI-V025-STAGE10-WHOLE-REVIEW`；本轮只形成 Phase candidate，不执行整阶段验收。
- Risk：`T2_SCHEMA_CONCURRENCY_RECOVERY`
- 实现基线：`87743da7ce64fe173de1809f8c438369d222160e`
- 产品提交：`b97827f0b90f7e72de9fec64f88f702658a823bf`
- 明确不做：Phase 10.2 runtime diff/cache、Phase 10.3 observability/crash matrix、正式 UI、真实 PFI DB 迁移、外部网络、push、PFI.app install、production/final acceptance。

## Durable Schema 与事件事实

- `durable_jobs` 覆盖 `queued/running/retrying/succeeded/failed/cancelled/dead_letter`，直接列出 revision、attempt、available time、lease owner/hash/expiry、heartbeat、真实进度、结果复核态与终态时间。
- `durable_job_events` 每个 job revision 唯一，带前序 event hash；UPDATE/DELETE trigger 使事件只追加。job 删除受外键 `RESTRICT`。
- migration ID 为 `v025_stage10_durable_jobs_v1`。已有数据库在迁移前使用 SQLite Online Backup API 生成一致快照；本 Phase 只在隔离临时库验证。
- idempotency key 相同且 immutable input 相同返回既有任务；payload、attempt policy 或财务事实标记冲突时 fail closed。

## Worker Protocol 与恢复

- claim 使用 `BEGIN IMMEDIATE`，同时以 `job_id + revision + prior status` CAS；双 worker 并发只有一个获得租约。
- 原始 lease token 只在 claim 返回一次，SQLite 仅保存与 job ID 绑定的 SHA-256；heartbeat、progress、success/failure 均要求 owner、token、未过期 lease 与 expected revision。
- 可重试错误进入 `retrying`；达到 attempt 上限进入 `dead_letter`；不可重试错误进入 `failed`；cancel 会递增 revision、清除 lease，使旧 worker 后续写入失败。
- 过期 lease 保留已持久化 checkpoint，未耗尽时重新排队，耗尽时进入 dead letter。测试重开同一隔离库证明任务和事件不依赖进程内存。

## 真实进度与安全边界

- progress 只能由 `completed_units/total_units/step` 事件产生，必须单调；heartbeat 不改变进度，timer 不参与状态推导。
- `succeeded` 前必须存在完整进度且 `completed_units == total_units`。
- 含财务事实的 result 只记录 `private://`/`artifact://`/`report://` 引用，状态固定为 `pending_human_review`、`publishable=false`；没有后台发布或交易能力。
- public projection 不返回 payload 或 token；错误消息中的本机用户路径被脱敏。

## SQLite 与验证结论

- 当前 PFI Python 为 `3.12.13`，Python sqlite3 wrapper `2.6.0`，SQLite runtime `3.50.4`。
- Task Pack 规定并发 WAL 必须为 `3.51.3+` 或官方安全 backport `3.44.6/3.50.7`；当前 runtime 不满足，因此本实现明确使用 rollback journal `DELETE`、`synchronous=FULL`、`foreign_keys=ON`、`busy_timeout=30000` 与显式 commit/rollback。
- Phase target `7/7`、历史 Stage 10/SQLite 邻接回归 `19/19`、合并复验 `26/26`、release identity `10/10` 通过。
- 隔离 DB probe materialize 七种状态各一条、7 jobs/20 events；revision hash chain、重复 claim、stale worker、token 不落明文、integrity/foreign-key check 全部通过，临时库随后删除。
- 未改正式 UI，因此本 Phase 不伪造 browser/screenshot/trace 结果；正式 UI 与 DB 一致性留给后续 Phase 和 Stage 10 whole-stage acceptance。

## 当前状态与下一 Gate

- Phase 10.1=`candidate_pass`；Stage 10=`4/12 in_progress`；v0.2.5=`124/156 (79.49%)`。
- Phase 10.2、10.3、whole-stage independent review 与用户验收均 `not_started`。
- 下一唯一工作单元：`S10-P2-T1`，Acceptance 仍为 `ACC-PFI-V025-STAGE10-WHOLE-REVIEW`。
- 未使用 Finder、LaunchServices 或 GUI 文件操作；无外网、真实 DB、财务值、model/formula/parameter 值修改、push 或 install。
