# PFI v0.2.5 Stage 12 整阶段初审整改

## 唯一目标

关闭初审发现的三个 P1：release source commit 漂移、候选/验收请求未精确绑定、Downloads 旧非 canonical App。整改完成后停在独立复审前，不执行 `S12-P3-T4`、最终验收、GitHub push 或 canonical PFI.app 最终重装。

## 身份模型

- Runtime source commit：`78375ec98fc1265abd03ef10087cc05beccab8b4`，即最后一次修改 v0.2.5 runtime payload 的提交。
- Remediation candidate commit：包含修正后的 manifest/embedded manifest、精确绑定生成器、CLI 隔离工具、测试与隔离 receipt 的不可变提交。
- 后续 closure commit 只允许增加证据与治理 overlay；如 runtime payload 再变化，必须重新建立 release identity 与 candidate。

## CLI-only 入口整改

旧 `Downloads/PFI.app` 仅在核对版本 `0.2.3`、build `20260629.1` 和 bundle hash 后，使用原子移动进入私有隔离目录。操作不删除 App、不修改 canonical PFI.app，并在公开 receipt 中保留使用 `$HOME` 的精确回滚命令。

## 验收边界

- 三个初审 P1 均有独立机器证据，整改后 P0/P1 为零。
- Phase 12.3 index、request、state、evidence 必须绑定同一 40 位 candidate commit，禁止 `SELF`。
- release manifest 与 web embedded manifest 必须完全一致；runtime payload 在 source commit 后不得漂移。
- `/Applications/PFI.app`、Desktop canonical symlink 与 Downloads CLI census 必须一致，非 canonical entry mismatch 为零。
- Fresh real E2E、focused Stage 12、selected adjacent regression、Node cache、dual-plane、renderer、complete overlay governance 全部通过。
- 独立复审状态保持 `not_started`；最终人类验收文件必须不存在。

## 回滚

先按 `entry_quarantine.json` 中的命令恢复旧 App；必要时再 revert evidence/governance closure commit 与 remediation candidate commit。整个整改不修改 canonical private DB、origin/main 或 final acceptance。
