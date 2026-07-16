# Stage 12 整阶段初审整改风险与回滚

- 三项 P1 已完成整改，但必须经后续独立复审才能转为 Stage 12 审查通过；本轮不执行最终验收。
- runtime payload 锚定于 `78375ec98fc1265abd03ef10087cc05beccab8b4`，remediation candidate 只增加身份载体、整改工具与证据；任何后续 runtime 漂移都必须重建 release identity。
- 旧 Downloads App 未删除，已用 CLI 原子移动至权限为 0700 的私有隔离目录；公开 receipt 保留 `$HOME` 形式的精确回滚命令。
- canonical PFI.app、canonical private DB、origin/main 与 final human acceptance 均未修改。
- 五项 P2 继续透明保留：kernel sleep/wake 代理限制、Holdings not_loaded、CLI-only 方法约束、axe-core 替代证据、六项历史状态测试债务。
- 停止边界：独立复审、`S12-P3-T4`、最终验收、push、最终 App 重装和 v0.2.6 均未开始；Finder/LaunchServices/open/AppleScript/GUI 操作均为零。
