# PFI v0.2.5 Stage 11 Phase 11.1 — SQLite 安全与并发

## 1. 本轮合同

- Phase：`V025-S11-P11.1`
- Tasks：`S11-P1-T1..T4`
- 唯一后续 Acceptance：`ACC-PFI-V025-STAGE11-WHOLE-REVIEW`
- 风险路由：`T2_SQLITE_RUNTIME_CONCURRENCY_MIGRATION`
- 主产品提交：`b07709d0453d3d2c6d36a10375d823dbb0870c53`
- release identity 收口提交：`ad16901505f7e6f23653aa8b1e03945211dc4e93`
- 数据边界：仅 disposable SQLite；canonical private PFI DB 未读取、未迁移、未修改。

本轮只完成 SQLite runtime gate、连接配置、migration lifecycle 和并发/强杀回滚验证。Phase 11.2 的 online backup、隔离 restore 与原子替换，以及 Phase 11.3 的公共/私有分发边界均未开始。

## 2. Runtime gate

项目 Python 3.12.13 当前绑定 SQLite `3.50.4`，source id 为 `2025-07-30 19:33:53 4d8adfb30e03f9cf27f800a2c1ba3c48fb4ca1b08b0f5ed59a4d5ecbf45e20a3`。SQLite 官方说明 WAL-reset 风险影响 `3.7.0` 至 `3.51.2`，修复进入 `3.51.3`，并回移到 `3.50.7` 与 `3.44.6`：

- <https://sqlite.org/wal.html>
- <https://sqlite.org/releaselog/3_51_3.html>

因此 `3.50.4` 不允许并发 WAL。`evaluate_sqlite_runtime()` 对官方修复版本矩阵作确定性判断；任何显式 WAL 请求在不安全 runtime 上抛出 `UnsafeSQLiteRuntimeError`。默认策略始终是可审计的 `DELETE` rollback journal，不会因为版本字符串或旧数据库状态静默进入 WAL。

## 3. 连接与事务合同

活跃 operational store 统一通过 `operational_transaction()`：

- `PRAGMA journal_mode=DELETE`
- `PRAGMA synchronous=FULL`
- `PRAGMA foreign_keys=ON`
- `PRAGMA busy_timeout=30000`
- 写竞争使用 `BEGIN IMMEDIATE`
- 任意 `BaseException` 显式 rollback；commit 失败再次 rollback
- 配置后回读 PRAGMA，任何 drift fail closed

Stage 10 durable-job store 已独立使用相同 `DELETE/FULL/FK/timeout/transaction` 边界，因此未进行无价值重构。

## 4. Migration lifecycle

新增 `pfi_operational_migrations` registry，记录 versioned `migration_id`、source SHA-256、UTC applied time 与 SQLite version。migration source checksum 与 pinned checksum 不一致时拒绝执行；重复相同 migration 为幂等 verified replay；失败 SQL 在同一 `BEGIN IMMEDIATE` 内回滚 schema、data 与 registry entry。

Migration SQL 不得自带 `BEGIN/COMMIT/ROLLBACK/SAVEPOINT/RELEASE`，不得用 `PRAGMA` 改写连接策略，也不得 `ATTACH/DETACH/VACUUM` 逃出受控数据库边界。注释伪装的控制语句同样拒绝。

## 5. 验证结果与边界

- Stage 11 新增测试覆盖 runtime matrix、WAL fail-closed、PRAGMA audit、异常 rollback、四进程并发、实际 SIGKILL、checksum drift、迁移失败回滚与 SQL transaction escape；加上 Stage 7/10 相邻回归和 release identity 共 `68/68`。
- Stage 7 import/holding 与 Stage 10 job lifecycle 相邻回归同时执行。
- disposable DB 重开后要求：并发写入数精确、未提交强杀行数为 0、`integrity_check=ok`、`foreign_key_check=[]`。
- 研究层仅访问 `sqlite.org` 官方文档核对当前安全公告；产品与测试 runtime 外部网络调用为 0。不使用 Finder、LaunchServices 或 GUI 文件操作；不 push、不安装 PFI.app，不修改 model/formula/parameter 数值。

## 6. Scope override 与 rollback

TaskPack 实现 allowlist 列出 `infrastructure/operational_store*`，但真实基础入口位于 `PFI/src/pfi_os/application/operational_store.py`。若只增加 infrastructure helper 而不接入该入口，运行时 gate 不会覆盖实际产品路径。因此本轮在用户 standing authorization 下仅对该一个活跃文件作必要 scope override；证据中的 `allowed_files_obeyed` 如实为 `false`，并单列 override 原因。

Rollback 顺序：先 revert Phase 11.1 证据/治理提交，再依次 revert `ad16901505f7e6f23653aa8b1e03945211dc4e93` 与 `b07709d0453d3d2c6d36a10375d823dbb0870c53`。本轮未触碰 canonical private DB、生产安装或远端；无需数据库数据回滚。Phase 11.2 在任何 canonical migration 前仍必须补齐一致备份与 restore rehearsal。
