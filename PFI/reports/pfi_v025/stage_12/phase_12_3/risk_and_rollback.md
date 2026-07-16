# Phase 12.3 整阶段审查整改风险与回滚

- 本次只完成初审三个 P1 的整改、精确候选绑定和最终证据索引重建；独立复审、`S12-P3-T4` 与最终明确验收均未开始。
- 上游已迁移顶层 `MetaDatabase`；不得恢复该目录。真实源只从当前分支可达的 immutable commit 读取，并逐 blob 校验 OID、字节数与 SHA-256。
- 已知 P2 为五项：真实内核 sleep/wake 未执行、Holdings source 未加载、CLI-only 方法约束、无 axe-core 的替代证据，以及六个历史状态测试债务；P0/P1 为零。
- 旧 Downloads App 已通过 CLI 原子移动到私有隔离区并保留精确回滚命令；canonical PFI.app 未修改。
- 回滚：先按公开 receipt 的命令恢复旧 App；必要时 revert remediation anchor 与后续证据/治理提交。未改 canonical DB、remote main 或 final human acceptance。
- 停止边界：不执行独立复审、最终验收、push、最终重装或 v0.2.6；Finder/LaunchServices/open/GUI 操作始终为零。
