# Memory-only Snapshot 与 Clean-Room 恢复

本流程恢复的是 Portable Agent Memory 的 canonical records、必要 contracts 和两个 generated
entrypoint，不是整仓备份。它不创建 archive branch、Git bundle、Issue、PR，也不修改当前
canonical 数据。

## 资产边界

- 文件名固定为 `portable-agent-memory-v1-<40-char-commit>.zip`。
- commit 文件直接读取对应 Git object，不读取工作树同名文件。
- snapshot 逐文件记录 SHA-256、字节数、来源和类别；ZIP 使用固定时间、固定权限和
  `ZIP_STORED`，相同输入生成相同字节。
- raw 只允许 canonical record 明确引用、位于 `data/public_raw/`、公开授权且为浅层文本的
  文件。opaque/private-origin export refs 不会被解析或复制；当前 canonical 集合的 eligible
  raw file count 为 `0`。
- ZIP 内附 policy、runbook 和 stdlib-only recovery tool。Task36 drill 可从当前受控工作树读取这
  三个 runtime 文件；Task37 公开发布必须加 `--release-candidate`，使所有成员直接读取 accepted
  commit，validator 会拒绝混入工作树 runtime 的 Release asset。
- SHA-256 只证明 integrity。无独立签名时不得声称 authenticity。

## 在仓库中导出

```bash
python3 scripts/memory_snapshot.py export \
  --database-dir . \
  --policy config/memory-snapshot-policy.json \
  --source-commit <exact-40-char-commit> \
  --output-dir <private-temp-dir>
```

导出只允许写入指定的仓库外目录。同名资产存在且 hash 相同时为 idempotent no-op；同名但
内容不同时 fail closed。

## 完全离线验证和查询

下载 public-safe Release asset 后可断网执行：

```bash
python3 memory_snapshot.py validate \
  --snapshot portable-agent-memory-v1-<commit>.zip \
  --expected-commit <exact-40-char-commit>

python3 memory_snapshot.py query \
  --snapshot portable-agent-memory-v1-<commit>.zip \
  --expected-commit <exact-40-char-commit> \
  --record-id <memory-id>
```

也可先用系统 `unzip` 取出 `tools/memory_snapshot.py`，再执行相同命令。query smoke 仅返回
record ID、状态、memory key 与 statement/source hashes，不回显 statement。

## Atomic clean-room restore

目标路径必须不存在；restore 先写 sibling 临时目录，逐文件复核后一次 rename 发布。任何
缺失、篡改、commit 不匹配、path traversal、symlink、credential shape 或非空目标都会失败并
清理临时目录。

```bash
python3 memory_snapshot.py restore \
  --snapshot portable-agent-memory-v1-<commit>.zip \
  --expected-commit <exact-40-char-commit> \
  --destination <new-clean-room-root>

python3 <new-clean-room-root>/tools/memory_snapshot.py query \
  --database-dir <new-clean-room-root>/OpenAIDatabase \
  --record-id <memory-id>
```

恢复完成后以 `SNAPSHOT_MANIFEST.json`、canonical manifest/dataset SHA-256 和逐文件 reconciliation
作为验收；不要用文件存在性替代 hash 校验。

## Release 与回滚

- Task36 只完成本地 deterministic drill，不发布资产。
- Task37 从最终 production commit 使用 `--release-candidate` 重新导出，并把 ZIP 作为 public-safe
  `LinzeColin/AgentDatabase` Release asset 发布；每条 record 均须公开授权、无 credential 且仅为
  redacted summary。CodexProject 只记录 asset name、size、SHA-256 和 disposition，不跟踪 ZIP。
- 发布失败时删除未完成 Release asset；不创建 archive branch，不改写 Git history。
- 本 Task 代码回滚为 revert 单一 Task36 commit，再复跑 export/validate/restore/query 与 0/0/0
  审计。
