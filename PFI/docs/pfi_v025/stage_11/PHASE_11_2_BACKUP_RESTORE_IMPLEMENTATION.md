# PFI v0.2.5 Stage 11 Phase 11.2 备份、恢复与完整性

## Run contract

- Phase / tasks：`V025-S11-P11.2` / `S11-P2-T1..T4`
- Acceptance：`ACC-PFI-V025-STAGE11-WHOLE-REVIEW`
- 风险路由：`T2_SQLITE_BACKUP_RESTORE_ATOMIC_REPLACEMENT`
- implementation base：`aa6bacba3342fe0a775fad2225317dd20842f6bf`
- product commit：`bbfdfa419e1fb8ffc3e3ba22d63cffbc3d5f267b`
- 状态边界：本文件只记录 Phase 11.2 candidate；Phase 11.3 与 Stage 11 整阶段审查未开始。

## 实现

`operational_store_backup.py` 提供三个 fail-closed primitive：

1. `create_online_backup()` 使用 Python `sqlite3.Connection.backup()` 对在线数据库取得一致快照；不使用在线 `cp`，不覆盖已有 backup，输出文件固定 `0600` 并 fsync 文件和目录。
2. `verify_sqlite_snapshot()` 以只读连接运行 `integrity_check`、`foreign_key_check`、required table、migration registry/checksum 与只读 application invariant；receipt 只包含 hash、计数、schema hash、状态和 invariant ID。
3. `restore_verified_backup()` 先验证 backup，再复制到隔离 candidate 并再次验证；只有 candidate 合格、target exact SHA-256 未漂移、target 无 SQLite sidecar、staging/rollback 与 target 位于同一文件系统时，才在独占 maintenance lock 下创建并验证 rollback snapshot，然后执行 `os.replace()`、fsync 与 installed verification。

所有 base/import/holding/job operational transaction 共享同一 advisory maintenance lock。恢复后的验证如果失败，原数据库会在同一独占 lock 尚未释放时自动替换回来，并验证 rollback hash、integrity、foreign key、migration 与 application invariants；rollback 无法验证时独立抛出 `RestoreRollbackError`，不会伪报成功。

CLI 为 `scripts/v025/pfi_operational_backup_restore.py`：

```bash
python PFI/scripts/v025/pfi_operational_backup_restore.py inspect \
  --database "$PFI_DATA_HOME/private/operational/pfi.sqlite"

python PFI/scripts/v025/pfi_operational_backup_restore.py backup \
  --database "$PFI_DATA_HOME/private/operational/pfi.sqlite" \
  --output "$PFI_DATA_HOME/private/backups/pfi-pre-restore.sqlite"

python PFI/scripts/v025/pfi_operational_backup_restore.py restore \
  --backup "$PFI_DATA_HOME/private/backups/pfi-pre-restore.sqlite" \
  --target "$PFI_DATA_HOME/private/operational/pfi.sqlite" \
  --staging-directory "$PFI_DATA_HOME/private/restore-staging" \
  --rollback-directory "$PFI_DATA_HOME/private/rollback" \
  --expected-target-sha256 '<inspect 返回的 exact SHA-256>'
```

本 Phase 没有执行上述 canonical 路径命令；验证只使用测试临时目录内的非财务 disposable SQLite。

## 验证与证据

- focused + adjacent regression：Phase 11.2、Phase 11.1、Stage 7 import/holding、Stage 10 jobs 与 release identity 合计 `82/82`。
- online rehearsal：并发 transaction 的 parent/child pairing 始终为 0 差异，backup method=`sqlite_online_backup_api`，结构、FK、migration 与 application invariant 通过。
- restore rehearsal：candidate 在 target 被触碰前验证；target exact hash、same-filesystem atomic replace、verified rollback snapshot 与 installed hash 全部通过。
- rollback rehearsal：`after_atomic_replace` 注入故障后状态=`rolled_back`，automatic rollback 通过；恢复结果匹配预先验证的 rollback snapshot SHA，原 application invariants 恢复。SQLite online backup 是逻辑一致副本，不声称与操作前 target 具有相同物理文件 SHA。
- TaskPack evidence schema、完整 archive + exact overlay governance、两个 Python parser renderer、privacy scan 与 artifact hashes 全部作为 Phase evidence 生成器的停止条件。

## Scope override 与边界

TaskPack 的 literal allowlist 未覆盖同一数据库的 durable job writer 与 release identity closure。standing authorization 下仅增加以下必要范围，并在 evidence 中保留 `allowed_files_obeyed=false`：

- `PFI/src/pfi_os/infrastructure/jobs/sqlite_store.py`：job transaction 必须参与同一 maintenance lock，否则 atomic restore 期间仍可能写入。
- `PFI/src/pfi_v02/stage_v021_runtime_api.py`、`PFI/config/release_manifest.json`、`PFI/web/index.html`、`PFI/tests/test_v025_stage1_release_identity.py`：把新增 backup/restore module 与 CLI 纳入 backend identity closure；未改变 version/build/release commit。

本实现只协调遵守 PFI maintenance lock 的进程。未知或不合作的外部 SQLite client 必须先 quiesce；存在 `-journal`、`-wal` 或 `-shm` sidecar 时恢复 fail closed。现有目录若向 group/other 开放，不会被静默 chmod，而是拒绝操作。

本 Phase 未使用 Finder、LaunchServices 或 GUI；未读取、迁移或修改 canonical private PFI DB；未输出财务值；未修改 model/formula/parameter 数值；未 push、安装或声明 production/final acceptance。研究层仅核对 SQLite Online Backup、atomic commit 与 Python `Connection.backup()` 官方文档，产品/测试 runtime 外部网络调用为 0。

## Rollback

先 revert Phase 11.2 证据/治理提交，再 revert product commit `bbfdfa419e1fb8ffc3e3ba22d63cffbc3d5f267b`。由于本 Phase 没有 canonical DB、安装面或远端副作用，不需要数据、App 或 GitHub 回滚。
